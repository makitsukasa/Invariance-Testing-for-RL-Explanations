"""exp011: SHAP vs 介入テスト Δ の p-sweep 比較。

同一 oracle・seed で SHAP と Δ を両方計算し、spurious 特徴 c の検出率を比較する。

Usage:
    python experiments/run_shap_psweep.py --config experiments/configs/exp011_shap_psweep.yaml
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
import shap
import torch
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import DQN

from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout

SPURIOUS_IDX = 2


def _feature_names(n_noise: int) -> list[str]:
    return ["agent_x", "agent_y", "c (spurious)"] + [f"noise_{i}" for i in range(n_noise)]


def _train_oracle(seed: int, spurious_p: float, n_noise: int, n_steps: int) -> DQN:
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=n_steps)
    env.close()
    return model


def _collect_transitions(
    model: DQN, spurious_p: float, n_noise: int, seed: int, n_samples: int
) -> tuple[np.ndarray, np.ndarray]:
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    obs_list, act_list = [], []
    obs, _ = env.reset(seed=seed)
    while len(obs_list) < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        act_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        if terminated or truncated:
            obs, _ = env.reset()
    env.close()
    return np.array(obs_list, dtype=np.float32), np.array(act_list, dtype=np.int64)


def _compute_shap_ranking(model: DQN, obs: np.ndarray, shap_cfg: dict) -> tuple[int, np.ndarray]:
    """Returns (top_feature_idx, mean_abs_shap_per_feature)."""
    n_features = obs.shape[1]

    def q_fn(x: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            return model.q_net(torch.FloatTensor(x)).numpy()

    bg   = obs[:shap_cfg["n_background"]]
    test = obs[:shap_cfg["n_eval"]]
    explainer = shap.KernelExplainer(q_fn, bg)
    shap_vals = explainer.shap_values(test, nsamples=shap_cfg["n_samples"], silent=True)

    if isinstance(shap_vals, list):
        stacked  = np.stack([np.abs(np.array(sv, dtype=float)) for sv in shap_vals])
        mean_abs = stacked.mean(axis=(0, 1))
    else:
        arr      = np.abs(np.array(shap_vals, dtype=float))
        mean_abs = arr.reshape(-1, n_features).mean(axis=0)

    mean_abs = mean_abs.flatten()[:n_features]
    return int(np.argmax(mean_abs)), mean_abs


def _eval_intervention(
    surrogate: SoftMoET,
    spurious_p: float,
    n_noise: int,
    feature_idx: int,
    n_episodes: int,
    seed: int,
    rng: np.random.Generator,
) -> float:
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    total_reward = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            obs_p = obs.copy()
            obs_p[feature_idx] = float(rng.uniform(0.0, 1.0))
            action = int(surrogate.predict(obs_p[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            done = terminated or truncated
    env.close()
    return total_reward / n_episodes


def run_one_seed(seed: int, spurious_p: float, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}  (spurious_p={spurious_p})", f"{'='*60}"]

    n_noise    = cfg["env"]["n_noise"]
    n_obs      = 3 + n_noise
    feat_names = _feature_names(n_noise)
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]

    # [1/5] Oracle
    logs.append("  [1/5] Oracle training...")
    model = _train_oracle(seed, spurious_p, n_noise, cfg["oracle"]["n_steps"])

    # [2/5] Data collection
    logs.append("  [2/5] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, spurious_p, n_noise, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, n_noise, seed + 10_000, n_eval)

    # [3/5] Surrogate
    logs.append("  [3/5] Surrogate training (MoET)...")
    moet = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train   = action_agreement(obs_eval, oracle_actions, moet)
    train_env  = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_s_train  = evaluate_rollout(moet, train_env, n_episodes, seed + 20_000)
    train_env.close()
    logs.append(f"    Stage 1: AA={aa_train:.3f} ({'PASS' if aa_train>=0.9 else 'FAIL'}), J_S_train={j_s_train:.3f}")

    # [4/5] Δ intervention test
    logs.append("  [4/5] Δ intervention test...")
    rng = np.random.default_rng(seed + 30_000)
    j_s_feat: list[float] = []
    for fi in range(n_obs):
        j_f = _eval_intervention(moet, spurious_p, n_noise, fi, n_episodes, seed + 40_000 + fi * 1000, rng)
        j_s_feat.append(j_f)
    delta = [j_s_train - j_f for j_f in j_s_feat]
    delta_top_idx = int(np.argmax(delta))
    delta_correct = (delta_top_idx == SPURIOUS_IDX)
    logs.append(f"    Δ selected: {feat_names[delta_top_idx]} -> {'CORRECT' if delta_correct else 'WRONG'}")
    logs.append(f"    Δ_c={delta[SPURIOUS_IDX]:.3f}, Δ_top={delta[delta_top_idx]:.3f}")

    # [5/5] SHAP
    logs.append("  [5/5] SHAP ranking...")
    shap_top_idx, shap_vals = _compute_shap_ranking(model, obs_eval, cfg["shap"])
    shap_correct = (shap_top_idx == SPURIOUS_IDX)
    logs.append(f"    SHAP selected: {feat_names[shap_top_idx]} -> {'CORRECT' if shap_correct else 'WRONG'}")
    logs.append(f"    SHAP_c={shap_vals[SPURIOUS_IDX]:.4f}, SHAP_top={shap_vals[shap_top_idx]:.4f}")

    result = {
        "seed": seed,
        "spurious_p": spurious_p,
        "aa_train": aa_train,
        "j_s_train": j_s_train,
        **{f"delta_{feat_names[i]}": delta[i] for i in range(n_obs)},
        **{f"shap_{feat_names[i]}": shap_vals[i] for i in range(n_obs)},
        "delta_selected": feat_names[delta_top_idx],
        "delta_correct": delta_correct,
        "shap_selected": feat_names[shap_top_idx],
        "shap_correct": shap_correct,
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

    seeds    = cfg["evaluation"]["seeds"]
    p_values = cfg["env"]["p_values"]
    n_workers = cfg.get("n_workers", 4)
    feat_names = _feature_names(cfg["env"]["n_noise"])

    print(f"Experiment : {cfg['name']}")
    print(f"Seeds      : {seeds}")
    print(f"p_values   : {p_values}")

    records: dict = {}
    seed_logs: dict = {}

    tasks = [(s, p) for p in p_values for s in seeds]
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, p, cfg): (s, p) for s, p in tasks}
        for future in as_completed(futures):
            key = futures[future]
            rec, logs = future.result()
            records[key] = rec
            seed_logs[key] = logs
            print(f"[DONE] p={rec['spurious_p']}, seed={rec['seed']}: "
                  f"Δ={rec['delta_selected']}({'OK' if rec['delta_correct'] else 'NG'}), "
                  f"SHAP={rec['shap_selected']}({'OK' if rec['shap_correct'] else 'NG'})")
            # 中間保存
            pd.DataFrame(list(records.values())).sort_values(["spurious_p", "seed"]).to_csv(
                output_dir / "results_partial.csv", index=False)

    for p in p_values:
        for s in seeds:
            for line in seed_logs.get((s, p), []):
                print(line)

    df = pd.DataFrame(list(records.values())).sort_values(["spurious_p", "seed"]).reset_index(drop=True)
    df.to_csv(output_dir / "results.csv", index=False)

    # Summary
    print("\n" + "=" * 60)
    print(f"{'p':>4}  {'Δ detect':>8}  {'SHAP detect':>11}")
    print("-" * 30)
    lines = [f"=== {cfg['name']} ===", "",
             f"{'p':>4}  {'Δ detect':>8}  {'SHAP detect':>11}", "-"*30]
    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n   = len(sub)
        d_rate   = sub["delta_correct"].mean()
        sh_rate  = sub["shap_correct"].mean()
        row = f"{p:>4}  {d_rate*n:.0f}/{n} ({d_rate:.0%})  {sh_rate*n:.0f}/{n} ({sh_rate:.0%})"
        print(row)
        lines.append(row)

    lines += ["", "Per-seed:"]
    for p in p_values:
        for _, r in df[df["spurious_p"] == p].iterrows():
            lines.append(
                f"  p={p} seed={r['seed']}: "
                f"Δ={r['delta_selected']}({'OK' if r['delta_correct'] else 'NG'})  "
                f"Δ_c={r['delta_c (spurious)']:.3f}  "
                f"SHAP={r['shap_selected']}({'OK' if r['shap_correct'] else 'NG'})  "
                f"SHAP_c={r['shap_c (spurious)']:.4f}"
            )

    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")

    _plot(df, output_dir, p_values, feat_names)
    print(f"\nResults: {output_dir}")


def _plot(df: pd.DataFrame, output_dir: Path, p_values: list[float], feat_names: list[str]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Detection rate comparison
    ax = axes[0]
    delta_rates = [df[df["spurious_p"] == p]["delta_correct"].mean() for p in p_values]
    shap_rates  = [df[df["spurious_p"] == p]["shap_correct"].mean()  for p in p_values]
    x = np.arange(len(p_values))
    w = 0.35
    ax.bar(x - w/2, delta_rates, w, label="Δ (intervention)", color="steelblue")
    ax.bar(x + w/2, shap_rates,  w, label="SHAP",             color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels([f"p={p}" for p in p_values])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Detection rate (spurious c)")
    ax.set_title("Δ vs SHAP: spurious feature detection rate")
    ax.legend()
    for xi, (d, s) in enumerate(zip(delta_rates, shap_rates)):
        ax.text(xi - w/2, d + 0.03, f"{d:.0%}", ha="center", fontsize=8)
        ax.text(xi + w/2, s + 0.03, f"{s:.0%}", ha="center", fontsize=8)

    # Δ_c value by p
    ax = axes[1]
    means = [df[df["spurious_p"] == p]["delta_c (spurious)"].mean() for p in p_values]
    stds  = [df[df["spurious_p"] == p]["delta_c (spurious)"].std()  for p in p_values]
    ax.bar([f"p={p}" for p in p_values], means, yerr=stds, color="steelblue", capsize=5)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Mean Δ_c by spurious_p (± SD)")
    ax.set_ylabel("Δ_c")

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
