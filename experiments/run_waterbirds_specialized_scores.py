"""exp021: Generate Waterbirds specialized baseline scores from exp018 checkpoints.

This script produces `specialized_scores.csv` for the exp021 comparison step.
It reuses the exp018 saved checkpoints, and computes two specialized metrics
on Waterbirds:

  bg_score = fraction of test examples whose true-class probability increases
             after class-consistent background replacement by > epsilon
  fg_score = fraction of test examples whose true-class probability increases
             after class-consistent foreground replacement by > epsilon
  pca_score = hidden-layer PCA spuriousness proxy based on the penultimate
              feature space of the checkpointed oracle

The output CSV is intentionally minimal and matches the contract expected by
`run_waterbirds_specialized_baseline.py`:

  seed,bg_score,fg_score[,pca_score,pca_bg_score,pca_fg_score]

We also save a partial CSV, summary text, and metadata for reproducibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_waterbirds import build_oracle, load_oracle_checkpoint  # noqa: E402
from src.waterbirds_dataset import EVAL_TRANSFORM  # noqa: E402


def _config_hash(cfg: dict) -> str:
    payload = json.dumps(cfg, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _git_commit_short() -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _load_metadata(root: str) -> pd.DataFrame:
    meta = pd.read_csv(Path(root) / "metadata.csv")
    meta["split"] = meta["split"].astype(int)
    meta["y"] = meta["y"].astype(int)
    meta["place"] = meta["place"].astype(int)
    return meta


def _load_img(root: str, rel_path: str) -> np.ndarray:
    from PIL import Image

    img = Image.open(Path(root) / rel_path).convert("RGB")
    return np.array(img)


def _grabcut_mask(img_np: np.ndarray) -> np.ndarray:
    """Foreground mask (1=foreground) using the same GrabCut recipe as exp018."""
    h, w = img_np.shape[:2]
    bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    mask = np.zeros((h, w), np.uint8)
    rect = (w // 8, h // 8, w * 3 // 4, h * 3 // 4)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    return fg


def _resize_to(img_np: np.ndarray, shape_hw: tuple[int, int]) -> np.ndarray:
    h, w = shape_hw
    return cv2.resize(img_np, (w, h), interpolation=cv2.INTER_AREA)


def _apply_background_replacement(img_np: np.ndarray, fg_mask: np.ndarray, donor_np: np.ndarray) -> np.ndarray:
    donor_np = _resize_to(donor_np, img_np.shape[:2])
    out = img_np.copy()
    out[fg_mask == 0] = donor_np[fg_mask == 0]
    return out


def _apply_foreground_replacement(img_np: np.ndarray, fg_mask: np.ndarray, donor_np: np.ndarray) -> np.ndarray:
    donor_np = _resize_to(donor_np, img_np.shape[:2])
    out = img_np.copy()
    out[fg_mask == 1] = donor_np[fg_mask == 1]
    return out


def _to_tensor(img_np: np.ndarray) -> torch.Tensor:
    from PIL import Image

    return EVAL_TRANSFORM(Image.fromarray(img_np))


def _predict_true_class_prob(model: torch.nn.Module, batch: torch.Tensor, labels: torch.Tensor) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(batch)
        probs = torch.softmax(logits, dim=1)
        return probs.gather(1, labels.view(-1, 1)).squeeze(1).cpu().numpy()


def _extract_penultimate_features(model: torch.nn.Module, batch: torch.Tensor) -> np.ndarray:
    """Return the activations immediately before the final linear layer."""
    captured: dict[str, torch.Tensor] = {}

    def _hook(_module, inputs, _output):
        captured["features"] = inputs[0].detach()

    handle = model.fc.register_forward_hook(_hook)
    try:
        model.eval()
        with torch.no_grad():
            _ = model(batch)
        if "features" not in captured:
            raise RuntimeError("failed to capture penultimate features")
        return captured["features"].cpu().numpy()
    finally:
        handle.remove()


def _auc_from_scores(labels: np.ndarray, scores: np.ndarray) -> float:
    """Compute AUC via rank statistics; returns 0.5 when labels are degenerate."""
    labels = np.asarray(labels).astype(int)
    scores = np.asarray(scores).astype(float)
    pos = labels == 1
    neg = labels == 0
    n_pos = int(pos.sum())
    n_neg = int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = pd.Series(scores).rank(method="average").to_numpy()
    sum_pos = float(ranks[pos].sum())
    auc = (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def _best_oriented_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    auc = _auc_from_scores(labels, scores)
    return float(max(auc, 1.0 - auc))


def _compute_pca_spuriousness(
    model: torch.nn.Module,
    orig_batch: torch.Tensor,
    place_labels: np.ndarray,
    class_labels: np.ndarray,
    batch_size: int,
) -> dict:
    """Compute a lightweight PCA proxy for hidden-layer spuriousness.

    We fit PCA on the penultimate features of the evaluation batch, then score
    how well the leading principal directions separate background-place labels
    versus class labels. The returned score is positive when the hidden space is
    more aligned with background than with class identity.
    """
    feat_chunks: list[np.ndarray] = []
    for start in range(0, len(orig_batch), batch_size):
        sl = slice(start, min(start + batch_size, len(orig_batch)))
        feat_chunks.append(_extract_penultimate_features(model, orig_batch[sl]))
    feats = np.concatenate(feat_chunks, axis=0)
    feats = feats - feats.mean(axis=0, keepdims=True)
    if feats.shape[0] < 2:
        return {
            "pca_bg_score": 0.5,
            "pca_fg_score": 0.5,
            "pca_score": 0.0,
            "pca_ok": False,
        }

    _, _, vt = np.linalg.svd(feats, full_matrices=False)
    n_pcs = min(5, vt.shape[0])
    proj = feats @ vt[:n_pcs].T

    bg_scores = [_best_oriented_auc(place_labels, proj[:, j]) for j in range(n_pcs)]
    fg_scores = [_best_oriented_auc(class_labels, proj[:, j]) for j in range(n_pcs)]
    pca_bg_score = float(max(bg_scores))
    pca_fg_score = float(max(fg_scores))
    pca_score = pca_bg_score - pca_fg_score
    return {
        "pca_bg_score": pca_bg_score,
        "pca_fg_score": pca_fg_score,
        "pca_score": pca_score,
        "pca_ok": bool(pca_score > 0),
    }


def _build_class_donor_pool(root: str, meta: pd.DataFrame, y: int, n_samples: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    rows = meta[(meta["split"] == 0) & (meta["y"] == y)].to_dict("records")
    if not rows:
        raise ValueError(f"no training rows available for class y={y}")
    rng.shuffle(rows)
    pool: list[np.ndarray] = []
    for row in rows:
        if len(pool) >= n_samples:
            break
        pool.append(_load_img(root, row["img_filename"]))
    return pool


def _select_eval_rows(meta: pd.DataFrame, n_eval: int, seed: int) -> pd.DataFrame:
    rows = meta[meta["split"] == 2].reset_index(drop=True).copy()
    rng = np.random.default_rng(seed)
    order = np.arange(len(rows))
    rng.shuffle(order)
    rows = rows.iloc[order[: min(n_eval, len(rows))]].reset_index(drop=True)
    return rows


def _score_seed(seed: int, cfg: dict, oracle_cfg: dict, outdir: Path) -> dict:
    torch.set_num_threads(int(cfg.get("threads_per_worker", 4)))

    root = cfg["data"]["root"]
    epsilon = float(cfg["specialized"]["epsilon"])
    n_eval = int(cfg["specialized"]["n_eval"])
    bg_pool_n = int(cfg["specialized"]["bg_pool_n"])
    fg_pool_n = int(cfg["specialized"]["fg_pool_n"])
    ckpt_path = Path(cfg["input"]["checkpoint_dir"]) / f"seed_{seed}.pt"
    if not ckpt_path.exists():
        raise FileNotFoundError(f"checkpoint not found: {ckpt_path}")

    meta = _load_metadata(root)
    eval_rows = _select_eval_rows(meta, n_eval=n_eval, seed=seed)
    model = build_oracle(seed)
    val_acc = load_oracle_checkpoint(model, ckpt_path, oracle_cfg)

    # Build class-conditioned donor pools so background and foreground swaps are
    # both class-consistent, which mirrors the exp018 Waterbirds setup.
    bg_pool_by_y = {
        0: _build_class_donor_pool(root, meta, y=0, n_samples=bg_pool_n, seed=seed),
        1: _build_class_donor_pool(root, meta, y=1, n_samples=bg_pool_n, seed=seed),
    }
    fg_pool_by_y = {
        0: _build_class_donor_pool(root, meta, y=0, n_samples=fg_pool_n, seed=seed + 13),
        1: _build_class_donor_pool(root, meta, y=1, n_samples=fg_pool_n, seed=seed + 13),
    }

    rng = np.random.default_rng(seed + 999)
    orig_batch: list[torch.Tensor] = []
    bg_batch: list[torch.Tensor] = []
    fg_batch: list[torch.Tensor] = []
    labels: list[int] = []

    mask_cache: dict[int, np.ndarray] = {}
    donor_pick = {"bg": {0: 0, 1: 0}, "fg": {0: 0, 1: 0}}

    for idx, row in enumerate(eval_rows.to_dict("records")):
        y = int(row["y"])
        img_np = _load_img(root, row["img_filename"])
        if idx not in mask_cache:
            mask_cache[idx] = _grabcut_mask(img_np)
        fg_mask = mask_cache[idx]

        bg_pool = bg_pool_by_y[y]
        fg_pool = fg_pool_by_y[y]
        bg_donor = bg_pool[int(rng.integers(0, len(bg_pool)))]
        fg_donor = fg_pool[int(rng.integers(0, len(fg_pool)))]
        donor_pick["bg"][y] += 1
        donor_pick["fg"][y] += 1

        bg_img = _apply_background_replacement(img_np, fg_mask, bg_donor)
        fg_img = _apply_foreground_replacement(img_np, fg_mask, fg_donor)

        orig_batch.append(_to_tensor(img_np))
        bg_batch.append(_to_tensor(bg_img))
        fg_batch.append(_to_tensor(fg_img))
        labels.append(y)

    orig = torch.stack(orig_batch, dim=0)
    bg = torch.stack(bg_batch, dim=0)
    fg = torch.stack(fg_batch, dim=0)
    y = torch.tensor(labels, dtype=torch.long)

    batch_size = int(cfg["specialized"].get("batch_size", 32))
    orig_probs: list[np.ndarray] = []
    bg_probs: list[np.ndarray] = []
    fg_probs: list[np.ndarray] = []
    for start in range(0, len(y), batch_size):
        sl = slice(start, min(start + batch_size, len(y)))
        orig_probs.append(_predict_true_class_prob(model, orig[sl], y[sl]))
        bg_probs.append(_predict_true_class_prob(model, bg[sl], y[sl]))
        fg_probs.append(_predict_true_class_prob(model, fg[sl], y[sl]))

    orig_prob = np.concatenate(orig_probs)
    bg_prob = np.concatenate(bg_probs)
    fg_prob = np.concatenate(fg_probs)

    bg_delta = bg_prob - orig_prob
    fg_delta = fg_prob - orig_prob
    bg_score = float((bg_delta > epsilon).mean())
    fg_score = float((fg_delta > epsilon).mean())
    place_labels = np.array([int(r["place"]) for r in eval_rows.to_dict("records")], dtype=int)
    class_labels = np.array(labels, dtype=int)
    pca_res = _compute_pca_spuriousness(
        model=model,
        orig_batch=orig,
        place_labels=place_labels,
        class_labels=class_labels,
        batch_size=batch_size,
    )

    return {
        "seed": int(seed),
        "bg_score": bg_score,
        "fg_score": fg_score,
        **pca_res,
        "bg_mean_delta": float(bg_delta.mean()),
        "fg_mean_delta": float(fg_delta.mean()),
        "epsilon": epsilon,
        "n_eval": int(len(y)),
        "checkpoint_path": str(ckpt_path).replace("\\", "/"),
        "val_acc": float(val_acc),
        "bg_pool_n": bg_pool_n,
        "fg_pool_n": fg_pool_n,
    }


def _worker(args):
    seed, cfg, oracle_cfg, outdir = args
    return _score_seed(seed, cfg, oracle_cfg, outdir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    with open(cfg["input"]["exp018_config"], encoding="utf-8") as f:
        oracle_cfg = yaml.safe_load(f)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_csv = outdir / "specialized_scores.csv"
    partial_csv = outdir / "specialized_scores_partial.csv"
    summary_txt = outdir / "summary.txt"
    meta_json = outdir / "meta.json"

    seeds = [int(s) for s in cfg["evaluation"]["seeds"]]
    n_workers = int(cfg.get("n_workers", 1))

    print(f"Experiment : {outdir.name}")
    print(f"Seeds      : {seeds}")
    print(f"n_workers  : {n_workers}", flush=True)

    start = time.time()
    results: list[dict] = []
    done_seeds: set[int] = set()
    if partial_csv.exists() and not args.no_resume:
        try:
            partial_df = pd.read_csv(partial_csv)
            if not partial_df.empty:
                results = partial_df.to_dict("records")
                done_seeds = {int(r["seed"]) for r in results}
                print(f"[RESUME] loaded {len(results)} rows from {partial_csv}", flush=True)
        except Exception as e:
            print(f"[RESUME] failed to read partial file: {e}", flush=True)

    pending = [s for s in seeds if s not in done_seeds]
    print(f"[RESUME] remaining seeds: {len(pending)} / {len(seeds)}", flush=True)

    if pending:
        est_min = float(cfg["specialized"].get("est_min_per_seed", 10.0))
        est_total = (len(pending) * est_min) / max(1, n_workers)
        print(f"Estimated remaining runtime: {est_total:.1f} minutes", flush=True)

    if n_workers <= 1:
        for seed in pending:
            results.append(_score_seed(seed, cfg, oracle_cfg, outdir))
            pd.DataFrame(results).drop_duplicates(subset=["seed"], keep="last").sort_values("seed").to_csv(partial_csv, index=False)
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futures = {
                pool.submit(_worker, (seed, cfg, oracle_cfg, outdir)): seed
                for seed in pending
            }
            for fut in as_completed(futures):
                results.append(fut.result())
                pd.DataFrame(results).drop_duplicates(subset=["seed"], keep="last").sort_values("seed").to_csv(partial_csv, index=False)

    final_df = pd.DataFrame(results).drop_duplicates(subset=["seed"], keep="last").sort_values("seed").reset_index(drop=True)
    final_df.to_csv(out_csv, index=False)

    bg_ok = int((final_df["bg_score"] > final_df["fg_score"]).sum())
    n = len(final_df)
    elapsed = time.time() - start

    lines = [
        "=== exp021 Waterbirds specialized score generation ===",
        f"method: {cfg['method']['name']}",
        f"exp018_results_csv: {cfg['input']['exp018_results_csv']}",
        f"checkpoint_dir: {cfg['input']['checkpoint_dir']}",
        f"exp018_config: {cfg['input']['exp018_config']}",
        f"epsilon: {float(cfg['specialized']['epsilon'])}",
        f"n_eval: {int(cfg['specialized']['n_eval'])}",
        f"bg_pool_n: {int(cfg['specialized']['bg_pool_n'])}",
        f"fg_pool_n: {int(cfg['specialized']['fg_pool_n'])}",
        f"n(seed): {n}",
        f"bg_score > fg_score: {bg_ok}/{n} ({100.0 * bg_ok / max(1, n):.1f}%)",
        f"elapsed: {elapsed/60:.1f} min",
        "",
        final_df.to_string(index=False),
    ]
    summary_txt.write_text("\n".join(lines), encoding="utf-8")

    meta = {
        "script": Path(__file__).name,
        "config_hash": _config_hash(cfg),
        "oracle_config_hash": _config_hash(oracle_cfg),
        "git_commit": _git_commit_short(),
        "cmd": " ".join(sys.argv),
        "n_workers": n_workers,
        "seeds": seeds,
        "created_at_unix": time.time(),
    }
    meta_json.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved: {out_csv}")
    print(f"Saved: {summary_txt}")
    print(f"Saved: {meta_json}")


if __name__ == "__main__":
    main()
