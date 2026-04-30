"""exp021: Compare specialized spurious baseline with Delta/SHAP on Waterbirds.

This is a posthoc comparison script. It aligns a per-seed specialized
score CSV with exp018 outputs, and optionally verifies the exp018
checkpoints that were saved during training.

The shared exp021 config points to a specialized_scores.csv with:
  seed,bg_score,fg_score
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import torch
import yaml
from scipy.stats import binomtest


def _mcnemar_p(b_only: int, a_only: int) -> float:
    # exact two-sided McNemar via binomial test on discordant pairs
    n = b_only + a_only
    if n == 0:
        return 1.0
    k = min(b_only, a_only)
    return float(2.0 * binomtest(k, n, 0.5).pvalue)


def _load_checkpoint_meta(path: Path) -> dict:
    ckpt = torch.load(path, map_location="cpu")
    return {
        "checkpoint_version": int(ckpt.get("checkpoint_version", 0)),
        "checkpoint_seed": int(ckpt.get("seed", -1)),
        "checkpoint_val_acc": float(ckpt.get("val_acc", float("nan"))),
        "checkpoint_config_hash": str(ckpt.get("config_hash", "")),
        "checkpoint_git_commit": str(ckpt.get("git_commit", "")),
    }


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
    out_txt = outdir / "summary.txt"

    ref = pd.read_csv(cfg["input"]["exp018_results_csv"])
    base = pd.read_csv(cfg["input"]["specialized_scores_csv"])
    required = {"seed", "bg_score", "fg_score"}
    miss = required - set(base.columns)
    if miss:
        raise ValueError(f"specialized_scores_csv missing columns: {sorted(miss)}")

    base = base.copy()
    base["seed"] = base["seed"].astype(int)
    base["spec_ok"] = base["bg_score"] > base["fg_score"]
    ref["seed"] = ref["seed"].astype(int)

    merged = ref.merge(base[["seed", "bg_score", "fg_score", "spec_ok"]], on="seed", how="inner")
    if merged.empty:
        raise ValueError("No overlapping seeds between exp018 results and specialized baseline.")

    ckpt_dir = cfg["input"].get("checkpoint_dir")
    if ckpt_dir:
        ckpt_dir = Path(ckpt_dir)
        merged["checkpoint_path"] = merged["seed"].apply(lambda s: str((ckpt_dir / f"seed_{int(s)}.pt").as_posix()))
        missing = [p for p in merged["checkpoint_path"].tolist() if not Path(p).exists()]
        if missing:
            raise FileNotFoundError(
                "Some exp018 checkpoints are missing. Re-run exp018 with checkpoint saving enabled. "
                f"Missing count={len(missing)}"
            )
        metas = []
        for p in merged["checkpoint_path"].tolist():
            metas.append(_load_checkpoint_meta(Path(p)))
        meta_df = pd.DataFrame(metas)
        merged = pd.concat([merged.reset_index(drop=True), meta_df], axis=1)
        if not (merged["checkpoint_version"].astype(int) == 2).all():
            raise ValueError("unexpected checkpoint_version in exp018 artifacts")
        if not (merged["checkpoint_seed"].astype(int) == merged["seed"].astype(int)).all():
            raise ValueError("checkpoint seed mismatch with exp018 results")
        if "val_acc" in merged.columns:
            if not (merged["checkpoint_val_acc"].sub(merged["val_acc"]).abs() < 1e-8).all():
                raise ValueError("checkpoint val_acc mismatch with exp018 results")

    merged.to_csv(out_csv, index=False)

    n = len(merged)
    d_ok = int(merged["delta_ok"].sum())
    s_ok = int(merged["shap_ok"].sum())
    p_ok = int(merged["spec_ok"].sum())

    d_only = int(((merged["delta_ok"] == 1) & (merged["spec_ok"] == 0)).sum())
    p_only = int(((merged["delta_ok"] == 0) & (merged["spec_ok"] == 1)).sum())
    p_mcnemar = _mcnemar_p(d_only, p_only)

    lines = [
        "=== exp021 Waterbirds specialized baseline comparison ===",
        f"specialized method: {cfg['method']['name']}",
        f"checkpoint_dir: {ckpt_dir.as_posix() if ckpt_dir else '(not provided)'}",
        f"n(seed overlap): {n}",
        "",
        f"Delta detect: {d_ok}/{n} ({100.0*d_ok/n:.1f}%)",
        f"SHAP  detect: {s_ok}/{n} ({100.0*s_ok/n:.1f}%)",
        f"Spec  detect: {p_ok}/{n} ({100.0*p_ok/n:.1f}%)",
        "",
        "Delta vs Spec cross-tab:",
        f"  Delta=OK & Spec=OK : {int(((merged['delta_ok']==1)&(merged['spec_ok']==1)).sum())}",
        f"  Delta=OK & Spec=NG : {d_only}",
        f"  Delta=NG & Spec=OK : {p_only}",
        f"  Delta=NG & Spec=NG : {int(((merged['delta_ok']==0)&(merged['spec_ok']==0)).sum())}",
        f"  McNemar exact p    : {p_mcnemar:.6f}",
    ]
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {out_csv}")
    print(f"Saved: {out_txt}")


if __name__ == "__main__":
    main()
