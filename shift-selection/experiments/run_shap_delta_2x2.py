"""exp029: SHAP と Δ を、オラクルとサロゲートの両方で計算する 2×2 比較。

exp011・exp016（run_shap_psweep.py）は、SHAP をオラクル（DQN の Q 値）で、
Δ をサロゲート（SoftMoET）で計算しており、手法の差とモデルの差が切り分けられない。
この実験では同じ seed・同じデータで次の 4 つを計算する。

    | モデル       | SHAP                                   | Δ（一様分布 [0,1] で置換したときの平均リターンの低下） |
    |--------------|----------------------------------------|-------------------------------------------------------|
    | オラクル     | Q 値（全 4 行動）に KernelExplainer    | DQN（deterministic=True）を同じ介入で走らせる          |
    | サロゲート   | 行動確率（全 4 行動）に KernelExplainer | SoftMoET（exp016 と同じ）                              |

SHAP の集約は、|SHAP| を評価サンプルと出力（行動）の両方について平均する。
補助として、各サンプルの予測行動（オラクルは greedy 行動、サロゲートは argmax 行動）
の出力だけを説明対象にした集約も記録する（*_pred_*）。

exp016 と同じ順序で乱数を消費するよう、オラクル SHAP とサロゲート Δ を先に計算し、
オラクル Δ とサロゲート SHAP を後に計算する。また、run_shap_psweep.py の集約
（`reshape(-1, n_features)`）をそのまま適用した値も shap_ora_legacy_* として記録し、
exp016 の結果と照合できるようにする。

Usage:
    python experiments/run_shap_delta_2x2.py --config experiments/configs/exp029_shap_delta_same_model.yaml
    python experiments/run_shap_delta_2x2.py --config ... --seeds 0 1 --p-values 0.0 --output-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import shap
import torch
import yaml

from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout
from experiments.run_shap_psweep import (
    SPURIOUS_IDX,
    _collect_transitions,
    _eval_intervention,
    _feature_names,
    _train_oracle,
)

CELLS = ("shap_ora", "shap_sur", "delta_ora", "delta_sur")


class _DeterministicOracle:
    """DQN を SoftMoET と同じ predict(X) -> actions の形で呼ぶためのラッパー。"""

    def __init__(self, model):
        self.model = model

    def predict(self, X: np.ndarray) -> np.ndarray:
        actions, _ = self.model.predict(X, deterministic=True)
        return np.asarray(actions)


def _kernel_shap(fn, obs: np.ndarray, shap_cfg: dict):
    """Returns (raw shap_values as returned by shap, array of shape (n_eval, n_features, n_outputs))."""
    n_features = obs.shape[1]
    bg   = obs[:shap_cfg["n_background"]]
    test = obs[:shap_cfg["n_eval"]]
    explainer = shap.KernelExplainer(fn, bg)
    raw = explainer.shap_values(test, nsamples=shap_cfg["n_samples"], silent=True)
    if isinstance(raw, list):
        arr = np.stack([np.asarray(sv, dtype=float) for sv in raw], axis=-1)
    else:
        arr = np.asarray(raw, dtype=float)
    if arr.ndim != 3 or arr.shape[0] != len(test) or arr.shape[1] != n_features:
        raise ValueError(f"unexpected shap_values shape {arr.shape}")
    return raw, arr


def _legacy_mean_abs(raw, n_features: int) -> np.ndarray:
    """run_shap_psweep._compute_shap_ranking の集約をそのまま再現する。"""
    if isinstance(raw, list):
        stacked  = np.stack([np.abs(np.array(sv, dtype=float)) for sv in raw])
        mean_abs = stacked.mean(axis=(0, 1))
    else:
        arr      = np.abs(np.array(raw, dtype=float))
        mean_abs = arr.reshape(-1, n_features).mean(axis=0)
    return mean_abs.flatten()[:n_features]


def _pred_mean_abs(arr: np.ndarray, pred_out: np.ndarray) -> np.ndarray:
    """各サンプルの予測行動の出力だけを説明対象にした mean |SHAP|。"""
    picked = arr[np.arange(arr.shape[0]), :, pred_out]
    return np.abs(picked).mean(axis=0)


def _delta(policy, spurious_p, n_noise, n_obs, n_episodes, seed, j_base) -> list[float]:
    rng = np.random.default_rng(seed + 30_000)
    j_feat = [
        _eval_intervention(policy, spurious_p, n_noise, fi, n_episodes, seed + 40_000 + fi * 1000, rng)
        for fi in range(n_obs)
    ]
    return [j_base - j for j in j_feat]


def run_one_seed(seed: int, spurious_p: float, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}  (spurious_p={spurious_p})", f"{'='*60}"]
    t0 = time.perf_counter()
    times: dict[str, float] = {}

    def lap(name: str) -> None:
        times[f"time_{name}"] = time.perf_counter() - t0 - sum(times.values())

    n_noise    = cfg["env"]["n_noise"]
    n_obs      = 3 + n_noise
    feat_names = _feature_names(n_noise)
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]
    shap_cfg   = cfg["shap"]

    # --- exp016 と同じ順序 ---------------------------------------------------
    model = _train_oracle(seed, spurious_p, n_noise, cfg["oracle"]["n_steps"])
    lap("oracle_train")

    obs_distill, act_distill = _collect_transitions(model, spurious_p, n_noise, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, n_noise, seed + 10_000, n_eval)

    moet = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])
    lap("surrogate_train")

    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train  = action_agreement(obs_eval, oracle_actions, moet)
    train_env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_s_train = evaluate_rollout(moet, train_env, n_episodes, seed + 20_000)
    train_env.close()

    delta_sur = _delta(moet, spurious_p, n_noise, n_obs, n_episodes, seed, j_s_train)
    lap("delta_sur")

    def q_fn(x: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            return model.q_net(torch.FloatTensor(x)).numpy()

    raw_ora, arr_ora = _kernel_shap(q_fn, obs_eval, shap_cfg)
    lap("shap_ora")

    # --- 追加の 2 セル ---------------------------------------------------------
    oracle_policy = _DeterministicOracle(model)
    oracle_env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_oracle_train = evaluate_rollout(model, oracle_env, n_episodes, seed + 20_000)
    oracle_env.close()
    delta_ora = _delta(oracle_policy, spurious_p, n_noise, n_obs, n_episodes, seed, j_oracle_train)
    lap("delta_ora")

    raw_sur, arr_sur = _kernel_shap(moet.predict_proba, obs_eval, shap_cfg)
    lap("shap_sur")

    test = obs_eval[:shap_cfg["n_eval"]]
    scores = {
        "shap_ora":        np.abs(arr_ora).mean(axis=(0, 2)),
        "shap_sur":        np.abs(arr_sur).mean(axis=(0, 2)),
        "delta_ora":       np.asarray(delta_ora),
        "delta_sur":       np.asarray(delta_sur),
        "shap_ora_pred":   _pred_mean_abs(arr_ora, q_fn(test).argmax(axis=1)),
        "shap_sur_pred":   _pred_mean_abs(arr_sur, moet.predict(test)),
        "shap_ora_legacy": _legacy_mean_abs(raw_ora, n_obs),
    }

    result: dict = {
        "seed": seed,
        "spurious_p": spurious_p,
        "aa_train": aa_train,
        "j_s_train": j_s_train,
        "j_oracle_train": j_oracle_train,
        "shap_ora_target": "q_values_all_actions",
        "shap_sur_target": "action_proba_all_actions",
    }
    for key, vals in scores.items():
        top = int(np.argmax(vals))
        result.update({f"{key}_{feat_names[i]}": float(vals[i]) for i in range(n_obs)})
        result[f"{key}_selected"] = feat_names[top]
        result[f"{key}_correct"] = top == SPURIOUS_IDX
    result.update(times)
    result["time_total"] = time.perf_counter() - t0

    logs.append(f"  AA={aa_train:.3f}, J_S_train={j_s_train:.3f}, J_oracle_train={j_oracle_train:.3f}")
    for key in scores:
        logs.append(f"  {key:<16} selected: {result[f'{key}_selected']:<14} "
                    f"({'OK' if result[f'{key}_correct'] else 'NG'})")
    logs.append(f"  time: " + ", ".join(f"{k[5:]}={v:.0f}s" for k, v in times.items()))
    return result, logs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument("--p-values", type=float, nargs="+")
    parser.add_argument("--output-dir")
    parser.add_argument("--n-workers", type=int)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = Path(args.output_dir) if args.output_dir else ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds     = args.seeds or cfg["evaluation"]["seeds"]
    p_values  = args.p_values or cfg["env"]["p_values"]
    n_workers = args.n_workers or cfg.get("n_workers", 4)

    print(f"Experiment : {cfg['name']}", flush=True)
    print(f"Seeds      : {seeds}", flush=True)
    print(f"p_values   : {p_values}", flush=True)
    print(f"n_workers  : {n_workers}", flush=True)

    records: dict = {}
    seed_logs: dict = {}
    t_start = time.perf_counter()

    tasks = [(s, p) for p in p_values for s in seeds]
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, p, cfg): (s, p) for s, p in tasks}
        for future in as_completed(futures):
            key = futures[future]
            rec, logs = future.result()
            records[key] = rec
            seed_logs[key] = logs
            print(f"[DONE {len(records)}/{len(tasks)} {time.perf_counter() - t_start:.0f}s] "
                  f"p={rec['spurious_p']}, seed={rec['seed']}: "
                  + ", ".join(f"{c}={'OK' if rec[f'{c}_correct'] else 'NG'}" for c in CELLS)
                  + f" ({rec['time_total']:.0f}s)", flush=True)
            pd.DataFrame(list(records.values())).sort_values(["spurious_p", "seed"]).to_csv(
                output_dir / "results_partial.csv", index=False)

    for p in p_values:
        for s in seeds:
            for line in seed_logs.get((s, p), []):
                print(line, flush=True)

    df = pd.DataFrame(list(records.values())).sort_values(["spurious_p", "seed"]).reset_index(drop=True)
    df.to_csv(output_dir / "results.csv", index=False)
    print(f"\nTotal wall time: {time.perf_counter() - t_start:.0f}s", flush=True)
    print(f"Results: {output_dir}", flush=True)


if __name__ == "__main__":
    main()
