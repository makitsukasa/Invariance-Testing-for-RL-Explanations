"""exp022: Waterbirds GrabCut mask sensitivity with exp018 checkpoint reuse.

This experiment quantifies how much Delta changes when the GrabCut foreground
mask is slightly perturbed. Unlike exp020, it does *not* retrain the oracle:
it reuses the exp018 saved checkpoints for all seeds.

For each seed, we:
  1. load seed_{seed}.pt from exp018 checkpoints
  2. compute baseline GrabCut masks on the Waterbirds test split once
  3. perturb those masks by several radii (erosion / dilation)
  4. evaluate Delta_bg and Delta_fg under each radius

The output is a per-seed, per-radius CSV that can be aggregated into a
single robustness figure and summary table.
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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_waterbirds import build_oracle, eval_accuracy, load_oracle_checkpoint  # noqa: E402
from src.waterbirds_dataset import (  # noqa: E402
    EVAL_TRANSFORM,
    WaterbirdsDataset,
    build_bg_pool,
    grabcut_mask,
)


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


def _perturb_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    """radius>0: dilate, radius<0: erode, radius=0: identity."""
    if radius == 0:
        return mask
    k = abs(int(radius)) * 2 + 1
    kernel = np.ones((k, k), np.uint8)
    if radius > 0:
        out = cv2.dilate(mask.astype(np.uint8), kernel, iterations=1)
    else:
        out = cv2.erode(mask.astype(np.uint8), kernel, iterations=1)
    return (out > 0).astype(np.uint8)


def _build_base_mask_cache(ds: WaterbirdsDataset) -> dict[int, np.ndarray]:
    cache: dict[int, np.ndarray] = {}
    for idx in range(len(ds)):
        row = ds.df.iloc[idx]
        img_np = ds._load_img(row)  # internal helper from WaterbirdsDataset
        cache[idx] = grabcut_mask(img_np)
    return cache


def _mean_ci(values: np.ndarray, alpha: float = 0.05) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return 0.0, 0.0, 0.0
    mean = float(values.mean())
    if values.size == 1:
        return mean, 0.0, 0.0
    z = float(norm.ppf(1 - alpha / 2))
    se = float(values.std(ddof=1) / np.sqrt(values.size))
    lo = max(0.0 if mean >= 0 else -np.inf, mean - z * se)
    hi = mean + z * se
    return mean, float(mean - lo), float(hi - mean)


def _wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return float(max(0.0, center - margin)), float(min(1.0, center + margin))


def _rate_with_ci(k: int, n: int) -> tuple[float, float, float]:
    rate = k / n if n > 0 else 0.0
    lo, hi = _wilson_ci(k, n)
    return rate, max(0.0, rate - lo), max(0.0, hi - rate)


def _evaluate_radius(
    model: torch.nn.Module,
    root: str,
    n_eval: int,
    fg_noise_std: float,
    seed: int,
    bg_pool_n: int,
    mask_radius: int,
    base_mask_cache: dict[int, np.ndarray],
) -> dict:
    perturbed_cache = {
        idx: _perturb_mask(mask, mask_radius)
        for idx, mask in base_mask_cache.items()
    }
    bg_pool = build_bg_pool(root, split="train", n_samples=bg_pool_n, seed=seed)

    ds_clean = WaterbirdsDataset(
        root, split="test", transform=EVAL_TRANSFORM, mask_cache=perturbed_cache, seed=seed
    )
    ds_bg = WaterbirdsDataset(
        root, split="test", transform=EVAL_TRANSFORM, mode="bg_replace",
        bg_pool=bg_pool, mask_cache=perturbed_cache, seed=seed
    )
    ds_fg = WaterbirdsDataset(
        root, split="test", transform=EVAL_TRANSFORM, mode="fg_noise",
        fg_noise_std=fg_noise_std, mask_cache=perturbed_cache, seed=seed
    )

    j_base = eval_accuracy(model, ds_clean, n_eval)
    j_bg = eval_accuracy(model, ds_bg, n_eval)
    j_fg = eval_accuracy(model, ds_fg, n_eval)
    delta_bg = j_base - j_bg
    delta_fg = j_base - j_fg
    return {
        "seed": int(seed),
        "mask_radius": int(mask_radius),
        "j_base": float(j_base),
        "j_bg_replace": float(j_bg),
        "j_fg_noise": float(j_fg),
        "delta_bg": float(delta_bg),
        "delta_fg": float(delta_fg),
        "delta_gap": float(delta_bg - delta_fg),
        "delta_correct": bool(delta_bg > delta_fg),
        "n_eval": int(n_eval),
        "fg_noise_std": float(fg_noise_std),
        "bg_pool_n": int(bg_pool_n),
    }


def _plot(df: pd.DataFrame, out_png: Path) -> None:
    radii = sorted(int(r) for r in df["mask_radius"].unique())
    mean_bg, lo_bg, hi_bg = [], [], []
    mean_fg, lo_fg, hi_fg = [], [], []
    mean_gap, lo_gap, hi_gap = [], [], []
    ok_rates, ok_lo, ok_hi = [], [], []
    counts = []

    for r in radii:
        sub = df[df["mask_radius"] == r]
        counts.append(len(sub))
        m, lo, hi = _mean_ci(sub["delta_bg"].to_numpy())
        mean_bg.append(m); lo_bg.append(lo); hi_bg.append(hi)
        m, lo, hi = _mean_ci(sub["delta_fg"].to_numpy())
        mean_fg.append(m); lo_fg.append(lo); hi_fg.append(hi)
        m, lo, hi = _mean_ci(sub["delta_gap"].to_numpy())
        mean_gap.append(m); lo_gap.append(lo); hi_gap.append(hi)
        rate, lo, hi = _rate_with_ci(int(sub["delta_correct"].sum()), len(sub))
        ok_rates.append(rate); ok_lo.append(lo); ok_hi.append(hi)

    x = np.array(radii)
    with plt.rc_context({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 1.8,
        "lines.markersize": 6,
    }):
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))

        ax[0].errorbar(x, mean_bg, yerr=[lo_bg, hi_bg], fmt="o-", capsize=3, label="Δ_bg")
        ax[0].errorbar(x, mean_fg, yerr=[lo_fg, hi_fg], fmt="s--", capsize=3, label="Δ_fg")
        ax[0].errorbar(x, mean_gap, yerr=[lo_gap, hi_gap], fmt="d-", capsize=3, label="Δ_gap")
        ax[0].axhline(0.0, color="black", linewidth=1, alpha=0.6)
        ax[0].set_xlabel("mask radius (px)")
        ax[0].set_ylabel("mean Δ (95% CI)")
        ax[0].set_title("GrabCut perturbation effect")
        ax[0].legend(loc="best")
        ax[0].grid(alpha=0.3)

        ax[1].errorbar(x, ok_rates, yerr=[ok_lo, ok_hi], fmt="o-", color="#2166ac", capsize=3)
        ax[1].set_xlabel("mask radius (px)")
        ax[1].set_ylabel("P(Δ_bg > Δ_fg) (95% Wilson CI)")
        ax[1].set_ylim(-0.05, 1.05)
        ax[1].axhline(0.5, color="gray", linewidth=1, linestyle=":", alpha=0.7)
        ax[1].set_title("Decision stability")
        ax[1].grid(alpha=0.3)

        fig.suptitle("Waterbirds exp022: GrabCut mask sensitivity over 30 seeds", fontsize=11)
        fig.tight_layout()
        fig.savefig(out_png, dpi=150)
        fig.savefig(out_png.with_suffix(".pdf"), bbox_inches="tight")
        plt.close(fig)


def _seed_worker(args) -> list[dict]:
    seed, cfg, oracle_cfg = args
    torch.set_num_threads(int(cfg.get("threads_per_worker", 4)))

    root = cfg["data"]["root"]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    n_eval = int(cfg["intervention"]["n_eval"])
    fg_noise_std = float(cfg["intervention"]["fg_noise_std"])
    bg_pool_n = int(cfg["data"]["n_bg_pool"])

    ckpt_dir = Path(cfg["input"]["checkpoint_dir"])
    ckpt_path = ckpt_dir / f"seed_{seed}.pt"
    if not ckpt_path.exists():
        raise FileNotFoundError(f"checkpoint not found: {ckpt_path}")

    model = build_oracle(seed)
    val_acc = load_oracle_checkpoint(model, ckpt_path, oracle_cfg)

    ds_for_mask = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM, seed=seed)
    base_mask_cache = _build_base_mask_cache(ds_for_mask)

    rows: list[dict] = []
    for radius in radii:
        row = _evaluate_radius(
            model=model,
            root=root,
            n_eval=n_eval,
            fg_noise_std=fg_noise_std,
            seed=seed,
            bg_pool_n=bg_pool_n,
            mask_radius=radius,
            base_mask_cache=base_mask_cache,
        )
        row["val_acc"] = float(val_acc)
        row["checkpoint_path"] = str(ckpt_path).replace("\\", "/")
        row["checkpoint_version"] = 2
        row["checkpoint_seed"] = int(seed)
        row["checkpoint_val_acc"] = float(val_acc)
        rows.append(row)
    return rows


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
    out_csv = outdir / "results.csv"
    partial_csv = outdir / "results_partial.csv"
    summary_txt = outdir / "summary.txt"
    meta_json = outdir / "meta.json"
    fig_png = outdir / "fig_grabcut_sensitivity.png"

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
    elif args.no_resume and partial_csv.exists():
        print(f"[NO-RESUME] ignoring existing {partial_csv}", flush=True)

    pending = [s for s in seeds if s not in done_seeds]
    print(f"[RESUME] remaining seeds: {len(pending)} / {len(seeds)}", flush=True)

    if pending:
        est_min = float(cfg["experiment"].get("est_min_per_seed", 5.0))
        est_total = (len(pending) * est_min) / max(1, n_workers)
        print(f"Estimated remaining runtime: {est_total:.1f} minutes", flush=True)

    if n_workers <= 1:
        for seed in pending:
            rows = _seed_worker((seed, cfg, oracle_cfg))
            results.extend(rows)
            pd.DataFrame(results).drop_duplicates(
                subset=["seed", "mask_radius"], keep="last"
            ).sort_values(["seed", "mask_radius"]).to_csv(partial_csv, index=False)
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futures = {pool.submit(_seed_worker, (seed, cfg, oracle_cfg)): seed for seed in pending}
            for fut in as_completed(futures):
                rows = fut.result()
                results.extend(rows)
                pd.DataFrame(results).drop_duplicates(
                    subset=["seed", "mask_radius"], keep="last"
                ).sort_values(["seed", "mask_radius"]).to_csv(partial_csv, index=False)

    final_df = (
        pd.DataFrame(results)
        .drop_duplicates(subset=["seed", "mask_radius"], keep="last")
        .sort_values(["seed", "mask_radius"])
        .reset_index(drop=True)
    )
    final_df.to_csv(out_csv, index=False)

    radii = sorted(int(r) for r in final_df["mask_radius"].unique())
    lines = [
        "=== exp022 Waterbirds GrabCut sensitivity ===",
        f"checkpoint_dir: {cfg['input']['checkpoint_dir']}",
        f"exp018_config: {cfg['input']['exp018_config']}",
        f"n(seed): {len(final_df['seed'].unique())}",
        f"mask_radii: {radii}",
        f"n_eval: {int(cfg['intervention']['n_eval'])}",
        f"fg_noise_std: {float(cfg['intervention']['fg_noise_std'])}",
        "",
    ]

    for radius in radii:
        sub = final_df[final_df["mask_radius"] == radius]
        n = len(sub)
        correct = int(sub["delta_correct"].sum())
        rate, lo, hi = _rate_with_ci(correct, n)
        mean_bg, lo_bg, hi_bg = _mean_ci(sub["delta_bg"].to_numpy())
        mean_fg, lo_fg, hi_fg = _mean_ci(sub["delta_fg"].to_numpy())
        mean_gap, lo_gap, hi_gap = _mean_ci(sub["delta_gap"].to_numpy())
        lines += [
            f"radius={radius}:",
            f"  delta_bg = {mean_bg:.4f} (+{hi_bg:.4f}/-{lo_bg:.4f})",
            f"  delta_fg = {mean_fg:.4f} (+{hi_fg:.4f}/-{lo_fg:.4f})",
            f"  delta_gap = {mean_gap:.4f} (+{hi_gap:.4f}/-{lo_gap:.4f})",
            f"  bg>fg rate = {correct}/{n} ({100.0 * rate:.1f}%, 95% CI [{lo:.3f}, {hi:.3f}])",
        ]

    elapsed = time.time() - start
    lines += [
        "",
        f"elapsed: {elapsed/60:.1f} min",
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

    _plot(final_df, fig_png)

    print(f"Saved: {out_csv}")
    print(f"Saved: {summary_txt}")
    print(f"Saved: {meta_json}")
    print(f"Saved: {fig_png}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
