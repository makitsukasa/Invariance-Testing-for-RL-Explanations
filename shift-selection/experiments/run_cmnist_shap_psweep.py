"""exp012: ColoredMNIST SHAP vs 介入テスト Δ の p-sweep 比較。

IRM 設定（label_noise_p=0.25）で、同一 oracle・seed で SHAP と Δ を両方計算し、
spurious 特徴（hue / color）の検出率を比較する。

SHAP の集約方法:
  color_attr = mean(|shap_R - shap_G|) over eval images and pixels
  struct_attr = mean(|shap_R + shap_G|) / 2 over eval images and pixels
  shap_correct = (color_attr > struct_attr)

これはドメイン知識（R-G が色を, R+G が輝度＝構造を表す）を前提とした
最も有利な SHAP 集約。

Usage:
    python experiments/run_cmnist_shap_psweep.py --config experiments/configs/exp012_cmnist_shap_psweep.yaml
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import time
import uuid

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import shap
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.src.colored_mnist import ColoredMNIST, hue_shuffle, structure_noise


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


def train_model(model, loader, epochs, lr):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for x, y in loader:
            opt.zero_grad()
            criterion(model(x), y).backward()
            opt.step()


def batch_predict(model, images, batch_size=512):
    model.eval()
    preds = []
    for i in range(0, len(images), batch_size):
        with torch.no_grad():
            preds.append(model(images[i:i + batch_size]).argmax(1))
    return torch.cat(preds)


def accuracy_on(model, images, labels):
    return (batch_predict(model, images) == labels).float().mean().item()


def agreement(model_a, model_b, images):
    return (batch_predict(model_a, images) == batch_predict(model_b, images)).float().mean().item()


def _compute_shap(oracle: CNN, bg: torch.Tensor, test: torch.Tensor) -> dict:
    """Returns shap_color_attr, shap_struct_attr, and shap_correct."""
    oracle.eval()
    # GradientExplainer (expected gradients) is robust to MaxPool2d, unlike DeepExplainer
    explainer = shap.GradientExplainer(oracle, bg)
    # shap_values: list of 2 arrays (one per class), each (n_test, 3, 28, 28)
    sv_list = explainer.shap_values(test)

    # Use class-1 SHAP values (class 0 = -class 1 for cross-entropy)
    if isinstance(sv_list, list):
        sv = np.array(sv_list[1])   # (n_test, 3, 28, 28)
    else:
        sv = np.array(sv_list)

    # R-G asymmetry = color attribution (requires domain knowledge of R/G encoding)
    color_attr = float(np.abs(sv[:, 0, :, :] - sv[:, 1, :, :]).mean())
    # R+G symmetry / 2 = structure attribution (luminance / digit-presence)
    struct_attr = float(np.abs(sv[:, 0, :, :] + sv[:, 1, :, :]).mean() / 2.0)

    return {
        "shap_color_attr": color_attr,
        "shap_struct_attr": struct_attr,
        "shap_correct": color_attr > struct_attr,
    }


def run_one_seed_worker(args):
    seed, spurious_p, cfg = args
    torch.set_num_threads(cfg.get("threads_per_worker", 4))
    return run_one_seed(seed, spurious_p, cfg)


def run_one_seed(seed: int, spurious_p: float, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}  (spurious_p={spurious_p})", f"{'='*60}"]

    torch.manual_seed(seed)
    np.random.seed(seed)

    data_cfg    = cfg["data"]
    oracle_cfg  = cfg["oracle"]
    surr_cfg    = cfg["surrogate"]
    shap_cfg    = cfg["shap"]
    eval_cfg    = cfg["evaluation"]
    label_noise = data_cfg.get("label_noise_p", 0.0)
    stage2_p    = data_cfg.get("stage2_p", 1.0)
    data_root   = data_cfg["root"]

    # [1/5] Data
    logs.append("  [1/5] Loading data...")
    train_ds  = ColoredMNIST(data_root, train=True,  spurious_p=spurious_p, label_noise_p=label_noise, seed=seed)
    test_corr = ColoredMNIST(data_root, train=False, spurious_p=spurious_p, label_noise_p=label_noise, seed=seed + 1000)
    test_anti = ColoredMNIST(data_root, train=False, spurious_p=stage2_p,   label_noise_p=label_noise, seed=seed + 2000)

    train_loader = DataLoader(train_ds, batch_size=oracle_cfg["batch_size"], shuffle=True)

    # [2/5] Oracle
    logs.append("  [2/5] Oracle training...")
    oracle = CNN()
    train_model(oracle, train_loader, oracle_cfg["epochs"], oracle_cfg["lr"])
    j_oracle = accuracy_on(oracle, test_corr.images, test_corr.labels)
    logs.append(f"    J_oracle={j_oracle:.3f}")

    # [3/5] Surrogate
    logs.append("  [3/5] Surrogate distillation...")
    oracle_labels = batch_predict(oracle, train_ds.images)
    distill_ds    = TensorDataset(train_ds.images, oracle_labels)
    distill_loader = DataLoader(distill_ds, batch_size=surr_cfg["batch_size"], shuffle=True)
    surrogate = CNN()
    train_model(surrogate, distill_loader, surr_cfg["epochs"], surr_cfg["lr"])
    aa = agreement(oracle, surrogate, test_corr.images)
    logs.append(f"    AA={aa:.3f} ({'PASS' if aa >= 0.9 else 'FAIL'})")

    # [4/5] Delta intervention test
    logs.append("  [4/5] Delta intervention test...")
    j_s_train  = accuracy_on(surrogate, test_corr.images, test_corr.labels)
    j_hue      = accuracy_on(surrogate, hue_shuffle(test_corr.images,     seed=seed), test_corr.labels)
    j_struct   = accuracy_on(surrogate, structure_noise(test_corr.images, seed=seed), test_corr.labels)
    delta_hue    = j_s_train - j_hue
    delta_struct = j_s_train - j_struct
    delta_correct = delta_hue > delta_struct
    j_s_anti = accuracy_on(surrogate, test_anti.images, test_anti.labels)
    collapse  = j_s_anti < eval_cfg["collapse_threshold"]
    logs.append(f"    delta_hue={delta_hue:.3f}, delta_struct={delta_struct:.3f} -> {'CORRECT' if delta_correct else 'WRONG'}")

    # [5/5] SHAP
    logs.append("  [5/5] SHAP (GradientExplainer)...")
    n_bg   = shap_cfg["n_background"]
    n_eval = shap_cfg["n_eval"]
    bg_images   = train_ds.images[:n_bg]
    eval_images = test_corr.images[:n_eval]
    shap_result = _compute_shap(oracle, bg_images, eval_images)
    logs.append(f"    color_attr={shap_result['shap_color_attr']:.4f}, "
                f"struct_attr={shap_result['shap_struct_attr']:.4f} "
                f"-> {'CORRECT' if shap_result['shap_correct'] else 'WRONG'}")

    result = {
        "seed": seed,
        "spurious_p": spurious_p,
        "j_oracle": j_oracle,
        "aa": aa,
        "j_s_train": j_s_train,
        "delta_hue": delta_hue,
        "delta_struct": delta_struct,
        "delta_correct": bool(delta_correct),
        "j_s_anti": j_s_anti,
        "collapse": bool(collapse),
        **shap_result,
    }
    return result, logs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    partial_path = output_dir / "results_partial.csv"
    runtime_path = output_dir / "runtime_sessions.csv"
    session_start_dt = datetime.now()
    session_start_ts = time.time()
    session_status = "running"
    session_id = uuid.uuid4().hex

    seeds     = cfg["evaluation"]["seeds"]
    p_values  = cfg["data"]["p_values"]
    n_workers = cfg.get("n_workers", 1)

    print(f"Experiment : {cfg['name']}")
    print(f"Seeds      : {seeds}")
    print(f"p_values   : {p_values}")
    print(f"n_workers  : {n_workers}")

    tasks = [(s, p, cfg) for p in p_values for s in seeds]
    total_tasks = len(tasks)
    records: list[dict] = []
    done_keys: set[tuple[int, float]] = set()
    seed_logs: dict = {}

    if partial_path.exists():
        try:
            partial_df = pd.read_csv(partial_path)
            if not partial_df.empty:
                records = partial_df.to_dict("records")
                done_keys = {
                    (int(r["seed"]), float(r["spurious_p"]))
                    for r in records
                }
                print(f"[RESUME] loaded {len(records)} rows from {partial_path}")
        except Exception as e:
            print(f"[RESUME] failed to read partial file: {e}")

    tasks = [t for t in tasks if (int(t[0]), float(t[1])) not in done_keys]
    remaining_tasks = len(tasks)
    print(f"[RESUME] remaining tasks: {remaining_tasks} / {total_tasks}")

    # Persist session start immediately so interrupted runs are still traceable.
    start_row = pd.DataFrame([{
        "session_id": session_id,
        "started_at": session_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "ended_at": "",
        "elapsed_sec": "",
        "elapsed_hms": "",
        "status": "running",
        "remaining_tasks_at_start": remaining_tasks,
        "total_tasks": total_tasks,
    }])
    if runtime_path.exists():
        hist0 = pd.read_csv(runtime_path)
        hist0 = pd.concat([hist0, start_row], ignore_index=True)
    else:
        hist0 = start_row
    hist0.to_csv(runtime_path, index=False)

    try:
        if tasks:
            if n_workers <= 1:
                for t in tasks:
                    rec, logs = run_one_seed_worker(t)
                    key = (t[0], t[1])
                    records.append(rec)
                    seed_logs[key] = logs
                    print(f"[DONE] p={rec['spurious_p']}, seed={rec['seed']}: "
                          f"delta={'OK' if rec['delta_correct'] else 'NG'}, "
                          f"shap={'OK' if rec['shap_correct'] else 'NG'}")
                    pd.DataFrame(records).drop_duplicates(
                        subset=["seed", "spurious_p"], keep="last"
                    ).sort_values(["spurious_p", "seed"]).to_csv(
                        partial_path, index=False
                    )
            else:
                with ProcessPoolExecutor(max_workers=n_workers) as executor:
                    futures = {executor.submit(run_one_seed_worker, t): (t[0], t[1]) for t in tasks}
                    for future in as_completed(futures):
                        key = futures[future]
                        rec, logs = future.result()
                        records.append(rec)
                        seed_logs[key] = logs
                        print(f"[DONE] p={rec['spurious_p']}, seed={rec['seed']}: "
                              f"delta={'OK' if rec['delta_correct'] else 'NG'}, "
                              f"shap={'OK' if rec['shap_correct'] else 'NG'}")
                        # 中間保存
                        pd.DataFrame(records).drop_duplicates(
                            subset=["seed", "spurious_p"], keep="last"
                        ).sort_values(["spurious_p", "seed"]).to_csv(
                            partial_path, index=False
                        )

        for p in p_values:
            for s in seeds:
                for line in seed_logs.get((s, p), []):
                    print(line)

        df = pd.DataFrame(records).drop_duplicates(
            subset=["seed", "spurious_p"], keep="last"
        ).sort_values(["spurious_p", "seed"]).reset_index(drop=True)
        df.to_csv(output_dir / "results.csv", index=False)

        # Summary
        print("\n" + "=" * 60)
        print(f"{'p':>4}  {'delta detect':>12}  {'SHAP detect':>11}")
        print("-" * 35)
        lines = [f"=== {cfg['name']} ===", "",
                 f"{'p':>4}  {'delta detect':>12}  {'SHAP detect':>11}", "-" * 35]
        for p in p_values:
            sub = df[df["spurious_p"] == p]
            n         = len(sub)
            d_rate    = sub["delta_correct"].mean()
            sh_rate   = sub["shap_correct"].mean()
            row = f"{p:>4}  {d_rate*n:.0f}/{n} ({d_rate:.0%})  {sh_rate*n:.0f}/{n} ({sh_rate:.0%})"
            print(row)
            lines.append(row)

        lines += ["", "Per-seed:"]
        for p in p_values:
            for _, r in df[df["spurious_p"] == p].iterrows():
                lines.append(
                    f"  p={p} seed={int(r['seed'])}: "
                    f"delta={'OK' if r['delta_correct'] else 'NG'} "
                    f"(hue={r['delta_hue']:.3f}, struct={r['delta_struct']:.3f})  "
                    f"shap={'OK' if r['shap_correct'] else 'NG'} "
                    f"(color_attr={r['shap_color_attr']:.4f}, struct_attr={r['shap_struct_attr']:.4f})"
                )

        (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")

        _plot(df, output_dir, p_values)
        print(f"\nResults: {output_dir}")
        session_status = "ok"
    except Exception:
        session_status = "error"
        raise
    finally:
        session_end_dt = datetime.now()
        elapsed_sec = int(time.time() - session_start_ts)
        elapsed_h = elapsed_sec // 3600
        elapsed_m = (elapsed_sec % 3600) // 60
        elapsed_s = elapsed_sec % 60
        elapsed_hms = f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}"

        if runtime_path.exists():
            hist = pd.read_csv(runtime_path)
        else:
            # Fallback: runtime file was removed while running.
            hist = pd.DataFrame([{
                "session_id": session_id,
                "started_at": session_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "ended_at": "",
                "elapsed_sec": "",
                "elapsed_hms": "",
                "status": "running",
                "remaining_tasks_at_start": remaining_tasks,
                "total_tasks": total_tasks,
            }])

        mask = hist.get("session_id", pd.Series(dtype=str)) == session_id
        if mask.any():
            hist.loc[mask, "ended_at"] = session_end_dt.strftime("%Y-%m-%d %H:%M:%S")
            hist.loc[mask, "elapsed_sec"] = elapsed_sec
            hist.loc[mask, "elapsed_hms"] = elapsed_hms
            hist.loc[mask, "status"] = session_status
            hist.loc[mask, "remaining_tasks_at_start"] = remaining_tasks
            hist.loc[mask, "total_tasks"] = total_tasks
        else:
            hist = pd.concat([hist, pd.DataFrame([{
                "session_id": session_id,
                "started_at": session_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "ended_at": session_end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_sec": elapsed_sec,
                "elapsed_hms": elapsed_hms,
                "status": session_status,
                "remaining_tasks_at_start": remaining_tasks,
                "total_tasks": total_tasks,
            }])], ignore_index=True)
        hist.to_csv(runtime_path, index=False)

        ok_elapsed = pd.to_numeric(
            hist.loc[hist["status"] == "ok", "elapsed_sec"], errors="coerce"
        ).fillna(0).sum()
        ok_elapsed = int(ok_elapsed)
        ok_h = ok_elapsed // 3600
        ok_m = (ok_elapsed % 3600) // 60
        ok_s = ok_elapsed % 60
        print(f"[TIME] session={elapsed_hms} status={session_status}")
        print(f"[TIME] cumulative_ok={ok_h:02d}:{ok_m:02d}:{ok_s:02d} ({runtime_path.name})")


def _plot(df: pd.DataFrame, output_dir: Path, p_values: list[float]) -> None:
    has_lime = "lime_ok" in df.columns
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Detection rate comparison
    ax = axes[0]
    delta_rates = [df[df["spurious_p"] == p]["delta_correct"].mean() for p in p_values]
    shap_rates  = [df[df["spurious_p"] == p]["shap_correct"].mean()  for p in p_values]
    x = np.arange(len(p_values))
    if has_lime:
        lime_rates = [df[df["spurious_p"] == p]["lime_ok"].mean() for p in p_values]
        w = 0.25
        ax.bar(x - w, delta_rates, w, label="Δ (intervention)", color="steelblue")
        ax.bar(x,     shap_rates,  w, label="SHAP",             color="tomato")
        ax.bar(x + w, lime_rates,  w, label="LIME (channel)",   color="seagreen")
        for xi, (d, s, li) in enumerate(zip(delta_rates, shap_rates, lime_rates)):
            ax.text(xi - w, d + 0.03, f"{d:.0%}", ha="center", fontsize=7)
            ax.text(xi,     s + 0.03, f"{s:.0%}", ha="center", fontsize=7)
            ax.text(xi + w, li + 0.03, f"{li:.0%}", ha="center", fontsize=7)
    else:
        w = 0.35
        ax.bar(x - w/2, delta_rates, w, label="delta (intervention)", color="steelblue")
        ax.bar(x + w/2, shap_rates,  w, label="SHAP (DK-aggregation)", color="tomato")
        for xi, (d, s) in enumerate(zip(delta_rates, shap_rates)):
            ax.text(xi - w/2, d + 0.03, f"{d:.0%}", ha="center", fontsize=8)
            ax.text(xi + w/2, s + 0.03, f"{s:.0%}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"p={p}" for p in p_values])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Detection rate (hue = spurious)")
    ax.set_title("ColoredMNIST: Δ vs SHAP vs LIME detection")
    ax.legend()

    # delta_hue and delta_struct means by p
    ax = axes[1]
    hue_means    = [df[df["spurious_p"] == p]["delta_hue"].mean() for p in p_values]
    struct_means = [df[df["spurious_p"] == p]["delta_struct"].mean() for p in p_values]
    hue_stds    = [df[df["spurious_p"] == p]["delta_hue"].std() for p in p_values]
    struct_stds = [df[df["spurious_p"] == p]["delta_struct"].std() for p in p_values]
    ax.errorbar(p_values, hue_means,    yerr=hue_stds,    marker="o",
                label="delta_hue (spurious)",  color="tomato",     capsize=4)
    ax.errorbar(p_values, struct_means, yerr=struct_stds, marker="s",
                label="delta_struct (true)", color="steelblue", capsize=4, linestyle="--")
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("spurious_p")
    ax.set_ylabel("mean delta")
    ax.set_title("delta_hue vs delta_struct by p (mean +/- SD)")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
