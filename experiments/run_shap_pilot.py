"""SHAP-based shift auto-selection — pilot experiment on SpuriousGridWorld.

Pipeline:
  1. Oracle (DQN) を訓練
  2. SHAP で特徴重要度を計算 → 特徴をランク付け
  3. 上位特徴をシフト候補として自動選択
  4. MoET surrogate を Oracle に蒸留
  5. Stage 1 (train): AA >= 0.9 を確認
  6. Stage 2 (auto-selected shift): J_S 崩壊を確認

確認したい問い:
  Q1. SHAP は c (spurious feature, index=2) を上位に出すか？
  Q2. SHAP が選んだ特徴をシフトしたとき、Stage 2 で崩壊を検出できるか？
  Q3. 非スプリアス特徴（x, y）をシフトしたとき、崩壊しないか（対照）？

Usage:
  python experiments/run_shap_pilot.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import shap
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import DQN

from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SPURIOUS_P = 0.0
N_ORACLE_STEPS = 50_000
N_DISTILL_SAMPLES = 10_000
N_EVAL_SAMPLES = 2_000
N_EVAL_EPISODES = 100
N_EXPERTS = 4
MAX_DEPTH = 3
DISTILL_EPOCHS = 100
SHAP_BG = 100
SHAP_EVAL = 300

SEEDS = [42, 123, 456, 789, 0]

FEATURE_NAMES = ["agent_x", "agent_y", "c (spurious)"]
SPURIOUS_IDX = 2

OUTPUT_DIR = ROOT / "experiments" / "results" / "pilot_shap_gridworld"

# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

def train_oracle(seed: int) -> DQN:
    env = SpuriousGridWorld(spurious_p=SPURIOUS_P)
    model = DQN("MlpPolicy", env, seed=seed, verbose=0, learning_starts=1000)
    model.learn(total_timesteps=N_ORACLE_STEPS)
    env.close()
    return model


def collect_transitions(model: DQN, seed: int, n_samples: int) -> tuple[np.ndarray, np.ndarray]:
    env = SpuriousGridWorld(spurious_p=SPURIOUS_P)
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
# SHAP
# ---------------------------------------------------------------------------

def compute_shap_ranking(model: DQN, obs: np.ndarray) -> tuple[list[int], np.ndarray]:
    """SHAP で特徴重要度を計算し、降順インデックスリストと平均 |SHAP| を返す。

    Oracle の Q 値（全行動分）を出力関数として使い、行動間で |SHAP| を平均する。
    """
    def q_fn(x: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            return model.q_net(torch.FloatTensor(x)).numpy()

    n_features = obs.shape[1]
    bg = obs[:SHAP_BG]
    test = obs[:SHAP_EVAL]
    explainer = shap.KernelExplainer(q_fn, bg)
    shap_vals = explainer.shap_values(test, nsamples=100, silent=True)

    if isinstance(shap_vals, list):
        # list of arrays, one per output: each (n_samples, n_features)
        stacked = np.stack([np.abs(np.array(sv, dtype=float)) for sv in shap_vals])
        mean_abs = stacked.mean(axis=(0, 1))  # (n_features,)
    else:
        arr = np.abs(np.array(shap_vals, dtype=float))
        # 特徴次元（== n_features）を探して、それ以外の軸で平均する
        feat_axes = [i for i, s in enumerate(arr.shape) if s == n_features]
        if feat_axes:
            feat_axis = feat_axes[-1]  # 複数マッチする場合は末尾を使う
            other_axes = tuple(i for i in range(arr.ndim) if i != feat_axis)
            mean_abs = arr.mean(axis=other_axes)
        else:
            mean_abs = arr.reshape(-1, n_features).mean(axis=0)

    mean_abs = mean_abs.flatten()[:n_features]
    ranking = list(np.argsort(mean_abs)[::-1])
    return ranking, mean_abs

# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def perturb_obs(obs: np.ndarray, feature_idx: int, mode: str) -> np.ndarray:
    """指定特徴を perturb した obs を返す。

    mode:
      "reversed" : 二値特徴を反転 (1 - x)
      "random"   : 一様ランダムで置き換え
    """
    out = obs.copy()
    if mode == "reversed":
        out[:, feature_idx] = 1.0 - out[:, feature_idx]
    elif mode == "random":
        out[:, feature_idx] = np.random.uniform(
            obs[:, feature_idx].min(), obs[:, feature_idx].max(), len(obs)
        ).astype(np.float32)
    return out


def eval_condition(
    model: DQN,
    surrogate: SoftMoET,
    obs_base: np.ndarray,
    feature_idx: int,
    perturb_mode: str,
    seed: int,
) -> dict:
    """静的観測を perturb して AA を計算し、ロールアウト環境で J を計算する。

    c (index=2) のシフトは environment の eval_mode で再現できるが、
    x/y のシフトは環境が直接サポートしないので静的 perturb で AA のみ計算する。
    """
    obs_p = perturb_obs(obs_base, feature_idx, perturb_mode)
    oracle_actions, _ = model.predict(obs_p, deterministic=True)
    aa = action_agreement(obs_p, oracle_actions, surrogate)

    # ロールアウト: c シフトは environment の eval_mode を使う（正確な J）
    # x/y シフトは環境がサポートしないため J を NaN にする
    if feature_idx == SPURIOUS_IDX:
        env_mode = "reversed" if perturb_mode == "reversed" else "random"
        oracle_env = SpuriousGridWorld(spurious_p=SPURIOUS_P, eval_mode=env_mode)
        j_oracle = evaluate_rollout(model, oracle_env, N_EVAL_EPISODES, seed)
        oracle_env.close()
        surr_env = SpuriousGridWorld(spurious_p=SPURIOUS_P, eval_mode=env_mode)
        j_s = evaluate_rollout(surrogate, surr_env, N_EVAL_EPISODES, seed)
        surr_env.close()
    else:
        j_oracle = float("nan")
        j_s = float("nan")

    return {"aa": aa, "j_oracle": j_oracle, "j_s": j_s}

# ---------------------------------------------------------------------------
# Single-seed pipeline
# ---------------------------------------------------------------------------

def run_one_seed(seed: int) -> dict:
    print(f"\n{'='*60}\nSeed {seed}\n{'='*60}")

    print("  [1/5] Oracle training...")
    model = train_oracle(seed)

    print("  [2/5] Data collection...")
    obs_distill, act_distill = collect_transitions(model, seed, N_DISTILL_SAMPLES)
    obs_eval, _ = collect_transitions(model, seed + 10_000, N_EVAL_SAMPLES)

    print(f"  [3/5] SHAP analysis (bg={SHAP_BG}, eval={SHAP_EVAL}, nsamples=100)...")
    ranking, mean_abs = compute_shap_ranking(model, obs_eval)
    top_idx = ranking[0]
    shap_correct = (top_idx == SPURIOUS_IDX)
    print(f"    Ranking: {[FEATURE_NAMES[i] for i in ranking]}")
    print(f"    Mean |SHAP|: " + ", ".join(f"{FEATURE_NAMES[i]}={mean_abs[i]:.4f}" for i in range(3)))
    print(f"    Auto-selected: {FEATURE_NAMES[top_idx]} → {'CORRECT (c)' if shap_correct else 'WRONG'}")

    print("  [4/5] Surrogate training (MoET)...")
    moet = SoftMoET(3, 4, N_EXPERTS, MAX_DEPTH)
    moet = distill(moet, obs_distill, act_distill, epochs=DISTILL_EPOCHS)

    # Stage 1 (train)
    oracle_actions_train, _ = model.predict(obs_eval, deterministic=True)
    aa_train = action_agreement(obs_eval, oracle_actions_train, moet)
    train_env = SpuriousGridWorld(spurious_p=SPURIOUS_P)
    j_oracle_train = evaluate_rollout(model, train_env, N_EVAL_EPISODES, seed + 20_000)
    j_s_train = evaluate_rollout(moet, train_env, N_EVAL_EPISODES, seed + 20_000)
    train_env.close()
    stage1_pass = aa_train >= 0.9
    print(f"  [5/5] Stage 1: AA={aa_train:.3f} ({'PASS' if stage1_pass else 'FAIL'}), "
          f"J_oracle={j_oracle_train:.3f}, J_S={j_s_train:.3f}")

    # Stage 2: c reversed（スプリアス依存の検出）
    res_c = eval_condition(model, moet, obs_eval, SPURIOUS_IDX, "reversed", seed + 30_000)
    c_collapse = j_s_train > 0 and res_c["j_s"] < 0.5 * j_s_train
    print(f"    Stage 2 (c reversed):  AA={res_c['aa']:.3f}, "
          f"J_oracle={res_c['j_oracle']:.3f}, J_S={res_c['j_s']:.3f} "
          f"→ {'COLLAPSE DETECTED' if c_collapse else 'no collapse'}")

    # 対照: x, y をシフト（非スプリアス → 崩壊しないはず）
    res_x = eval_condition(model, moet, obs_eval, 0, "random", seed + 40_000)
    res_y = eval_condition(model, moet, obs_eval, 1, "random", seed + 50_000)
    print(f"    Control (x random):    AA={res_x['aa']:.3f}")
    print(f"    Control (y random):    AA={res_y['aa']:.3f}")

    return {
        "seed": seed,
        # SHAP
        "shap_rank_1st": FEATURE_NAMES[ranking[0]],
        "shap_rank_2nd": FEATURE_NAMES[ranking[1]],
        "shap_rank_3rd": FEATURE_NAMES[ranking[2]],
        "shap_c": float(mean_abs[SPURIOUS_IDX]),
        "shap_x": float(mean_abs[0]),
        "shap_y": float(mean_abs[1]),
        "shap_correct": shap_correct,
        # Stage 1
        "aa_train": aa_train,
        "stage1_pass": stage1_pass,
        "j_oracle_train": j_oracle_train,
        "j_s_train": j_s_train,
        # Stage 2 (c reversed)
        "aa_c_reversed": res_c["aa"],
        "j_oracle_c_reversed": res_c["j_oracle"],
        "j_s_c_reversed": res_c["j_s"],
        "c_collapse": c_collapse,
        # Control
        "aa_x_random": res_x["aa"],
        "aa_y_random": res_y["aa"],
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    for seed in SEEDS:
        rec = run_one_seed(seed)
        records.append(rec)

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_DIR / "results.csv", index=False)

    _print_summary(df)
    _save_summary_txt(df)
    _plot(df)
    print(f"\nResults: {OUTPUT_DIR}")


def _print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    n = len(df)
    print(f"Q1. SHAP correctly ranked c as top feature:  "
          f"{df['shap_correct'].mean():.0%}  ({df['shap_correct'].sum()}/{n} seeds)")
    print(f"    Mean |SHAP|: x={df['shap_x'].mean():.4f}, y={df['shap_y'].mean():.4f}, c={df['shap_c'].mean():.4f}")
    print(f"Q2. Stage 2 collapse detected (c reversed):  "
          f"{df['c_collapse'].mean():.0%}  ({df['c_collapse'].sum()}/{n} seeds)")
    print(f"    Mean J_S train={df['j_s_train'].mean():.3f}, reversed={df['j_s_c_reversed'].mean():.3f}")
    print(f"Q3. AA after x/y shift (should stay high):  "
          f"AA_x={df['aa_x_random'].mean():.3f}, AA_y={df['aa_y_random'].mean():.3f}")
    print(f"\nStage 1 pass rate: {df['stage1_pass'].mean():.0%}")


def _save_summary_txt(df: pd.DataFrame) -> None:
    lines = [
        "=== Pilot: SHAP-based shift auto-selection on SpuriousGridWorld ===",
        "",
        f"Seeds tested: {list(df['seed'])}",
        "",
        f"Q1. SHAP correctly identified c as top feature: {df['shap_correct'].mean():.0%}",
        f"    Mean |SHAP|: x={df['shap_x'].mean():.4f} ± {df['shap_x'].std():.4f}",
        f"               y={df['shap_y'].mean():.4f} ± {df['shap_y'].std():.4f}",
        f"               c={df['shap_c'].mean():.4f} ± {df['shap_c'].std():.4f}",
        "",
        f"Q2. Collapse detected after c reversed: {df['c_collapse'].mean():.0%}",
        f"    J_S train={df['j_s_train'].mean():.3f} ± {df['j_s_train'].std():.3f}",
        f"    J_S reversed={df['j_s_c_reversed'].mean():.3f} ± {df['j_s_c_reversed'].std():.3f}",
        "",
        f"Q3. AA after non-spurious shift (control):",
        f"    AA_x_random={df['aa_x_random'].mean():.3f} ± {df['aa_x_random'].std():.3f}",
        f"    AA_y_random={df['aa_y_random'].mean():.3f} ± {df['aa_y_random'].std():.3f}",
        "",
        "Per-seed:",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"  seed={int(row['seed'])}: "
            f"SHAP_1st={row['shap_rank_1st']}, "
            f"AA_train={row['aa_train']:.3f}, "
            f"J_S_train={row['j_s_train']:.3f}, "
            f"J_S_reversed={row['j_s_c_reversed']:.3f}, "
            f"collapse={row['c_collapse']}"
        )
    (OUTPUT_DIR / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"Summary saved: {OUTPUT_DIR / 'summary.txt'}")


def _plot(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # SHAP importance
    ax = axes[0]
    feats = ["agent_x", "agent_y", "c (spurious)"]
    means = [df["shap_x"].mean(), df["shap_y"].mean(), df["shap_c"].mean()]
    stds  = [df["shap_x"].std(),  df["shap_y"].std(),  df["shap_c"].std()]
    colors = ["steelblue", "steelblue", "tomato"]
    ax.bar(feats, means, yerr=stds, color=colors, capsize=5)
    ax.set_title("SHAP importance (mean ± SD across seeds)")
    ax.set_ylabel("Mean |SHAP|")

    # J_S comparison
    ax = axes[1]
    x = np.arange(len(df))
    w = 0.35
    ax.bar(x - w/2, df["j_s_train"],      w, label="train",      color="steelblue")
    ax.bar(x + w/2, df["j_s_c_reversed"], w, label="c reversed",  color="tomato")
    ax.set_xticks(x)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("J_S: train vs c-reversed")
    ax.set_ylabel("Mean episode reward")
    ax.legend()

    # AA comparison
    ax = axes[2]
    ax.bar(x - w/2, df["aa_train"],      w, label="train",      color="steelblue")
    ax.bar(x + w/2, df["aa_c_reversed"], w, label="c reversed",  color="tomato")
    ax.axhline(0.9, color="black", linestyle="--", linewidth=1, label="AA=0.9")
    ax.set_xticks(x)
    ax.set_xticklabels([f"s={int(s)}" for s in df["seed"]], rotation=30, fontsize=8)
    ax.set_title("Action Agreement: train vs c-reversed")
    ax.set_ylabel("AA")
    ax.set_ylim(0, 1.1)
    ax.legend()

    plt.tight_layout()
    path = OUTPUT_DIR / "pilot_results.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"Plot saved: {path}")


if __name__ == "__main__":
    main()
