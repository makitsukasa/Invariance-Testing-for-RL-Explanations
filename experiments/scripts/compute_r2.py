"""
compute_r2.py — Hopper surrogate の R² を action_diffs NPZ から計算する

使い方:
    .venv/Scripts/python.exe experiments/scripts/compute_r2.py [--exp EXP_DIR] [--out OUTPUT_CSV]

デフォルト:
    --exp experiments/results/exp011_hopper_surrogates
    --out experiments/results/exp011_hopper_surrogates/r2_summary.csv

計算方法:
    sklearn.metrics.r2_score(oracle_actions, surrogate_actions, multioutput='uniform_average')
    各 NPZ ファイル（seed × model_type × condition）に対して計算。
    同一 (model_type, condition) 内で seed を集約し mean ± std を報告。
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score


def parse_npz_filename(fname: str):
    """
    ファイル名から seed, model_type, condition を抽出する。
    例: seed42_reg_tree_train.npz -> (42, 'reg_tree', 'train')
         seed2024_reg_ebm_gravity_lo.npz -> (2024, 'reg_ebm', 'gravity_lo')
    """
    stem = fname.replace(".npz", "")
    m = re.match(r"seed(\d+)_(reg_[a-z_]+?)_([a-z_]+)$", stem)
    if not m:
        return None, None, None
    seed = int(m.group(1))
    model_type = m.group(2)
    condition = m.group(3)
    return seed, model_type, condition


def compute_r2_for_dir(action_diffs_dir: Path) -> pd.DataFrame:
    rows = []
    for npz_path in sorted(action_diffs_dir.glob("*.npz")):
        seed, model_type, condition = parse_npz_filename(npz_path.name)
        if seed is None:
            print(f"  [SKIP] cannot parse filename: {npz_path.name}")
            continue
        data = np.load(npz_path)
        oracle = data["oracle_actions"]
        surrogate = data["surrogate_actions"]
        r2 = r2_score(oracle, surrogate, multioutput="uniform_average")
        rows.append({
            "seed": seed,
            "model_type": model_type,
            "condition": condition,
            "r2": r2,
            "n_samples": len(oracle),
        })
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["model_type", "condition"])["r2"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "r2_mean", "std": "r2_std", "count": "n_seeds"})
    )
    summary["r2_mean"] = summary["r2_mean"].round(3)
    summary["r2_std"] = summary["r2_std"].round(3)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Compute R² from action_diffs NPZ files")
    parser.add_argument(
        "--exp",
        default="experiments/results/exp011_hopper_surrogates",
        help="Path to experiment directory (containing action_diffs/)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV path (default: <exp>/r2_summary.csv)",
    )
    args = parser.parse_args()

    exp_dir = Path(args.exp)
    action_diffs_dir = exp_dir / "action_diffs"
    if not action_diffs_dir.exists():
        raise FileNotFoundError(f"action_diffs/ not found in {exp_dir}")

    out_path = Path(args.out) if args.out else exp_dir / "r2_summary.csv"

    print(f"Computing R2 from: {action_diffs_dir}")
    df = compute_r2_for_dir(action_diffs_dir)
    print(f"  {len(df)} NPZ files processed")

    summary = summarize(df)
    summary.to_csv(out_path, index=False)
    print(f"\nSummary saved to: {out_path}")
    print()
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
