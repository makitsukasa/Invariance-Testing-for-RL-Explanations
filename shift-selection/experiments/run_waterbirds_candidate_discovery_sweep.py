"""exp025: Waterbirds candidate discovery sweep with exp018/exp022 reuse.

This experiment evaluates simple candidate discovery baselines on Waterbirds by
asking which of two candidate features, background or foreground, is more
spurious-looking before the confirmation stage. We reuse:

  - exp018 checkpoints as the oracle models
  - exp022 mask-radius Delta results as the confirmation reference

Each worker handles one (seed, n_eval) task, computes candidate scores across
multiple GrabCut mask radii, and writes one row per method / radius.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_waterbirds import build_oracle, load_oracle_checkpoint  # noqa: E402
from src.waterbirds_dataset import EVAL_TRANSFORM, WaterbirdsDataset, grabcut_mask  # noqa: E402

ROOT = Path(__file__).parent.parent
SPURIOUS_FEATURE = "background"
CAUSAL_FEATURE = "foreground"

_WORKER_BASE_MASK_CACHE: dict[int, np.ndarray] | None = None
_WORKER_CACHE_PATH: str | None = None


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _config_hash(cfg: dict) -> str:
    payload = json.dumps(cfg, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _git_commit_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _feature_order(scores: dict[str, float]) -> list[str]:
    return [name for name, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def _task_label(task: tuple[int, int]) -> str:
    seed, n_eval = task
    return f"seed={seed}, n_eval={n_eval}"


def _condition_slug(n_eval: int) -> str:
    return f"n_eval_{int(n_eval):04d}"


def _seed_log_path(output_dir: Path, n_eval: int, seed: int) -> Path:
    log_dir = output_dir / "seed_logs" / _condition_slug(n_eval)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"seed_{seed:03d}.log"


def _cache_path(output_dir: Path) -> Path:
    return output_dir / "base_mask_cache.pt"


def _mask_key(seed: int, n_eval: int) -> tuple[int, int]:
    return int(seed), int(n_eval)


def _load_metadata(root: str) -> pd.DataFrame:
    meta = pd.read_csv(Path(root) / "metadata.csv")
    meta["split"] = meta["split"].astype(int)
    meta["y"] = meta["y"].astype(int)
    meta["place"] = meta["place"].astype(int)
    return meta


def _load_img(root: str, rel_path: str) -> np.ndarray:
    return np.array(Image.open(Path(root) / rel_path).convert("RGB"))


def _to_tensor(img_np: np.ndarray) -> torch.Tensor:
    return EVAL_TRANSFORM(Image.fromarray(img_np))


def _predict_true_class_prob(model: torch.nn.Module, batch: torch.Tensor, labels: torch.Tensor) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(batch)
        probs = torch.softmax(logits, dim=1)
        return probs.gather(1, labels.view(-1, 1)).squeeze(1).cpu().numpy()


def _extract_penultimate_features(model: torch.nn.Module, batch: torch.Tensor) -> np.ndarray:
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
) -> dict[str, float | bool]:
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
        "pca_ok": bool(pca_bg_score > pca_fg_score),
    }


def _perturb_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius == 0:
        return mask
    k = abs(int(radius)) * 2 + 1
    kernel = np.ones((k, k), np.uint8)
    if radius > 0:
        out = cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)
    else:
        out = cv2.erode(mask.astype(np.uint8), kernel, iterations=1)
    return (out > 0).astype(np.uint8)


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
    rows["dataset_idx"] = np.arange(len(rows), dtype=int)
    rng = np.random.default_rng(seed)
    order = np.arange(len(rows))
    rng.shuffle(order)
    rows = rows.iloc[order[: min(n_eval, len(rows))]].reset_index(drop=True)
    return rows


def _estimate_minutes_per_task(cfg: dict, n_eval: int) -> float:
    runtime_cfg = cfg.get("runtime", {})
    explicit = runtime_cfg.get("estimated_minutes_per_task")
    if explicit is not None:
        return float(explicit)
    base = 2.0
    return base + 0.015 * float(n_eval) * len(cfg["intervention"]["mask_radii"])


def _estimate_remaining_minutes(cfg: dict, tasks: list[tuple[int, int]], n_workers: int) -> float:
    total = sum(_estimate_minutes_per_task(cfg, n_eval) for _, n_eval in tasks)
    return total / max(1, n_workers)


def _save_records(records: list[dict], path: Path) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        df.to_csv(path, index=False)
        return df
    df = df.drop_duplicates(subset=["seed", "n_eval", "mask_radius", "method"], keep="last")
    df = df.sort_values(["n_eval", "mask_radius", "seed", "method"]).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def _completed_tasks(df: pd.DataFrame, methods: list[str], radii: list[int]) -> set[tuple[int, int]]:
    if df.empty:
        return set()
    completed: set[tuple[int, int]] = set()
    grouped = df.groupby(["seed", "n_eval"])
    target_count = len(methods) * len(radii)
    for (seed, n_eval), group in grouped:
        if len(group) == target_count:
            completed.add((int(seed), int(n_eval)))
    return completed


def _update_meta(
    meta_path: Path,
    cfg: dict,
    state: str,
    output_dir: Path,
    session_id: str,
    started_at: str,
    planned_tasks: list[tuple[int, int]],
    completed_tasks: list[tuple[int, int]],
    n_workers: int,
    estimate_minutes: float,
    no_resume: bool,
    completed_at: str | None = None,
) -> None:
    meta = {
        "experiment": cfg["name"],
        "state": state,
        "session_id": session_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "output_dir": str(output_dir).replace("\\", "/"),
        "config_hash": _config_hash(cfg),
        "resume_enabled": not no_resume,
        "planned_tasks": [{"seed": s, "n_eval": n} for s, n in planned_tasks],
        "completed_tasks": [{"seed": s, "n_eval": n} for s, n in completed_tasks],
        "n_workers": int(n_workers),
        "estimated_minutes_total": float(estimate_minutes),
        "estimated_minutes_per_task": float(cfg.get("runtime", {}).get("estimated_minutes_per_task", 0.0)),
        "mask_radii": [int(r) for r in cfg["intervention"]["mask_radii"]],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_runtime_session(
    runtime_path: Path,
    session_id: str,
    started_at: str,
    ended_at: str,
    elapsed_sec: float,
    state: str,
    completed_task_count: int,
    planned_task_count: int,
    note: str,
) -> None:
    record = {
        "session_id": session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_sec": round(elapsed_sec, 3),
        "elapsed_hms": time.strftime("%H:%M:%S", time.gmtime(max(0.0, elapsed_sec))),
        "state": state,
        "completed_tasks": int(completed_task_count),
        "planned_tasks": int(planned_task_count),
        "note": note,
    }
    if runtime_path.exists():
        df = pd.read_csv(runtime_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])
    df.to_csv(runtime_path, index=False)


def _load_or_build_mask_cache(root: str, output_dir: Path, cfg: dict) -> dict[int, np.ndarray]:
    external = cfg.get("input", {}).get("mask_cache_path")
    if external:
        ext_path = ROOT / external
        if ext_path.exists():
            return torch.load(ext_path, map_location="cpu", weights_only=False)
    path = _cache_path(output_dir)
    if path.exists():
        return torch.load(path, map_location="cpu", weights_only=False)

    ds = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM, seed=0)
    cache: dict[int, np.ndarray] = {}
    for idx in range(len(ds)):
        row = ds.df.iloc[idx]
        img_np = ds._load_img(row)
        cache[idx] = grabcut_mask(img_np)
    torch.save(cache, path)
    return cache


def _init_worker(cache_path: str) -> None:
    global _WORKER_BASE_MASK_CACHE, _WORKER_CACHE_PATH
    _WORKER_CACHE_PATH = cache_path
    try:
        torch.set_num_interop_threads(1)
    except Exception:
        pass
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass
    _WORKER_BASE_MASK_CACHE = torch.load(cache_path, map_location="cpu", weights_only=False)


def _score_to_record(
    *,
    seed: int,
    n_eval: int,
    radius: int,
    method: str,
    scores: dict[str, float],
    reference: dict[str, float | bool],
    common: dict[str, float | int | str | bool],
) -> dict:
    ordered = _feature_order(scores)
    selected_feature = ordered[0]
    pc_reference_feature = SPURIOUS_FEATURE if bool(reference["delta_correct"]) else CAUSAL_FEATURE
    selected_pc_delta = (
        float(reference["delta_bg"]) if selected_feature == SPURIOUS_FEATURE else float(reference["delta_fg"])
    )
    return {
        "seed": int(seed),
        "n_eval": int(n_eval),
        "mask_radius": int(radius),
        "method": method,
        "selected_feature": selected_feature,
        "selected_score": float(scores[selected_feature]),
        "bg_score": float(scores[SPURIOUS_FEATURE]),
        "fg_score": float(scores[CAUSAL_FEATURE]),
        "top1_hit": bool(selected_feature == SPURIOUS_FEATURE),
        "pc_reference_feature": pc_reference_feature,
        "pc_top1_alignment": bool(selected_feature == pc_reference_feature),
        "selected_pc_delta": selected_pc_delta,
        "pc_delta_bg": float(reference["delta_bg"]),
        "pc_delta_fg": float(reference["delta_fg"]),
        **common,
    }


def run_one_task(
    seed: int,
    n_eval: int,
    cfg: dict,
    oracle_cfg: dict,
    delta_reference: dict[tuple[int, int], dict[str, float | bool]],
    output_dir: str,
) -> tuple[list[dict], list[str]]:
    global _WORKER_BASE_MASK_CACHE, _WORKER_CACHE_PATH
    if _WORKER_BASE_MASK_CACHE is None:
        if _WORKER_CACHE_PATH is None:
            raise RuntimeError("worker cache path is not initialized")
        _WORKER_BASE_MASK_CACHE = torch.load(_WORKER_CACHE_PATH, map_location="cpu", weights_only=False)

    torch.set_num_threads(int(cfg.get("threads_per_worker", 4)))
    root = cfg["data"]["root"]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    methods = cfg["candidate_discovery"]["methods"]
    epsilon = float(cfg["candidate_discovery"]["epsilon"])
    donor_pool_n = int(cfg["candidate_discovery"]["donor_pool_n"])
    batch_size = int(cfg["candidate_discovery"]["batch_size"])
    outdir = Path(output_dir)
    logs = [
        f"\n{'=' * 60}",
        f"Seed {seed} / n_eval={n_eval}",
        f"{'=' * 60}",
    ]
    t0 = time.time()

    meta = _load_metadata(root)
    eval_rows = _select_eval_rows(meta, n_eval=n_eval, seed=seed)

    ckpt_path = Path(cfg["input"]["checkpoint_dir"]) / f"seed_{seed}.pt"
    model = build_oracle(seed)
    val_acc = load_oracle_checkpoint(model, ckpt_path, oracle_cfg)
    logs.append(f"  [1/5] Loaded checkpoint: {ckpt_path}")
    logs.append(f"    val_acc={val_acc:.3f}")

    logs.append("  [2/5] Loading evaluation subset and donor pools...")
    bg_pool_by_y = {
        0: _build_class_donor_pool(root, meta, y=0, n_samples=donor_pool_n, seed=seed),
        1: _build_class_donor_pool(root, meta, y=1, n_samples=donor_pool_n, seed=seed),
    }
    fg_pool_by_y = {
        0: _build_class_donor_pool(root, meta, y=0, n_samples=donor_pool_n, seed=seed + 97),
        1: _build_class_donor_pool(root, meta, y=1, n_samples=donor_pool_n, seed=seed + 97),
    }

    examples: list[dict] = []
    orig_batch: list[torch.Tensor] = []
    labels: list[int] = []
    places: list[int] = []
    for eval_idx, row in enumerate(eval_rows.to_dict("records")):
        img_np = _load_img(root, row["img_filename"])
        dataset_idx = int(row["dataset_idx"])
        mask = _WORKER_BASE_MASK_CACHE[int(dataset_idx)]
        examples.append(
            {
                "img_np": img_np,
                "mask": mask,
                "y": int(row["y"]),
            }
        )
        orig_batch.append(_to_tensor(img_np))
        labels.append(int(row["y"]))
        places.append(int(row["place"]))

    orig = torch.stack(orig_batch, dim=0)
    y = torch.tensor(labels, dtype=torch.long)
    orig_probs = []
    for start in range(0, len(y), batch_size):
        sl = slice(start, min(start + batch_size, len(y)))
        orig_probs.append(_predict_true_class_prob(model, orig[sl], y[sl]))
    orig_prob = np.concatenate(orig_probs)

    logs.append("  [3/5] PCA proxy on original batch...")
    pca_res = _compute_pca_spuriousness(
        model=model,
        orig_batch=orig,
        place_labels=np.asarray(places, dtype=int),
        class_labels=np.asarray(labels, dtype=int),
        batch_size=batch_size,
    )
    logs.append(
        f"    PCA bg={pca_res['pca_bg_score']:.3f}, fg={pca_res['pca_fg_score']:.3f}, ok={pca_res['pca_ok']}"
    )

    rng = np.random.default_rng(seed + n_eval * 17)
    donor_choices_bg = [int(rng.integers(0, donor_pool_n)) for _ in examples]
    donor_choices_fg = [int(rng.integers(0, donor_pool_n)) for _ in examples]

    records: list[dict] = []
    logs.append("  [4/5] Radius sweep...")
    for radius in radii:
        bg_batch: list[torch.Tensor] = []
        fg_batch: list[torch.Tensor] = []
        for ex_idx, ex in enumerate(examples):
            y_i = int(ex["y"])
            mask = _perturb_mask(ex["mask"], radius)
            bg_donor = bg_pool_by_y[y_i][donor_choices_bg[ex_idx]]
            fg_donor = fg_pool_by_y[y_i][donor_choices_fg[ex_idx]]
            bg_img = _apply_background_replacement(ex["img_np"], mask, bg_donor)
            fg_img = _apply_foreground_replacement(ex["img_np"], mask, fg_donor)
            bg_batch.append(_to_tensor(bg_img))
            fg_batch.append(_to_tensor(fg_img))

        bg = torch.stack(bg_batch, dim=0)
        fg = torch.stack(fg_batch, dim=0)

        bg_probs, fg_probs = [], []
        for start in range(0, len(y), batch_size):
            sl = slice(start, min(start + batch_size, len(y)))
            bg_probs.append(_predict_true_class_prob(model, bg[sl], y[sl]))
            fg_probs.append(_predict_true_class_prob(model, fg[sl], y[sl]))
        bg_prob = np.concatenate(bg_probs)
        fg_prob = np.concatenate(fg_probs)

        bg_delta = bg_prob - orig_prob
        fg_delta = fg_prob - orig_prob
        bg_score = float((bg_delta > epsilon).mean())
        fg_score = float((fg_delta > epsilon).mean())
        bg_mean_delta = float(bg_delta.mean())
        fg_mean_delta = float(fg_delta.mean())

        ref_key = (int(seed), int(radius))
        if ref_key not in delta_reference:
            raise KeyError(f"Missing exp022 reference for seed={seed}, radius={radius}")
        ref = delta_reference[ref_key]

        common = {
            "epsilon": epsilon,
            "val_acc": float(val_acc),
            "checkpoint_path": str(ckpt_path).replace("\\", "/"),
            "task_elapsed_sec": time.time() - t0,
            "fraction_score_gap": float(bg_score - fg_score),
            "mean_delta_gap": float(bg_mean_delta - fg_mean_delta),
            "pca_score_gap": float(pca_res["pca_bg_score"] - pca_res["pca_fg_score"]),
        }
        method_scores = {
            "score_fraction": {
                SPURIOUS_FEATURE: bg_score,
                CAUSAL_FEATURE: fg_score,
            },
            "mean_prob_delta": {
                SPURIOUS_FEATURE: bg_mean_delta,
                CAUSAL_FEATURE: fg_mean_delta,
            },
            "pca_proxy": {
                SPURIOUS_FEATURE: float(pca_res["pca_bg_score"]),
                CAUSAL_FEATURE: float(pca_res["pca_fg_score"]),
            },
            "random": {
                SPURIOUS_FEATURE: float(rng.random()),
                CAUSAL_FEATURE: float(rng.random()),
            },
        }

        logs.append(
            f"    radius={radius}: fraction(bg={bg_score:.3f}, fg={fg_score:.3f}), "
            f"mean_delta(bg={bg_mean_delta:.3f}, fg={fg_mean_delta:.3f}), "
            f"pc_ref={'bg' if ref['delta_correct'] else 'fg'}"
        )

        for method in methods:
            records.append(
                _score_to_record(
                    seed=seed,
                    n_eval=n_eval,
                    radius=radius,
                    method=method,
                    scores=method_scores[method],
                    reference=ref,
                    common=common,
                )
            )

    logs.append("  [5/5] Done")
    logs.append(f"    Task elapsed: {time.time() - t0:.1f} sec")
    return records, logs


def _worker(args):
    seed, n_eval, cfg, oracle_cfg, delta_reference, output_dir = args
    return run_one_task(seed, n_eval, cfg, oracle_cfg, delta_reference, output_dir)


def _save_seed_log(output_dir: Path, n_eval: int, seed: int, logs: list[str]) -> None:
    _seed_log_path(output_dir, n_eval, seed).write_text("\n".join(logs) + "\n", encoding="utf-8")


def _save_summary(df: pd.DataFrame, cfg: dict, output_dir: Path, elapsed_sec: float) -> None:
    methods = cfg["candidate_discovery"]["methods"]
    n_eval_values = [int(v) for v in cfg["evaluation"]["n_eval_values"]]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]

    lines = [
        f"=== {cfg['name']} ===",
        cfg.get("description", ""),
        "",
        f"Seeds      : {cfg['evaluation']['seeds']}",
        f"n_eval     : {n_eval_values}",
        f"mask_radii : {radii}",
        f"Methods    : {methods}",
        f"Elapsed    : {elapsed_sec / 60.0:.1f} min",
        "",
    ]
    for method in methods:
        lines.append(f"[{method}]")
        lines.append(f"{'n_eval':>6} | {'radius':>6} | {'top1':>6} | {'pc_align':>8} | {'score_gap':>9}")
        lines.append("-" * 46)
        sub = df[df["method"] == method]
        for n_eval in n_eval_values:
            for radius in radii:
                cond = sub[(sub["n_eval"] == n_eval) & (sub["mask_radius"] == radius)]
                if cond.empty:
                    continue
                score_gap_col = "pca_score_gap" if method == "pca_proxy" else (
                    "mean_delta_gap" if method == "mean_prob_delta" else "fraction_score_gap"
                )
                lines.append(
                    f"{n_eval:>6d} | {radius:>6d} | "
                    f"{cond['top1_hit'].mean():>6.0%} | "
                    f"{cond['pc_top1_alignment'].mean():>8.0%} | "
                    f"{cond[score_gap_col].mean():>9.3f}"
                )
        lines.append("")
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")


def _plot(df: pd.DataFrame, cfg: dict, output_dir: Path) -> None:
    if df.empty:
        return
    methods = cfg["candidate_discovery"]["methods"]
    n_eval_values = [int(v) for v in cfg["evaluation"]["n_eval_values"]]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]

    fig, axes = plt.subplots(len(methods), 2, figsize=(10, 3.2 * len(methods)))
    if len(methods) == 1:
        axes = np.array([axes])

    for row_idx, method in enumerate(methods):
        sub = df[df["method"] == method]
        top1_grid = np.zeros((len(radii), len(n_eval_values)))
        align_grid = np.zeros((len(radii), len(n_eval_values)))
        for i, radius in enumerate(radii):
            for j, n_eval in enumerate(n_eval_values):
                cond = sub[(sub["mask_radius"] == radius) & (sub["n_eval"] == n_eval)]
                if cond.empty:
                    top1_grid[i, j] = np.nan
                    align_grid[i, j] = np.nan
                else:
                    top1_grid[i, j] = cond["top1_hit"].mean()
                    align_grid[i, j] = cond["pc_top1_alignment"].mean()

        ax = axes[row_idx, 0]
        im = ax.imshow(top1_grid, vmin=0.0, vmax=1.0, aspect="auto", cmap="viridis")
        ax.set_title(f"{method}: background selected")
        ax.set_xticks(range(len(n_eval_values)))
        ax.set_xticklabels([str(v) for v in n_eval_values])
        ax.set_yticks(range(len(radii)))
        ax.set_yticklabels([str(r) for r in radii])
        ax.set_xlabel("n_eval")
        ax.set_ylabel("mask_radius")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        ax = axes[row_idx, 1]
        im = ax.imshow(align_grid, vmin=0.0, vmax=1.0, aspect="auto", cmap="magma")
        ax.set_title(f"{method}: align with exp022 Delta")
        ax.set_xticks(range(len(n_eval_values)))
        ax.set_xticklabels([str(v) for v in n_eval_values])
        ax.set_yticks(range(len(radii)))
        ax.set_yticklabels([str(r) for r in radii])
        ax.set_xlabel("n_eval")
        ax.set_ylabel("mask_radius")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=140)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    with open(cfg["input"]["exp018_config"], encoding="utf-8") as f:
        oracle_cfg = yaml.safe_load(f)

    output_dir = ROOT / (args.outdir or cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    partial_path = output_dir / "results_partial.csv"
    results_path = output_dir / "results.csv"
    runtime_path = output_dir / "runtime_sessions.csv"
    meta_path = output_dir / "meta.json"

    delta_df = pd.read_csv(ROOT / cfg["input"]["exp022_results_csv"])
    delta_reference = {
        (int(row["seed"]), int(row["mask_radius"])): {
            "delta_bg": float(row["delta_bg"]),
            "delta_fg": float(row["delta_fg"]),
            "delta_correct": bool(row["delta_correct"]),
        }
        for _, row in delta_df.iterrows()
    }

    base_cache = _load_or_build_mask_cache(cfg["data"]["root"], output_dir, cfg)
    local_cache_path = _cache_path(output_dir)
    if not local_cache_path.exists():
        torch.save(base_cache, local_cache_path)

    seeds = [int(seed) for seed in cfg["evaluation"]["seeds"]]
    n_eval_values = [int(v) for v in cfg["evaluation"]["n_eval_values"]]
    methods = list(cfg["candidate_discovery"]["methods"])
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    n_workers = int(cfg.get("n_workers", 1))
    tasks = [(seed, n_eval) for n_eval in n_eval_values for seed in seeds]

    existing_records: list[dict] = []
    completed = set()
    if partial_path.exists() and not args.no_resume:
        try:
            existing_df = pd.read_csv(partial_path)
            if not existing_df.empty:
                existing_records = existing_df.to_dict("records")
                completed = _completed_tasks(existing_df, methods, radii)
                print(f"[RESUME] loaded {len(existing_records)} rows from {partial_path}", flush=True)
        except Exception as e:
            print(f"[RESUME] failed to load partial results: {e}", flush=True)
    elif args.no_resume and partial_path.exists():
        print(f"[NO-RESUME] ignoring existing {partial_path}", flush=True)

    pending = [task for task in tasks if task not in completed]
    estimate_remaining = _estimate_remaining_minutes(cfg, pending, n_workers)
    session_id = f"{cfg['name']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    started_at = _now_str()

    print(f"Experiment : {cfg['name']}", flush=True)
    print(f"Outdir     : {output_dir}", flush=True)
    print(f"Seeds      : {seeds}", flush=True)
    print(f"n_eval     : {n_eval_values}", flush=True)
    print(f"mask_radii : {radii}", flush=True)
    print(f"Workers    : {n_workers}", flush=True)
    print(f"Pending    : {len(pending)} / {len(tasks)} tasks", flush=True)
    print(f"Estimated remaining runtime: {estimate_remaining:.1f} minutes", flush=True)

    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="running",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_tasks=tasks,
        completed_tasks=sorted(completed),
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
    )

    t0 = time.time()
    records = list(existing_records)
    all_logs: dict[tuple[int, int], list[str]] = {}

    if n_workers <= 1:
        _init_worker(str(local_cache_path))
        for task in pending:
            seed, n_eval = task
            task_records, logs = run_one_task(seed, n_eval, cfg, oracle_cfg, delta_reference, str(output_dir))
            records.extend(task_records)
            all_logs[task] = logs
            df_partial = _save_records(records, partial_path)
            _save_seed_log(output_dir, n_eval, seed, logs)
            _update_meta(
                meta_path=meta_path,
                cfg=cfg,
                state="running",
                output_dir=output_dir,
                session_id=session_id,
                started_at=started_at,
                planned_tasks=tasks,
                completed_tasks=sorted(_completed_tasks(df_partial, methods, radii)),
                n_workers=n_workers,
                estimate_minutes=estimate_remaining,
                no_resume=args.no_resume,
            )
            print(f"[DONE] {_task_label(task)}", flush=True)
    else:
        with ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_init_worker,
            initargs=(str(local_cache_path),),
        ) as executor:
            futures = {
                executor.submit(_worker, (*task, cfg, oracle_cfg, delta_reference, str(output_dir))): task
                for task in pending
            }
            for future in as_completed(futures):
                task = futures[future]
                seed, n_eval = task
                task_records, logs = future.result()
                records.extend(task_records)
                all_logs[task] = logs
                df_partial = _save_records(records, partial_path)
                _save_seed_log(output_dir, n_eval, seed, logs)
                _update_meta(
                    meta_path=meta_path,
                    cfg=cfg,
                    state="running",
                    output_dir=output_dir,
                    session_id=session_id,
                    started_at=started_at,
                    planned_tasks=tasks,
                    completed_tasks=sorted(_completed_tasks(df_partial, methods, radii)),
                    n_workers=n_workers,
                    estimate_minutes=estimate_remaining,
                    no_resume=args.no_resume,
                )
                print(f"[DONE] {_task_label(task)}", flush=True)

    for task in sorted(all_logs):
        for line in all_logs[task]:
            print(line, flush=True)

    final_df = _save_records(records, results_path)
    elapsed_sec = time.time() - t0
    _save_summary(final_df, cfg, output_dir, elapsed_sec=elapsed_sec)
    _plot(final_df, cfg, output_dir)

    ended_at = _now_str()
    completed_final = sorted(_completed_tasks(final_df, methods, radii))
    _update_meta(
        meta_path=meta_path,
        cfg=cfg,
        state="completed",
        output_dir=output_dir,
        session_id=session_id,
        started_at=started_at,
        planned_tasks=tasks,
        completed_tasks=completed_final,
        n_workers=n_workers,
        estimate_minutes=estimate_remaining,
        no_resume=args.no_resume,
        completed_at=ended_at,
    )
    _append_runtime_session(
        runtime_path=runtime_path,
        session_id=session_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed_sec=elapsed_sec,
        state="completed",
        completed_task_count=len(completed_final),
        planned_task_count=len(tasks),
        note="Main sweep session.",
    )

    print(f"\nResults: {output_dir}", flush=True)
    print(f"Elapsed: {elapsed_sec / 60.0:.1f} minutes", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
