"""Post-hoc LIME pass for ColoredMNIST results.

Reads an existing results.csv (from run_cmnist_shap_psweep.py),
re-trains the oracle deterministically for each (seed, spurious_p) row,
computes channel-level LIME, and adds lime_color_attr / lime_struct_attr /
lime_correct / lime_ok columns to results.csv in-place.

The oracle training uses the same seed and config as the original run, so
the trained model is identical. Δ and SHAP are NOT recomputed.

Usage:
    python experiments/run_cmnist_lime_pass.py \\
        --results experiments/results/exp017_cmnist_shap_psweep_30seeds/results.csv \\
        --config  experiments/configs/exp017_cmnist_shap_psweep_30seeds.yaml

    # With custom LIME params:
    python experiments/run_cmnist_lime_pass.py \\
        --results .../results.csv --config .../config.yaml \\
        --n_eval 100 --n_samples 128 --workers 2
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.linear_model import Ridge
from torch.utils.data import DataLoader, TensorDataset
import yaml

from experiments.src.colored_mnist import ColoredMNIST


# ---------------------------------------------------------------------------
# Model (must match run_cmnist_shap_psweep.py exactly)
# ---------------------------------------------------------------------------

class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            nn.Linear(128, 2),
        )

    def forward(self, x):
        return self.net(x)


def _train_oracle(seed: int, spurious_p: float, cfg: dict) -> CNN:
    """Reproduce the oracle from the original run (same seed → same model)."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    data_cfg   = cfg["data"]
    oracle_cfg = cfg["oracle"]
    label_noise = data_cfg.get("label_noise_p", 0.0)
    data_root   = data_cfg["root"]

    train_ds = ColoredMNIST(data_root, train=True,
                             spurious_p=spurious_p,
                             label_noise_p=label_noise,
                             seed=seed)
    loader = DataLoader(train_ds, batch_size=oracle_cfg["batch_size"], shuffle=True)

    oracle = CNN()
    opt = torch.optim.Adam(oracle.parameters(), lr=oracle_cfg["lr"])
    criterion = nn.CrossEntropyLoss()
    oracle.train()
    for _ in range(oracle_cfg["epochs"]):
        for x, y in loader:
            opt.zero_grad()
            criterion(oracle(x), y).backward()
            opt.step()
    oracle.eval()
    return oracle, train_ds


def _compute_lime(oracle: CNN, eval_images: torch.Tensor,
                  n_samples: int, seed: int) -> dict:
    """Channel-level LIME: perturb R/G/B independently, fit Ridge."""
    rng = np.random.default_rng(seed)
    oracle.eval()
    color_attrs, struct_attrs = [], []

    for img_t in eval_images:
        img = img_t.numpy()                        # (3, 28, 28)
        ch_means = img.mean(axis=(1, 2))           # (3,)

        masks = rng.integers(0, 2, size=(n_samples, 3)).astype(np.float32)
        keep = masks[:, :, None, None]
        base = ch_means[None, :, None, None]
        imgs_p = keep * img[None] + (1.0 - keep) * base  # (n_samples, 3, 28, 28)

        with torch.no_grad():
            probs = torch.softmax(
                oracle(torch.tensor(imgs_p)), dim=1
            )[:, 1].numpy()

        reg = Ridge(alpha=1.0)
        reg.fit(masks, probs)
        coef_R, coef_G, _ = reg.coef_

        color_attrs.append(abs(coef_R - coef_G))
        struct_attrs.append(abs(coef_R + coef_G) / 2.0)

    lime_color = float(np.mean(color_attrs))
    lime_struct = float(np.mean(struct_attrs))
    return {
        "lime_color_attr": lime_color,
        "lime_struct_attr": lime_struct,
        "lime_correct": lime_color > lime_struct,
        "lime_ok": lime_color > lime_struct,
    }


# ---------------------------------------------------------------------------
# Per-row worker
# ---------------------------------------------------------------------------

def _worker(args: tuple) -> dict:
    seed, spurious_p, cfg, n_eval, n_samples = args
    torch.set_num_threads(cfg.get("threads_per_worker", 4))

    oracle, train_ds = _train_oracle(seed, spurious_p, cfg)

    data_cfg    = cfg["data"]
    label_noise = data_cfg.get("label_noise_p", 0.0)
    test_corr   = ColoredMNIST(data_cfg["root"], train=False,
                                spurious_p=spurious_p,
                                label_noise_p=label_noise,
                                seed=seed + 1000)
    lime_images = test_corr.images[:n_eval]
    lime_result = _compute_lime(oracle, lime_images, n_samples=n_samples, seed=seed)

    return {"seed": seed, "spurious_p": spurious_p, **lime_result}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Add LIME columns to existing ColoredMNIST results.csv")
    parser.add_argument("--results", required=True, type=Path, metavar="CSV",
                        help="Path to existing results.csv")
    parser.add_argument("--config", required=True, type=Path, metavar="YAML",
                        help="Config yaml used for the original experiment")
    parser.add_argument("--n_eval",    type=int, default=100,
                        help="Images per seed for LIME (default 100)")
    parser.add_argument("--n_samples", type=int, default=128,
                        help="Perturbation samples per image (default 128)")
    parser.add_argument("--workers",   type=int, default=None,
                        help="Parallel workers (default: from config)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite lime columns if already present")
    args = parser.parse_args()

    if not args.results.exists():
        sys.exit(f"[ERROR] {args.results} not found")

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    df = pd.read_csv(args.results)

    if "lime_ok" in df.columns and not args.overwrite:
        print("[SKIP] lime_ok already present. Use --overwrite to recompute.")
        return

    n_workers = args.workers if args.workers is not None else cfg.get("n_workers", 1)

    tasks = [
        (int(row.seed), float(row.spurious_p), cfg, args.n_eval, args.n_samples)
        for row in df.itertuples()
    ]

    print(f"LIME pass: {len(tasks)} rows, n_eval={args.n_eval}, "
          f"n_samples={args.n_samples}, workers={n_workers}")

    lime_rows: list[dict] = []
    if n_workers <= 1:
        for i, t in enumerate(tasks):
            r = _worker(t)
            lime_rows.append(r)
            status = "OK" if r["lime_ok"] else "NG"
            print(f"  [{i+1}/{len(tasks)}] p={r['spurious_p']}, seed={r['seed']}: "
                  f"lime={status} "
                  f"(color={r['lime_color_attr']:.4f}, struct={r['lime_struct_attr']:.4f})")
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            futures = {pool.submit(_worker, t): t for t in tasks}
            done = 0
            for fut in as_completed(futures):
                r = fut.result()
                lime_rows.append(r)
                done += 1
                status = "OK" if r["lime_ok"] else "NG"
                print(f"  [{done}/{len(tasks)}] p={r['spurious_p']}, seed={r['seed']}: "
                      f"lime={status}")

    lime_df = pd.DataFrame(lime_rows)[["seed", "spurious_p",
                                        "lime_color_attr", "lime_struct_attr",
                                        "lime_correct", "lime_ok"]]

    # Drop old lime columns if overwriting
    for col in ["lime_color_attr", "lime_struct_attr", "lime_correct", "lime_ok"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    df = df.merge(lime_df, on=["seed", "spurious_p"], how="left")
    df.to_csv(args.results, index=False)
    print(f"\nSaved -> {args.results}")

    # Summary
    p_values = sorted(df["spurious_p"].unique())
    print(f"\n{'p':>4}  {'delta':>10}  {'shap':>10}  {'lime':>10}")
    print("-" * 42)
    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        d  = sub["delta_correct"].sum()
        s  = sub["shap_correct"].sum()
        li = sub["lime_ok"].sum()
        print(f"{p:>4}  {d:.0f}/{n} ({d/n:.0%})  "
              f"{s:.0f}/{n} ({s/n:.0%})  "
              f"{li:.0f}/{n} ({li/n:.0%})")


if __name__ == "__main__":
    main()
