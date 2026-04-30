"""Compute Waterbirds worst-group accuracy by reproducing per-seed oracles.

This script re-trains the Waterbirds oracle per seed using the same config as
run_waterbirds.py, then reports group-wise test accuracy for 4 groups:
  (y, place) in {(0,0), (0,1), (1,0), (1,1)}

Usage:
  python experiments/compute_waterbirds_wga.py \
    --config experiments/configs/exp018_waterbirds_30seeds.yaml \
    --outdir experiments/results/exp018_waterbirds_30seeds
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
import yaml

from experiments.run_waterbirds import build_oracle, train_oracle
from experiments.src.waterbirds_dataset import EVAL_TRANSFORM


class WaterbirdsGroupDataset(Dataset):
    def __init__(self, root: str, split: str = "test"):
        from PIL import Image
        import numpy as np

        self.root = Path(root)
        self._Image = Image
        self._np = np
        meta = pd.read_csv(self.root / "metadata.csv")
        split_id = {"train": 0, "val": 1, "test": 2}[split]
        self.df = meta[meta["split"] == split_id].reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        path = self.root / row["img_filename"]
        img = self._Image.open(path).convert("RGB")
        x = EVAL_TRANSFORM(img)
        y = int(row["y"])
        place = int(row["place"])
        return x, y, place


def eval_group_accuracy(model: torch.nn.Module, root: str) -> dict:
    ds = WaterbirdsGroupDataset(root=root, split="test")
    dl = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)
    model.eval()

    # counts[(y,place)] = [correct, total]
    counts: dict[tuple[int, int], list[int]] = {(0, 0): [0, 0], (0, 1): [0, 0], (1, 0): [0, 0], (1, 1): [0, 0]}
    with torch.no_grad():
        for x, y, place in dl:
            pred = model(x).argmax(1)
            for i in range(len(y)):
                key = (int(y[i].item()), int(place[i].item()))
                counts[key][1] += 1
                counts[key][0] += int(pred[i].item() == y[i].item())

    acc = {}
    for key, (c, n) in counts.items():
        acc[f"acc_y{key[0]}_p{key[1]}"] = (c / n) if n > 0 else 0.0
    acc["worst_group_acc"] = min(acc.values()) if acc else 0.0
    acc["avg_group_acc"] = sum(acc.values()) / len(acc) if acc else 0.0
    return acc


def run_one_seed(seed: int, cfg: dict) -> dict:
    torch.set_num_threads(cfg.get("threads_per_worker", 4))
    root = cfg["data"]["root"]
    model = build_oracle(seed)
    val_acc = train_oracle(
        model, root,
        epochs=cfg["oracle"]["epochs"],
        batch_size=cfg["oracle"]["batch_size"],
        lr=cfg["oracle"]["lr"],
        seed=seed,
    )
    group = eval_group_accuracy(model, root)
    return {"seed": seed, "val_acc": val_acc, **group}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _git_rev_parse_short() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_csv = outdir / "worst_group_results.csv"
    out_txt = outdir / "worst_group_summary.txt"
    runtime_csv = outdir / "worst_group_runtime.csv"
    meta_json = outdir / "worst_group_meta.json"

    seeds = cfg["evaluation"]["seeds"]
    n_workers = args.workers if args.workers is not None else cfg.get("n_workers", 1)
    do_resume = not args.no_resume

    meta = {
        "task": "compute_waterbirds_wga",
        "started_at": _now_iso(),
        "git_commit": _git_rev_parse_short(),
        "config_path": str(cfg_path).replace("\\", "/"),
        "config_sha256": _sha256(cfg_path),
        "outdir": str(outdir).replace("\\", "/"),
        "workers": int(n_workers),
        "resume_enabled": bool(do_resume),
        "seeds": [int(s) for s in seeds],
        "command": " ".join(os.sys.argv),
    }
    meta_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    rows: list[dict] = []
    done_seeds: set[int] = set()
    if do_resume and out_csv.exists():
        old = pd.read_csv(out_csv)
        if "seed" in old.columns:
            old = old.drop_duplicates(subset=["seed"], keep="last")
            rows = old.to_dict("records")
            done_seeds = {int(s) for s in old["seed"].tolist()}

    pending = [int(s) for s in seeds if int(s) not in done_seeds]

    runtime_rows: list[dict] = []
    if runtime_csv.exists() and do_resume:
        try:
            runtime_rows = pd.read_csv(runtime_csv).to_dict("records")
        except Exception:
            runtime_rows = []

    if n_workers <= 1:
        for s in pending:
            t0 = time.time()
            ok = True
            err = ""
            try:
                rec = run_one_seed(s, cfg)
                rows.append(rec)
            except Exception as e:
                ok = False
                err = repr(e)
                raise
            finally:
                runtime_rows.append({
                    "seed": int(s),
                    "started_at": datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
                    "ended_at": _now_iso(),
                    "elapsed_sec": round(time.time() - t0, 3),
                    "ok": int(ok),
                    "error": err,
                })
                pd.DataFrame(runtime_rows).to_csv(runtime_csv, index=False)
                if ok:
                    pd.DataFrame(rows).sort_values("seed").to_csv(out_csv, index=False)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as pool:
            t0_map: dict[int, float] = {}
            futures = {}
            for s in pending:
                futures[pool.submit(run_one_seed, s, cfg)] = s
                t0_map[s] = time.time()
            for fut in as_completed(futures):
                rec = fut.result()
                s = int(futures[fut])
                rows.append(rec)
                runtime_rows.append({
                    "seed": s,
                    "started_at": datetime.fromtimestamp(t0_map[s]).isoformat(timespec="seconds"),
                    "ended_at": _now_iso(),
                    "elapsed_sec": round(time.time() - t0_map[s], 3),
                    "ok": 1,
                    "error": "",
                })
                pd.DataFrame(runtime_rows).to_csv(runtime_csv, index=False)
                pd.DataFrame(rows).drop_duplicates(subset=["seed"], keep="last").sort_values("seed").to_csv(out_csv, index=False)

    df = pd.DataFrame(rows).drop_duplicates(subset=["seed"], keep="last").sort_values("seed").reset_index(drop=True)
    df.to_csv(out_csv, index=False)

    mean_wga = float(df["worst_group_acc"].mean())
    std_wga = float(df["worst_group_acc"].std())
    lines = [
        "=== Waterbirds worst-group accuracy ===",
        f"seeds: {len(df)}",
        f"mean worst_group_acc: {mean_wga:.4f}",
        f"std  worst_group_acc: {std_wga:.4f}",
        "",
        "per-seed:",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"seed={int(r['seed'])}: worst={r['worst_group_acc']:.4f}, avg_group={r['avg_group_acc']:.4f}, "
            f"y0p0={r['acc_y0_p0']:.4f}, y0p1={r['acc_y0_p1']:.4f}, y1p0={r['acc_y1_p0']:.4f}, y1p1={r['acc_y1_p1']:.4f}"
        )
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    meta["completed_at"] = _now_iso()
    meta["num_completed"] = int(len(df))
    meta_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_csv}")
    print(f"Saved: {out_txt}")
    print(f"Saved: {runtime_csv}")
    print(f"Saved: {meta_json}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
