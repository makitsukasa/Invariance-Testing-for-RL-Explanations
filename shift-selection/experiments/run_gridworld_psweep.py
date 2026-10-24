"""End-to-end pipeline sweep over spurious_p — exp005.

各 p で:
  1. Oracle 学習（spurious_p=p で訓練）
  2. サロゲート蒸留
  3. 介入テスト → スプリアス候補を自動選択
  4. Stage 2: 選択した特徴を反転して J_S 崩壊を確認

問い:
  - Q1. spurious_p が上がるほど検出率はどう落ちるか
  - Q2. 介入テストで c を選択できたとき、Stage 2 も一致して崩壊するか（end-to-end）

Usage:
    python experiments/run_gridworld_psweep.py --config experiments/configs/exp005_psweep_gridworld.yaml
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


# ---------------------------------------------------------------------------
# Oracle + Data collection
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Per-feature intervention rollout
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Single-seed pipeline
# ---------------------------------------------------------------------------

def run_one_seed(seed: int, spurious_p: float, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}  (spurious_p={spurious_p})", f"{'='*60}"]

    n_noise    = cfg["env"]["n_noise"]
    n_obs      = 3 + n_noise
    feat_names = _feature_names(n_noise)
    n_episodes = cfg["evaluation"]["n_eval_episodes"]
    n_distill  = cfg["surrogate"]["n_distill_samples"]
    n_eval     = cfg["evaluation"]["n_eval_samples"]

    logs.append("  [1/4] Oracle training...")
    model = _train_oracle(seed, spurious_p, n_noise, cfg["oracle"]["n_steps"])

    logs.append("  [2/4] Data collection...")
    obs_distill, act_distill = _collect_transitions(model, spurious_p, n_noise, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, n_noise, seed + 10_000, n_eval)

    logs.append("  [3/4] Surrogate training (MoET)...")
    moet = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train    = action_agreement(obs_eval, oracle_actions, moet)
    train_env   = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_s_train   = evaluate_rollout(moet, train_env, n_episodes, seed + 20_000)
    train_env.close()
    stage1_pass = aa_train >= 0.9
    logs.append(f"    Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), J_S_train={j_s_train:.3f}")

    logs.append("  [4a/5] Per-feature intervention test...")
    rng = np.random.default_rng(seed + 30_000)
    j_s_feat: list[float] = []
    for fi in range(n_obs):
        j_f = _eval_intervention(
            moet, spurious_p, n_noise,
            fi, n_episodes, seed + 40_000 + fi * 1000, rng,
        )
        j_s_feat.append(j_f)
        logs.append(f"    {feat_names[fi]}: J_S_perturbed={j_f:.3f}")

    delta = [j_s_train - j_f for j_f in j_s_feat]
    top_idx = int(np.argmax(delta))
    intervention_correct = (top_idx == SPURIOUS_IDX)
    logs.append(f"    Auto-selected: {feat_names[top_idx]} -> "
                f"{'CORRECT (c)' if intervention_correct else 'WRONG'}")

    logs.append("  [4b/5] Stage 2: c を反転して J_S 崩壊を確認...")
    rev_env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise, eval_mode="reversed")
    j_s_rev = evaluate_rollout(moet, rev_env, n_episodes, seed + 50_000)
    rev_env.close()
    # c の反転で J_S が半分以下に落ちれば崩壊とみなす
    c_collapse = j_s_train > 0 and j_s_rev < 0.5 * j_s_train
    logs.append(f"    J_S_train={j_s_train:.3f}, J_S_rev={j_s_rev:.3f} -> "
                f"{'COLLAPSE' if c_collapse else 'no collapse'}")

    # end-to-end 成功: 介入テストで c を選択 かつ Stage 2 でも崩壊確認
    e2e_success = intervention_correct and c_collapse

    result = {
        "seed": seed,
        "spurious_p": spurious_p,
        "aa_train": aa_train,
        "stage1_pass": stage1_pass,
        "j_s_train": j_s_train,
        "j_s_c_reversed": j_s_rev,
        **{f"delta_{feat_names[i]}": delta[i] for i in range(n_obs)},
        "intervention_selected": feat_names[top_idx],
        "intervention_correct": intervention_correct,
        "c_collapse": c_collapse,
        "e2e_success": e2e_success,
    }
    return result, logs

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds     = cfg["evaluation"]["seeds"]
    p_values  = cfg["env"]["p_values"]
    n_workers = cfg.get("n_workers", 4)
    feat_names = _feature_names(cfg["env"]["n_noise"])

    print(f"Experiment : {cfg.get('name', 'unknown')}")
    print(f"Seeds      : {seeds}")
    print(f"p_values   : {p_values}")
    print(f"Workers    : {n_workers}")

    records:   list[dict]           = []
    seed_logs: dict[tuple, list[str]] = {}

    tasks = [(s, p) for p in p_values for s in seeds]

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, p, cfg): (s, p) for s, p in tasks}
        for future in as_completed(futures):
            key = futures[future]
            rec, logs = future.result()
            records.append(rec)
            seed_logs[key] = logs
            print(f"[DONE] p={rec['spurious_p']}, seed={rec['seed']}: "
                  f"selected={rec['intervention_selected']}, "
                  f"correct={rec['intervention_correct']}, "
                  f"collapse={rec['c_collapse']}, "
                  f"e2e={rec['e2e_success']}")

    for p in p_values:
        for s in seeds:
            for line in seed_logs.get((s, p), []):
                print(line)

    df = pd.DataFrame(records).sort_values(["spurious_p", "seed"]).reset_index(drop=True)
    df.to_csv(output_dir / "results.csv", index=False)

    _print_summary(df, p_values, feat_names)
    _save_summary_txt(df, cfg, output_dir, p_values, feat_names)
    _plot(df, output_dir, p_values, feat_names)
    print(f"\nResults: {output_dir}")


def _print_summary(df: pd.DataFrame, p_values: list[float], feat_names: list[str]) -> None:
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'p':>5} | {'AA>=0.9':>7} | {'detect c':>8} | {'collapse':>8} | {'e2e':>5}")
    print("-" * 45)
    for p in p_values:
        sub = df[df["spurious_p"] == p]
        n = len(sub)
        print(f"{p:>5.1f} | "
              f"{sub['stage1_pass'].mean():>7.0%} | "
              f"{sub['intervention_correct'].mean():>8.0%} | "
              f"{sub['c_collapse'].mean():>8.0%} | "
              f"{sub['e2e_success'].mean():>5.0%}")


def _save_summary_txt(
    df: pd.DataFrame, cfg: dict, output_dir: Path,
    p_values: list[float], feat_names: list[str]
) -> None:
    lines = [
        f"=== {cfg.get('name', 'experiment')} ===",
        cfg.get("description", ""),
        "",
        f"Seeds    : {list(df['seed'].unique())}",
        f"p_values : {p_values}",
        f"n_noise  : {cfg['env']['n_noise']} (total obs dim: {3 + cfg['env']['n_noise']})",
        f"Oracle   : DQN {cfg['oracle']['n_steps']} steps",
        f"Surrogate: MoET K={cfg['surrogate']['n_experts']}, d={cfg['surrogate']['max_depth']}, "
        f"epochs={cfg['surrogate']['distill_epochs']}, n={cfg['surrogate']['n_distill_samples']}",
        "",
        f"{'p':>5} | {'AA>=0.9':>7} | {'detect c':>8} | {'collapse':>8} | {'e2e':>5}",
        "-" * 45,
    ]
    for p in p_values:
        sub = df[df["spurious_p"] == p]
        lines.append(
            f"{p:>5.1f} | "
            f"{sub['stage1_pass'].mean():>7.0%} | "
            f"{sub['intervention_correct'].mean():>8.0%} | "
            f"{sub['c_collapse'].mean():>8.0%} | "
            f"{sub['e2e_success'].mean():>5.0%}"
        )
    lines += ["", "Mean delta_c per p:"]
    for p in p_values:
        sub = df[df["spurious_p"] == p]
        lines.append(f"  p={p}: delta_c={sub['delta_c (spurious)'].mean():.3f}+-{sub['delta_c (spurious)'].std():.3f}")
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"summary.txt -> {output_dir / 'summary.txt'}")


def _plot(df: pd.DataFrame, output_dir: Path, p_values: list[float], feat_names: list[str]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 検出率・崩壊率・e2e を p ごとにまとめる
    ax = axes[0]
    detect  = [df[df["spurious_p"] == p]["intervention_correct"].mean() for p in p_values]
    collapse = [df[df["spurious_p"] == p]["c_collapse"].mean()           for p in p_values]
    e2e     = [df[df["spurious_p"] == p]["e2e_success"].mean()           for p in p_values]
    x = np.arange(len(p_values))
    w = 0.25
    ax.bar(x - w,  detect,   w, label="detect c",  color="steelblue")
    ax.bar(x,      collapse, w, label="Stage 2 collapse", color="tomato")
    ax.bar(x + w,  e2e,      w, label="e2e success", color="seagreen")
    ax.set_xticks(x)
    ax.set_xticklabels([f"p={p}" for p in p_values])
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Rate")
    ax.set_title("Detection / Collapse / End-to-end success rate")
    ax.legend()

    # delta_c per p
    ax = axes[1]
    means = [df[df["spurious_p"] == p]["delta_c (spurious)"].mean() for p in p_values]
    stds  = [df[df["spurious_p"] == p]["delta_c (spurious)"].std()  for p in p_values]
    ax.bar([f"p={p}" for p in p_values], means, yerr=stds, color="tomato", capsize=5)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Mean Δ_c by spurious_p (± SD)")
    ax.set_ylabel("Δ J_S (c)")

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=120)
    plt.close()


if __name__ == "__main__":
    main()
