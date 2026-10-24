"""exp020: Waterbirds mask sensitivity for delta robustness.

Runs a single-seed oracle, then evaluates delta under foreground-mask
perturbations (erosion/dilation). Saves per-perturbation CSV and a simple plot.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_waterbirds import build_oracle, train_oracle, eval_accuracy
from src.waterbirds_dataset import (
    EVAL_TRANSFORM,
    WaterbirdsDataset,
    build_bg_pool,
)


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


def _build_perturbed_mask_cache(ds: WaterbirdsDataset, radius: int) -> dict[int, np.ndarray]:
    cache: dict[int, np.ndarray] = {}
    for idx in range(len(ds)):
        row = ds.df.iloc[idx]
        img_np = ds._load_img(row)  # internal helper
        base_mask = ds._get_mask(idx, img_np)
        cache[idx] = _perturb_mask(base_mask, radius)
    return cache


def compute_delta_with_mask_radius(
    model: torch.nn.Module,
    root: str,
    n_eval: int,
    fg_noise_std: float,
    seed: int,
    bg_pool_n: int,
    mask_radius: int,
) -> dict:
    # Build base dataset only for generating base grabcut masks
    ds_for_mask = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM, seed=seed)
    perturbed_cache = _build_perturbed_mask_cache(ds_for_mask, mask_radius)
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
        "mask_radius": int(mask_radius),
        "j_base": float(j_base),
        "j_bg_replace": float(j_bg),
        "j_fg_noise": float(j_fg),
        "delta_bg": float(delta_bg),
        "delta_fg": float(delta_fg),
        "delta_gap": float(delta_bg - delta_fg),
        "delta_correct": bool(delta_bg > delta_fg),
    }


def _plot(df: pd.DataFrame, out_png: Path) -> None:
    df = df.sort_values("mask_radius")
    x = df["mask_radius"].to_numpy()
    y_bg = df["delta_bg"].to_numpy()
    y_fg = df["delta_fg"].to_numpy()
    y_gap = df["delta_gap"].to_numpy()

    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(x, y_bg, marker="o", label="delta_bg")
    ax[0].plot(x, y_fg, marker="o", label="delta_fg")
    ax[0].set_xlabel("mask radius (px)")
    ax[0].set_ylabel("delta")
    ax[0].set_title("Delta under mask perturbation")
    ax[0].legend()
    ax[0].grid(alpha=0.3)

    ax[1].plot(x, y_gap, marker="o", color="tab:red")
    ax[1].axhline(0.0, color="black", linewidth=1, alpha=0.6)
    ax[1].set_xlabel("mask radius (px)")
    ax[1].set_ylabel("delta_bg - delta_fg")
    ax[1].set_title("Decision margin")
    ax[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_csv = outdir / "results.csv"
    out_png = outdir / "fig_mask_sensitivity.png"
    out_txt = outdir / "summary.txt"

    seed = int(cfg["evaluation"]["seed"])
    radii = [int(r) for r in cfg["intervention"]["mask_radii"]]
    root = cfg["data"]["root"]
    torch.set_num_threads(int(cfg.get("threads_per_worker", 4)))

    model = build_oracle(seed)
    val_acc = train_oracle(
        model, root,
        epochs=cfg["oracle"]["epochs"],
        batch_size=cfg["oracle"]["batch_size"],
        lr=cfg["oracle"]["lr"],
        seed=seed,
    )

    rows = []
    for r in radii:
        rec = compute_delta_with_mask_radius(
            model=model,
            root=root,
            n_eval=int(cfg["intervention"]["n_eval"]),
            fg_noise_std=float(cfg["intervention"]["fg_noise_std"]),
            seed=seed,
            bg_pool_n=int(cfg["data"]["n_bg_pool"]),
            mask_radius=r,
        )
        rows.append(rec)

    df = pd.DataFrame(rows).sort_values("mask_radius").reset_index(drop=True)
    df.to_csv(out_csv, index=False)
    _plot(df, out_png)

    flips = int((~df["delta_correct"]).sum())
    lines = [
        "=== exp020 Waterbirds mask sensitivity ===",
        f"seed: {seed}",
        f"val_acc: {val_acc:.4f}",
        f"mask_radii: {radii}",
        f"decision flips (delta_bg <= delta_fg): {flips}/{len(df)}",
        "",
        df.to_string(index=False),
    ]
    out_txt.write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved: {out_csv}")
    print(f"Saved: {out_png}")
    print(f"Saved: {out_txt}")


if __name__ == "__main__":
    main()
