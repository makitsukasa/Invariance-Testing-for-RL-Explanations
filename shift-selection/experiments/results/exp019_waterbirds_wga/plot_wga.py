"""Plot Waterbirds worst-group accuracy for exp019."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent


def main() -> None:
    csv_path = ROOT / "worst_group_results.csv"
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)
    if "worst_group_acc" not in df.columns:
        raise ValueError("worst_group_results.csv missing worst_group_acc column")

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    seeds = df["seed"].astype(int).tolist()
    wga = df["worst_group_acc"].astype(float).tolist()
    val = df["val_acc"].astype(float).tolist() if "val_acc" in df.columns else None

    ax.plot(seeds, wga, marker="o", color="#2166ac", lw=1.8, label="Worst-group acc")
    if val is not None:
        ax.plot(seeds, val, marker="s", color="#d6604d", lw=1.4, alpha=0.8, label="Val acc")

    mean_wga = float(df["worst_group_acc"].mean())
    std_wga = float(df["worst_group_acc"].std(ddof=0))
    ax.axhline(mean_wga, color="#2166ac", ls="--", lw=1.2, alpha=0.8, label=f"Mean WGA = {mean_wga:.3f}")
    ax.fill_between(
        [-0.5, max(seeds) + 0.5],
        [mean_wga - std_wga] * 2,
        [mean_wga + std_wga] * 2,
        color="#2166ac",
        alpha=0.12,
        linewidth=0,
        label=f"±1 std = {std_wga:.3f}",
    )

    ax.set_xlim(min(seeds) - 0.5, max(seeds) + 0.5)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Seed")
    ax.set_ylabel("Accuracy")
    ax.set_title("Waterbirds exp019: worst-group accuracy per seed")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower left", fontsize=8)

    fig.tight_layout()
    out_png = ROOT / "fig_wga.png"
    out_pdf = ROOT / "fig_wga.pdf"
    fig.savefig(out_png, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_png}")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    main()
