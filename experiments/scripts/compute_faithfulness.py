"""exp015: Comprehensiveness faithfulness vs. Invariance 評価の比較。

既存の exp002 (Spurious GridWorld) の oracle model を再利用し、
MoET surrogate に対して Comprehensiveness faithfulness 指標を計算する。

Comprehensiveness（特徴 i に対して）:
    comp_i = AA(全特徴) - AA(特徴 i を平均値でマスクしたとき)

高い comp_i は「surrogate が特徴 i を訓練分布上で忠実に利用している」ことを意味する。
これは訓練分布内での评価であり、依存がスプリアスか因果的かを区別できない。
既存の不変性評価 (reversed_c 下の AA, J_S) と並べることで
「faithfulness だけでは検出できない問題を不変性評価が補う」ことを示す。

使い方:
    .venv/Scripts/python.exe experiments/scripts/compute_faithfulness.py

出力:
    experiments/results/exp015_faithfulness_comparison/faithfulness_results.csv
    experiments/results/exp015_faithfulness_comparison/summary.txt
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from stable_baselines3 import DQN

from experiments.src.gridworld_env import SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

GRIDWORLD_RESULTS = ROOT / "experiments" / "results" / "exp002_spurious_gridworld"
OUTPUT_DIR = ROOT / "experiments" / "results" / "exp015_faithfulness_comparison"

SPURIOUS_P_VALUES = [0.0, 0.2, 0.5]
SEEDS = [42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526]

# 論文の主実験と同一の surrogate 設定
N_EXPERTS = 4
MAX_DEPTH = 5
DISTILL_EPOCHS = 100
DISTILL_N_SAMPLES = 10_000
EVAL_N_SAMPLES = 5_000

N_ACTIONS = 4
INPUT_DIM = 3  # (agent_x, agent_y, c)
FEATURE_NAMES = ["agent_x", "agent_y", "c (spurious)"]
SPURIOUS_FEATURE_IDX = 2  # feature c


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def collect_oracle_data(
    model: DQN,
    spurious_p: float,
    n_samples: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Oracle rollout で (obs, actions) ペアを収集する。"""
    np.random.seed(seed)
    env = SpuriousGridWorld(spurious_p=spurious_p)
    obs_list, action_list = [], []
    obs, _ = env.reset(seed=seed)
    collected = 0
    while collected < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        action_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        collected += 1
        if terminated or truncated:
            obs, _ = env.reset()
    env.close()
    return np.array(obs_list, dtype=np.float32), np.array(action_list, dtype=np.int64)


def compute_comprehensiveness(
    moet: SoftMoET,
    obs_eval: np.ndarray,
    oracle_actions: np.ndarray,
    feature_idx: int,
) -> tuple[float, float, float]:
    """指定特徴の Comprehensiveness を計算する。

    Returns
    -------
    AA_full : float
        全特徴での AA
    AA_masked : float
        feature_idx を平均値でマスクしたときの AA
    comp : float
        AA_full - AA_masked（高いほど特徴 feature_idx への依存が強い）
    """
    AA_full = action_agreement(obs_eval, oracle_actions, moet)
    obs_masked = obs_eval.copy()
    obs_masked[:, feature_idx] = obs_eval[:, feature_idx].mean()
    AA_masked = action_agreement(obs_masked, oracle_actions, moet)
    return AA_full, AA_masked, AA_full - AA_masked


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 既存の不変性評価結果（exp002）を読み込む
    metrics_df = pd.read_csv(GRIDWORLD_RESULTS / "metrics.csv")
    # K=4, d=5 に絞る
    metrics_df = metrics_df[
        (metrics_df["n_experts"] == N_EXPERTS) &
        (metrics_df["max_depth"] == MAX_DEPTH)
    ]

    records = []

    for spurious_p in SPURIOUS_P_VALUES:
        for seed in SEEDS:
            print(f"[p={spurious_p}, seed={seed}] 処理中...", flush=True)

            # Oracle モデルをロード
            model_path = GRIDWORLD_RESULTS / f"intuitive_p{spurious_p}_seed{seed}"
            env = SpuriousGridWorld(spurious_p=spurious_p)
            try:
                model = DQN.load(str(model_path), env=env)
            except Exception as e:
                print(f"  oracle ロード失敗 ({e})、スキップ")
                env.close()
                continue

            # eval_states をロード
            eval_states_path = GRIDWORLD_RESULTS / f"eval_states_p{spurious_p}_seed{seed}.npy"
            if not eval_states_path.exists():
                print(f"  eval_states なし、スキップ")
                env.close()
                continue
            obs_eval = np.load(eval_states_path)[:EVAL_N_SAMPLES]

            # oracle の行動（AA 計算の基準）
            oracle_actions, _ = model.predict(obs_eval, deterministic=True)
            oracle_actions = oracle_actions.astype(np.int64)

            # MoET を蒸留（oracle rollout から）
            obs_distill, actions_distill = collect_oracle_data(
                model, spurious_p, DISTILL_N_SAMPLES, seed
            )
            moet = SoftMoET(INPUT_DIM, N_ACTIONS, N_EXPERTS, MAX_DEPTH)
            moet = distill(moet, obs_distill, actions_distill, epochs=DISTILL_EPOCHS)

            # Comprehensiveness: feature c（スプリアス特徴）
            AA_train, AA_c_masked, comp_c = compute_comprehensiveness(
                moet, obs_eval, oracle_actions, SPURIOUS_FEATURE_IDX
            )
            # Comprehensiveness: position features（ベースライン）
            _, _, comp_x = compute_comprehensiveness(moet, obs_eval, oracle_actions, 0)
            _, _, comp_y = compute_comprehensiveness(moet, obs_eval, oracle_actions, 1)

            # 既存の不変性評価結果を取得（reversed_c 条件）
            inv = metrics_df[
                (metrics_df["spurious_p"] == spurious_p) &
                (metrics_df["seed"] == seed) &
                (metrics_df["eval_condition"] == "reversed_c")
            ]
            AA_reversed = float(inv["action_agreement"].values[0]) if len(inv) else np.nan
            J_reasoned_rev = float(inv["j_reasoned"].values[0]) if len(inv) else np.nan
            J_oracle_rev = float(inv["j_intuitive"].values[0]) if len(inv) else np.nan

            records.append({
                "spurious_p": spurious_p,
                "seed": seed,
                "AA_train": round(AA_train, 4),
                "AA_c_masked": round(AA_c_masked, 4),
                "comp_c": round(comp_c, 4),
                "comp_x": round(comp_x, 4),
                "comp_y": round(comp_y, 4),
                "AA_reversed_c": round(AA_reversed, 4) if not np.isnan(AA_reversed) else np.nan,
                "J_reasoned_reversed": round(J_reasoned_rev, 4) if not np.isnan(J_reasoned_rev) else np.nan,
                "J_oracle_reversed": round(J_oracle_rev, 4) if not np.isnan(J_oracle_rev) else np.nan,
            })

            env.close()

    if not records:
        print("ERROR: 処理できたシードがありません。")
        return

    df = pd.DataFrame(records)
    csv_path = OUTPUT_DIR / "faithfulness_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n結果を保存: {csv_path}")

    _save_summary(df)


def _save_summary(df: pd.DataFrame) -> None:
    lines = [
        "=== Faithfulness（Comprehensiveness）vs. Invariance 比較 ===",
        "",
        "Comprehensiveness（comp_c）: AA(全特徴) - AA(feature c をマスク)",
        "  高い comp_c = surrogate が c に強く依存している（訓練分布内評価）",
        "  ただしこれは依存が spurious か causal かを区別しない",
        "",
        "不変性指標（AA_reversed_c, J 比率）: c を反転したシフト下での評価",
        "  これが低下する = スプリアス依存を検出",
        "",
        f"{'p':>5} | {'AA_train':>9} | {'comp_c':>9} | {'comp_x':>9} | {'comp_y':>9} "
        f"| {'AA_rev_c':>9} | {'J_rev/J_ora':>11}",
        "-" * 80,
    ]

    for sp in [0.0, 0.2, 0.5]:
        sub = df[df["spurious_p"] == sp].dropna(subset=["AA_train"])
        if len(sub) == 0:
            continue

        def fmt(s):
            return f"{s.mean():.3f}±{s.std():.3f}"

        AA_train_s = fmt(sub["AA_train"])
        comp_c_s = fmt(sub["comp_c"])
        comp_x_s = fmt(sub["comp_x"])
        comp_y_s = fmt(sub["comp_y"])
        AA_rev_s = fmt(sub["AA_reversed_c"].dropna()) if sub["AA_reversed_c"].notna().any() else "N/A"

        valid = sub.dropna(subset=["J_reasoned_reversed", "J_oracle_reversed"])
        if len(valid) > 0:
            oracle_abs = valid["J_oracle_reversed"].abs()
            nonzero = oracle_abs > 0.01
            if nonzero.any():
                j_ratio = (valid.loc[nonzero, "J_reasoned_reversed"] /
                           valid.loc[nonzero, "J_oracle_reversed"].abs())
                J_ratio_s = f"{j_ratio.mean():.1%}±{j_ratio.std():.1%}"
            else:
                J_ratio_s = "N/A"
        else:
            J_ratio_s = "N/A"

        lines.append(
            f"{sp:>5.1f} | {AA_train_s:>9} | {comp_c_s:>9} | {comp_x_s:>9} | {comp_y_s:>9} "
            f"| {AA_rev_s:>9} | {J_ratio_s:>11}"
        )

    lines += [
        "",
        "解釈:",
        "  p=0.0: comp_c が高い → surrogate は c に強く依存（faithfulness は高い）",
        "         AA_reversed_c が低い・J_rev/J_ora が低い → 不変性評価でスプリアス依存を検出",
        "  p=0.5: comp_c が低い → oracle が c を無視 → surrogate も c をほぼ使わない",
        "         AA_reversed_c が維持 → 不変性評価でも問題なし",
        "",
        "結論: Comprehensiveness は訓練分布内での利用度を測るが、",
        "      その依存が分布シフト下で有効かどうかは判定できない。",
        "      本枠組みの不変性評価はこの gap を補完する。",
    ]

    summary_text = "\n".join(lines)
    path = OUTPUT_DIR / "summary.txt"
    path.write_text(summary_text, encoding="utf-8")
    print(f"\n{summary_text}")
    print(f"\nサマリーを保存: {path}")


if __name__ == "__main__":
    main()
