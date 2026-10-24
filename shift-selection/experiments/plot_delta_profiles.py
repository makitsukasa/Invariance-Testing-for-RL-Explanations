"""Visualize per-feature Δ profiles from exp005 and exp010 logs."""

import re
import sys
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent


# ── exp005 parser ─────────────────────────────────────────────────────────────

def parse_exp005(log_path: Path) -> dict:
    """Returns {p: {feature: [delta_values]}}"""
    text = log_path.read_text(encoding="utf-8", errors="ignore")

    # Split into per-seed blocks
    block_re = re.compile(
        r'Seed \d+\s+\(spurious_p=([\d.]+)\)(.*?)(?=Seed \d+\s+\(spurious_p|$)',
        re.DOTALL
    )
    train_re  = re.compile(r'J_S_train=([\d.]+)')
    feat_re   = re.compile(r'^\s{4}(.+?):\s+J_S_perturbed=([\d.]+)', re.MULTILINE)

    results = defaultdict(lambda: defaultdict(list))
    for m in block_re.finditer(text):
        p = float(m.group(1))
        block = m.group(2)
        tm = train_re.search(block)
        if not tm:
            continue
        j_train = float(tm.group(1))
        for fm in feat_re.finditer(block):
            feat  = fm.group(1).strip()
            j_per = float(fm.group(2))
            results[p][feat].append(j_train - j_per)

    return dict(results)


def plot_exp005(results: dict, out_path: Path):
    p_values = sorted(results.keys())
    # Collect feature order: x, y, c first, then noises
    sample_p = p_values[0]
    feats = list(results[sample_p].keys())
    # Put c (spurious) after x/y, before noise
    ordered = sorted(feats, key=lambda f: (
        0 if "agent_x" in f else
        1 if "agent_y" in f else
        2 if "spurious" in f else
        3
    ))
    short = {f: f.replace("agent_", "").replace(" (spurious)", "*").replace("noise_", "n") for f in ordered}

    fig, axes = plt.subplots(1, len(p_values), figsize=(14, 4), sharey=True)
    fig.suptitle("GridWorld: per-feature Δ by spurious_p  (* = spurious feature c)", fontsize=12)

    for ax, p in zip(axes, p_values):
        means = [np.mean(results[p].get(f, [0])) for f in ordered]
        stds  = [np.std(results[p].get(f, [0]))  for f in ordered]
        colors = ["#e74c3c" if "spurious" in f else "#95a5a6" for f in ordered]
        xs = range(len(ordered))
        ax.bar(xs, means, yerr=stds, color=colors, capsize=3, width=0.6)
        ax.set_xticks(xs)
        ax.set_xticklabels([short[f] for f in ordered], rotation=45, ha="right", fontsize=8)
        ax.set_title(f"p = {p}", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_ylabel("mean Δ" if ax == axes[0] else "")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved: {out_path}")


# ── exp010 parser ─────────────────────────────────────────────────────────────

def parse_exp010(summary_path: Path) -> dict:
    """Returns {p: {"hue": [deltas], "struct": [deltas]}}"""
    text = summary_path.read_text(encoding="utf-8", errors="ignore")
    row_re = re.compile(r'p=([\d.]+) seed=\d+:.*?delta_hue=([-\d.]+).*?delta_struct=([-\d.]+)')

    results = defaultdict(lambda: {"hue": [], "struct": []})
    for m in row_re.finditer(text):
        p = float(m.group(1))
        results[p]["hue"].append(float(m.group(2)))
        results[p]["struct"].append(float(m.group(3)))
    return dict(results)


def plot_exp010(results: dict, out_path: Path):
    p_values = sorted(results.keys())
    hue_means    = [np.mean(results[p]["hue"])    for p in p_values]
    hue_stds     = [np.std(results[p]["hue"])     for p in p_values]
    struct_means = [np.mean(results[p]["struct"])  for p in p_values]
    struct_stds  = [np.std(results[p]["struct"])   for p in p_values]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(p_values, hue_means,    yerr=hue_stds,    marker="o",
                label="Δ_hue (spurious)", color="#e74c3c", capsize=4)
    ax.errorbar(p_values, struct_means, yerr=struct_stds, marker="s",
                label="Δ_struct (true)",  color="#3498db", capsize=4, linestyle="--")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("spurious_p")
    ax.set_ylabel("mean Δ  (mean ± std, n=5 seeds)")
    ax.set_title("ColoredMNIST IRM: Δ_hue vs Δ_struct by spurious_p")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved: {out_path}")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    res005 = ROOT / "experiments/results/exp005_psweep_gridworld"
    res010 = ROOT / "experiments/results/exp010_cmnist_irm_psweep"

    exp005_data = parse_exp005(res005 / "run.log")
    if exp005_data:
        plot_exp005(exp005_data, res005 / "delta_profile.png")
    else:
        print("WARNING: exp005 data not found or parse failed")

    exp010_data = parse_exp010(res010 / "summary.txt")
    if exp010_data:
        plot_exp010(exp010_data, res010 / "delta_profile.png")
    else:
        print("WARNING: exp010 data not found or parse failed")
