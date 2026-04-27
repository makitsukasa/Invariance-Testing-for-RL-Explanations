"""exp013: Waterbirds spurious-feature detection (Δ vs SHAP).

Oracle: frozen ResNet-18 (ImageNet) + single FC layer fine-tuned on biased data.
Features: background (spurious) vs foreground (causal).
Δ_bg = J_train - J(bg_replace)
Δ_fg = J_train - J(fg_noise)
SHAP: GradientExplainer on FC; aggregate shap values by GrabCut mask.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yaml
from torch.utils.data import DataLoader
from torchvision import models

sys.path.insert(0, str(Path(__file__).parent))
from src.waterbirds_dataset import (
    EVAL_TRANSFORM, TRAIN_TRANSFORM,
    WaterbirdsDataset, build_bg_pool, grabcut_mask,
)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def build_oracle(seed: int) -> nn.Module:
    torch.manual_seed(seed)
    backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    for p in backbone.parameters():
        p.requires_grad = False
    backbone.fc = nn.Linear(backbone.fc.in_features, 2)
    return backbone


def train_oracle(model: nn.Module, root: str, epochs: int, batch_size: int,
                 lr: float, seed: int) -> float:
    torch.manual_seed(seed)
    ds = WaterbirdsDataset(root, split="train", transform=TRAIN_TRANSFORM)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=True,
                    num_workers=0, pin_memory=False)
    opt = torch.optim.Adam(model.fc.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for x, y in dl:
            opt.zero_grad()
            loss_fn(model(x), y).backward()
            opt.step()

    model.eval()
    val_ds = WaterbirdsDataset(root, split="val", transform=EVAL_TRANSFORM)
    val_dl = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0)
    correct = total = 0
    with torch.no_grad():
        for x, y in val_dl:
            pred = model(x).argmax(1)
            correct += (pred == y).sum().item()
            total += len(y)
    acc = correct / total if total > 0 else 0.0
    return acc


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def eval_accuracy(model: nn.Module, ds: WaterbirdsDataset,
                  n_eval: int | None = None) -> float:
    dl = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in dl:
            pred = model(x).argmax(1)
            correct += (pred == y).sum().item()
            total += len(y)
            if n_eval and total >= n_eval:
                break
    return correct / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# SHAP
# ---------------------------------------------------------------------------

def compute_shap(model: nn.Module, root: str, n_background: int,
                 n_eval: int, seed: int) -> dict:
    import shap

    rng = np.random.default_rng(seed)
    ds = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM)
    all_idx = list(range(len(ds)))
    rng.shuffle(all_idx)
    bg_idx = all_idx[:n_background]
    ev_idx = all_idx[n_background:n_background + n_eval]

    bg_imgs = torch.stack([ds[i][0] for i in bg_idx])
    ev_imgs = torch.stack([ds[i][0] for i in ev_idx])

    model.eval()
    explainer = shap.GradientExplainer(model, bg_imgs)
    sv_raw = explainer.shap_values(ev_imgs)
    sv_arr = np.array(sv_raw)
    if sv_arr.ndim == 5:
        # shape (n_eval, C, H, W, n_classes) — SHAP >= 0.41 style; use class 1
        sv = sv_arr[..., 1]
    elif isinstance(sv_raw, list):
        sv = sv_arr[1]   # list of (n_eval, C, H, W), take class 1
    else:
        sv = sv_arr      # fallback

    # Per-pixel attribution magnitude
    attr_map = np.abs(sv).mean(axis=1)  # (n_eval, 224, 224)

    # GrabCut masks for eval images (224x224 tensor → numpy uint8)
    fg_fracs, bg_fracs = [], []
    for i, idx in enumerate(ev_idx):
        # Convert tensor to uint8 numpy for GrabCut
        img_t = ev_imgs[i]
        img_np = (img_t.permute(1, 2, 0).numpy() * 255).clip(0, 255).astype(np.uint8)
        mask = grabcut_mask(img_np)
        total = attr_map[i].sum() + 1e-12
        fg_fracs.append(attr_map[i][mask == 1].sum() / total)
        bg_fracs.append(attr_map[i][mask == 0].sum() / total)

    shap_fg = float(np.mean(fg_fracs))
    shap_bg = float(np.mean(bg_fracs))
    return {
        "shap_fg": shap_fg,
        "shap_bg": shap_bg,
        "shap_correct": shap_bg > shap_fg,  # background = spurious → expect larger bg attr
    }


# ---------------------------------------------------------------------------
# Delta (intervention test)
# ---------------------------------------------------------------------------

def compute_delta(model: nn.Module, root: str, n_eval: int,
                  fg_noise_std: float, seed: int,
                  mask_cache: dict) -> dict:
    ds_clean = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM,
                                 mask_cache=mask_cache, seed=seed)
    bg_pool = build_bg_pool(root, split="train", n_samples=200, seed=seed)

    ds_bg = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM,
                              mode="bg_replace", bg_pool=bg_pool,
                              mask_cache=mask_cache, seed=seed)
    ds_fg = WaterbirdsDataset(root, split="test", transform=EVAL_TRANSFORM,
                              mode="fg_noise", fg_noise_std=fg_noise_std,
                              mask_cache=mask_cache, seed=seed)

    j_base   = eval_accuracy(model, ds_clean, n_eval)
    j_bg_rep = eval_accuracy(model, ds_bg,    n_eval)
    j_fg_nse = eval_accuracy(model, ds_fg,    n_eval)

    delta_bg = j_base - j_bg_rep
    delta_fg = j_base - j_fg_nse
    return {
        "j_base": j_base,
        "j_bg_replace": j_bg_rep,
        "j_fg_noise": j_fg_nse,
        "delta_bg": delta_bg,
        "delta_fg": delta_fg,
        "delta_correct": delta_bg > delta_fg,  # background should drop more
    }


# ---------------------------------------------------------------------------
# Single seed worker
# ---------------------------------------------------------------------------

def run_one_seed(seed: int, cfg: dict) -> dict:
    torch.set_num_threads(cfg.get("threads_per_worker", 4))
    root = cfg["data"]["root"]

    print(f"\n{'='*60}\nSeed {seed}\n{'='*60}", flush=True)

    print("  [1/4] Building oracle...", flush=True)
    model = build_oracle(seed)
    val_acc = train_oracle(
        model, root,
        epochs=cfg["oracle"]["epochs"],
        batch_size=cfg["oracle"]["batch_size"],
        lr=cfg["oracle"]["lr"],
        seed=seed,
    )
    print(f"    val_acc={val_acc:.3f}", flush=True)

    print("  [2/4] Delta intervention test...", flush=True)
    mask_cache: dict = {}
    delta_res = compute_delta(
        model, root,
        n_eval=cfg["intervention"]["n_eval"],
        fg_noise_std=cfg["intervention"]["fg_noise_std"],
        seed=seed,
        mask_cache=mask_cache,
    )
    status_d = "CORRECT" if delta_res["delta_correct"] else "WRONG"
    print(f"    delta_bg={delta_res['delta_bg']:.3f}, "
          f"delta_fg={delta_res['delta_fg']:.3f} -> {status_d}", flush=True)

    print("  [3/4] SHAP...", flush=True)
    shap_res = compute_shap(
        model, root,
        n_background=cfg["shap"]["n_background"],
        n_eval=cfg["shap"]["n_eval"],
        seed=seed,
    )
    status_s = "CORRECT" if shap_res["shap_correct"] else "WRONG"
    print(f"    shap_bg={shap_res['shap_bg']:.4f}, "
          f"shap_fg={shap_res['shap_fg']:.4f} -> {status_s}", flush=True)

    return {
        "seed": seed,
        "val_acc": val_acc,
        **delta_res,
        **shap_res,
        "delta_ok": delta_res["delta_correct"],
        "shap_ok": shap_res["shap_correct"],
    }


def _worker(args):
    seed, cfg = args
    return run_one_seed(seed, cfg)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="experiments/configs/exp013_waterbirds.yaml")
    parser.add_argument("--outdir", default="experiments/results/exp013_waterbirds")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    seeds = cfg["evaluation"]["seeds"]
    n_workers = cfg.get("n_workers", 1)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Experiment : {outdir.name}")
    print(f"Seeds      : {seeds}")
    print(f"n_workers  : {n_workers}", flush=True)

    t0 = time.time()
    results = []
    if n_workers <= 1:
        for seed in seeds:
            results.append(run_one_seed(seed, cfg))
            pd.DataFrame(results).sort_values("seed").to_csv(
                outdir / "results_partial.csv", index=False)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futures = {pool.submit(_worker, (s, cfg)): s for s in seeds}
            for fut in as_completed(futures):
                results.append(fut.result())
                pd.DataFrame(results).sort_values("seed").to_csv(
                    outdir / "results_partial.csv", index=False)

    results.sort(key=lambda r: r["seed"])

    pd.DataFrame(results).sort_values("seed").reset_index(drop=True).to_csv(
        outdir / "results.csv", index=False)

    # Summary
    delta_ok = sum(r["delta_ok"] for r in results)
    shap_ok  = sum(r["shap_ok"]  for r in results)
    n = len(results)
    print(f"\n{'='*60}")
    print(f"delta detect: {delta_ok}/{n} ({100*delta_ok//n}%)")
    print(f"SHAP  detect: {shap_ok}/{n}  ({100*shap_ok//n}%)")
    elapsed = time.time() - t0
    print(f"Elapsed: {elapsed/60:.1f} min")

    # Save summary
    with open(outdir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"=== {outdir.name} ===\n\n")
        f.write(f"delta detect: {delta_ok}/{n} ({100*delta_ok//n}%)\n")
        f.write(f"SHAP  detect: {shap_ok}/{n}  ({100*shap_ok//n}%)\n\n")
        f.write("Per-seed:\n")
        for r in results:
            ds = "OK" if r["delta_ok"] else "NG"
            ss = "OK" if r["shap_ok"]  else "NG"
            f.write(
                f"  seed={r['seed']}: "
                f"val_acc={r['val_acc']:.3f}  "
                f"delta={ds} (bg={r['delta_bg']:.3f}, fg={r['delta_fg']:.3f})  "
                f"shap={ss} (bg={r['shap_bg']:.4f}, fg={r['shap_fg']:.4f})\n"
            )


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
