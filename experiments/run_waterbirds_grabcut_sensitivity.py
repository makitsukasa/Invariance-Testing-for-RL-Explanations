"""exp022: Waterbirds GrabCut mask sensitivity with exp018 checkpoint reuse.

The goal is to quantify how stable PerformanceCheck-style intervention scores
are when the GrabCut mask is slightly perturbed. We reuse the exp018 checkpoints
and keep the original resume / summary / meta / plot outputs, while using
process-based parallelism on Windows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
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

_WORKER_BASE_MASK_CACHE: dict[int, np.ndarray] | None = None
_WORKER_CACHE_PATH: str | None = None
_CACHE_DATASET: WaterbirdsDataset | None = None


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log(message: str) -> None:
    print(f"[{_stamp()}] {message}", flush=True)


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


def _cache_path(outdir: Path) -> Path:
    return outdir / "base_mask_cache.pt"


def _init_cache_worker(root: str) -> None:
    global _CACHE_DATASET
    try:
        torch.set_num_threads(1)
    except Exception:
        pass
    try:
        torch.set_num_interop_threads(1)
    except Exception:
        pass
    try:
        cv2.setNumThreads(1)
    except Exception:
        pass
    _CACHE_DATASET = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM, seed=0)


def _mask_cache_worker(idx: int) -> tuple[int, np.ndarray]:
    if _CACHE_DATASET is None:
        raise RuntimeError("cache dataset was not initialized in worker")
    row = _CACHE_DATASET.df.iloc[idx]
    img_np = _CACHE_DATASET._load_img(row)
    return idx, grabcut_mask(img_np)


def _load_or_build_mask_cache(root: str, outdir: Path, n_workers: int) -> dict[int, np.ndarray]:
    path = _cache_path(outdir)
    if path.exists():
        _log(f"[main] loading base mask cache from {path.name}")
        return torch.load(path, map_location="cpu", weights_only=False)

    _log("[main] building base mask cache for Waterbirds test split")
    ds = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM, seed=0)
    cache: dict[int, np.ndarray] = {}
    cache_workers = max(1, min(int(n_workers), os.cpu_count() or 1))
    if cache_workers <= 1:
        for idx in range(len(ds)):
            row = ds.df.iloc[idx]
            img_np = ds._load_img(row)
            cache[idx] = grabcut_mask(img_np)
    else:
        with ProcessPoolExecutor(max_workers=cache_workers, initializer=_init_cache_worker, initargs=(root,)) as pool:
            futures = {pool.submit(_mask_cache_worker, idx): idx for idx in range(len(ds))}
            for i, fut in enumerate(as_completed(futures), start=1):
                idx, mask = fut.result()
                cache[idx] = mask
                if i % 500 == 0 or i == len(ds):
                    _log(f"[main] built {i}/{len(ds)} masks")

    torch.save(cache, path)
    _log(f"[main] saved base mask cache to {path}")
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
    z = float(norm.ppf(1 - alpha / 2))
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(max(0.0, center - margin)), float(min(1.0, center + margin))


def _rate_with_ci(k: int, n: int) -> tuple[float, float, float]:
    rate = k / n if n > 0 else 0.0
    lo, hi = _wilson_ci(k, n)
    return rate, max(0.0, rate - lo), max(0.0, hi - rate)


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


def _seed_worker(args) -> list[dict]:
    global _WORKER_BASE_MASK_CACHE, _WORKER_CACHE_PATH
    seed, cfg, oracle_cfg = args
    if _WORKER_BASE_MASK_CACHE is None:
        if _WORKER_CACHE_PATH is None:
            raise RuntimeError("worker cache path is not initialized")
        _WORKER_BASE_MASK_CACHE = torch.load(_WORKER_CACHE_PATH, map_location="cpu", weights_only=False)

    torch.set_num_threads(int(cfg.get("threads_per_worker", 4)))

    root = cfg["data"]["root"]
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    n_eval = int(cfg["intervention"]["n_eval"])
    fg_noise_std = float(cfg["intervention"]["fg_noise_std"])
    bg_pool_n = int(cfg["data"]["n_bg_pool"])
    ckpt_path = Path(cfg["input"]["checkpoint_dir"]) / f"seed_{seed}.pt"

    _log(f"[seed {seed}] start")
    model = build_oracle(seed)
    val_acc = load_oracle_checkpoint(model, ckpt_path, oracle_cfg)
    bg_pool = build_bg_pool(root, split="train", n_samples=bg_pool_n, seed=seed)

    rows: list[dict] = []
    for radius in radii:
        p_cache = {idx: _perturb_mask(mask, radius) for idx, mask in _WORKER_BASE_MASK_CACHE.items()}
        ds_clean = WaterbirdsDataset(
            root, split="test", transform=EVAL_TRANSFORM, mask_cache=p_cache, seed=seed
        )
        ds_bg = WaterbirdsDataset(
            root,
            split="test",
            transform=EVAL_TRANSFORM,
            mode="bg_replace",
            bg_pool=bg_pool,
            mask_cache=p_cache,
            seed=seed,
        )
        ds_fg = WaterbirdsDataset(
            root,
            split="test",
            transform=EVAL_TRANSFORM,
            mode="fg_noise",
            fg_noise_std=fg_noise_std,
            mask_cache=p_cache,
            seed=seed,
        )

        j_base = eval_accuracy(model, ds_clean, n_eval)
        j_bg = eval_accuracy(model, ds_bg, n_eval)
        j_fg = eval_accuracy(model, ds_fg, n_eval)

        rows.append(
            {
                "seed": int(seed),
                "mask_radius": int(radius),
                "val_acc": float(val_acc),
                "j_base": float(j_base),
                "j_bg_replace": float(j_bg),
                "j_fg_noise": float(j_fg),
                "delta_bg": float(j_base - j_bg),
                "delta_fg": float(j_base - j_fg),
                "delta_gap": float((j_base - j_bg) - (j_base - j_fg)),
                "delta_correct": bool((j_base - j_bg) > (j_base - j_fg)),
                "n_eval": int(n_eval),
                "fg_noise_std": float(fg_noise_std),
                "bg_pool_n": int(bg_pool_n),
                "checkpoint_path": str(ckpt_path).replace("\\", "/"),
                "checkpoint_version": 2,
                "checkpoint_seed": int(seed),
                "checkpoint_val_acc": float(val_acc),
            }
        )
    _log(f"[seed {seed}] done")
    return rows


def _plot(df: pd.DataFrame, out_png: Path) -> None:
    radii = sorted(int(r) for r in df["mask_radius"].unique())
    mean_bg, lo_bg, hi_bg = [], [], []
    mean_fg, lo_fg, hi_fg = [], [], []
    mean_gap, lo_gap, hi_gap = [], [], []
    ok_rates, ok_lo, ok_hi = [], [], []

    for r in radii:
        sub = df[df["mask_radius"] == r]
        m, lo, hi = _mean_ci(sub["delta_bg"].to_numpy())
        mean_bg.append(m)
        lo_bg.append(lo)
        hi_bg.append(hi)
        m, lo, hi = _mean_ci(sub["delta_fg"].to_numpy())
        mean_fg.append(m)
        lo_fg.append(lo)
        hi_fg.append(hi)
        m, lo, hi = _mean_ci(sub["delta_gap"].to_numpy())
        mean_gap.append(m)
        lo_gap.append(lo)
        hi_gap.append(hi)
        rate, lo, hi = _rate_with_ci(int(sub["delta_correct"].sum()), len(sub))
        ok_rates.append(rate)
        ok_lo.append(lo)
        ok_hi.append(hi)

    x = np.array(radii)
    with plt.rc_context(
        {
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
        }
    ):
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    _log(
        f"exp022 start: config={args.config}, outdir={args.outdir}, no_resume={args.no_resume}"
    )

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
    cache_path = _cache_path(outdir)

    seeds = [int(s) for s in cfg["evaluation"]["seeds"]]
    n_workers = int(cfg.get("n_workers", 1))

    _log(f"Experiment : {outdir.name}")
    _log(f"Seeds      : {seeds}")
    _log(f"n_workers  : {n_workers}")

    start = time.time()
    _load_or_build_mask_cache(cfg["data"]["root"], outdir, n_workers)

    results: list[dict] = []
    done_seeds: set[int] = set()

    if partial_csv.exists() and not args.no_resume:
        try:
            partial_df = pd.read_csv(partial_csv)
            if not partial_df.empty:
                results = partial_df.to_dict("records")
                done_seeds = {int(r["seed"]) for r in results}
                _log(f"[RESUME] loaded {len(results)} rows from {partial_csv}")
        except Exception as e:
            _log(f"[RESUME] failed to read partial file: {e}")
    elif args.no_resume and partial_csv.exists():
        _log(f"[NO-RESUME] ignoring existing {partial_csv}")

    pending = [s for s in seeds if s not in done_seeds]
    _log(f"[RESUME] remaining seeds: {len(pending)} / {len(seeds)}")

    if pending:
        est_min = float(cfg["experiment"].get("est_min_per_seed", 5.0))
        est_total = (len(pending) * est_min) / max(1, n_workers)
        _log(f"Estimated remaining runtime: {est_total:.1f} minutes")

    if n_workers <= 1:
        _init_worker(str(cache_path))
        for seed in pending:
            rows = _seed_worker((seed, cfg, oracle_cfg))
            results.extend(rows)
            df_partial = (
                pd.DataFrame(results)
                .drop_duplicates(subset=["seed", "mask_radius"], keep="last")
                .sort_values(["seed", "mask_radius"])
            )
            df_partial.to_csv(partial_csv, index=False)
            _log(f"[main] completed seed {seed} ({len(df_partial)} rows total)")
    else:
        with ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_init_worker,
            initargs=(str(cache_path),),
        ) as pool:
            _log(f"[main] submitted {len(pending)} seeds to worker pool")
            futures = {pool.submit(_seed_worker, (seed, cfg, oracle_cfg)): seed for seed in pending}
            for done_idx, fut in enumerate(as_completed(futures), start=1):
                rows = fut.result()
                seed = futures[fut]
                results.extend(rows)
                df_partial = (
                    pd.DataFrame(results)
                    .drop_duplicates(subset=["seed", "mask_radius"], keep="last")
                    .sort_values(["seed", "mask_radius"])
                )
                df_partial.to_csv(partial_csv, index=False)
                _log(
                    f"[main] completed seed {seed} "
                    f"({done_idx}/{len(pending)} seeds, {len(df_partial)} rows total)"
                )
                _log(f"[main] partial CSV updated: {partial_csv.name}")

    final_df = (
        pd.DataFrame(results)
        .drop_duplicates(subset=["seed", "mask_radius"], keep="last")
        .sort_values(["seed", "mask_radius"])
        .reset_index(drop=True)
    )
    final_df.to_csv(out_csv, index=False)

    radii = sorted(int(r) for r in final_df["mask_radius"].unique()) if not final_df.empty else []
    lines = [
        "=== exp022 Waterbirds GrabCut sensitivity ===",
        f"checkpoint_dir: {cfg['input']['checkpoint_dir']}",
        f"exp018_config: {cfg['input']['exp018_config']}",
        f"n(seed): {len(final_df['seed'].unique()) if not final_df.empty else 0}",
        f"mask_radii: {radii}",
        f"n_eval: {int(cfg['intervention']['n_eval'])}",
        f"fg_noise_std: {float(cfg['intervention']['fg_noise_std'])}",
        f"elapsed: {(time.time() - start) / 60:.1f} min",
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
        lines.extend(
            [
                f"radius={radius}:",
                f"  delta_bg = {mean_bg:.4f} (+{hi_bg:.4f}/-{lo_bg:.4f})",
                f"  delta_fg = {mean_fg:.4f} (+{hi_fg:.4f}/-{lo_fg:.4f})",
                f"  delta_gap = {mean_gap:.4f} (+{hi_gap:.4f}/-{lo_gap:.4f})",
                f"  bg>fg rate = {correct}/{n} ({100.0 * rate:.1f}%, 95% CI [{lo:.3f}, {hi:.3f}])",
            ]
        )

    summary_txt.write_text("\n".join(lines), encoding="utf-8")

    meta = {
        "script": Path(__file__).name,
        "config_hash": _config_hash(cfg),
        "oracle_config_hash": _config_hash(oracle_cfg),
        "git_commit": _git_commit_short(),
        "cmd": " ".join(sys.argv),
        "n_workers": n_workers,
        "seeds": seeds,
        "cache_path": str(cache_path).replace("\\", "/"),
        "created_at_unix": time.time(),
    }
    meta_json.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    if not final_df.empty:
        _plot(final_df, fig_png)

    _log(f"Saved: {out_csv}")
    _log(f"Saved: {summary_txt}")
    _log(f"Saved: {meta_json}")
    _log(f"Saved: {fig_png}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
