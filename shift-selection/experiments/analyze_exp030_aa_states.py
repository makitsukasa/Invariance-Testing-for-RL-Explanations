"""exp030 の補足分析：c のシフト下で、2 種類の AA（状態の変換による aa と、ロールアウトの状態による aa_roll）が
大きく食い違う原因を調べる。

exp030 の記録（results.csv）は変更しない。exp029・exp030 と同じ順序でオラクルとサロゲートを再学習し、
exp030 と同じ seed で AA 用の状態を集め直して、状態の中身を分類する。

分類：エージェントが「c が示す角」（_GOALS[c]）にいる状態かどうか。
    c が正しい（c = goal_id）とき、その角は本当のゴールなので、到達した時点でエピソードが終わり、
    観測として残らない。c が誤っているときだけ、その角に着いてもエピソードが続く。

Usage:
    python experiments/analyze_exp030_aa_states.py --seeds 0 1 2 3 --p-values 0.0 0.1 0.2 0.3
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import yaml

from experiments.src.gridworld_env import _GOALS
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement
from experiments.run_shap_psweep import _collect_transitions, _train_oracle
from experiments.run_shift_target_validation import (
    AA_SEED_OFFSET, SEED_OFFSETS, ShiftedGridWorld, _collect_oracle_states, shift_conditions, shift_states,
)

CONFIG = ROOT / "experiments/configs/exp030_shift_target_validation.yaml"
OUT_DIR = ROOT / "experiments/results/exp030_shift_target_validation/supplement_aa_states"
TARGET = ("c__reversed", "c__random")


def _at_c_corner(states: np.ndarray, grid_size: int = 5) -> np.ndarray:
    pos = np.rint(states[:, :2] * (grid_size - 1)).astype(int)
    corner = np.array([_GOALS[int(round(c))] for c in states[:, 2]])
    return np.all(pos == corner, axis=1)


def _agree(model, moet, states: np.ndarray) -> np.ndarray:
    oracle_actions, _ = model.predict(states, deterministic=True)
    return oracle_actions == moet.predict(states)


def _summ(prefix: str, states: np.ndarray, agree: np.ndarray) -> dict:
    corner = _at_c_corner(states)
    return {
        f"{prefix}_aa": float(agree.mean()),
        f"{prefix}_frac_corner": float(corner.mean()),
        f"{prefix}_aa_corner": float(agree[corner].mean()) if corner.any() else np.nan,
        f"{prefix}_aa_other": float(agree[~corner].mean()) if (~corner).any() else np.nan,
    }


def run_one(seed: int, p: float, cfg: dict) -> list[dict]:
    n_noise = cfg["env"]["n_noise"]
    model = _train_oracle(seed, p, n_noise, cfg["oracle"]["n_steps"])
    obs_distill, act_distill = _collect_transitions(model, p, n_noise, seed, cfg["surrogate"]["n_distill_samples"])
    obs_eval, _ = _collect_transitions(model, p, n_noise, seed + 10_000, cfg["evaluation"]["n_eval_samples"])
    moet = SoftMoET(3 + n_noise, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])

    rows = []
    base = {"seed": seed, "spurious_p": p}
    base.update(_summ("train", obs_eval, _agree(model, moet, obs_eval)))
    conds = shift_conditions(n_noise)
    for ci, (cname, feature, kind) in enumerate(conds):
        if cname not in TARGET:
            continue
        aa_seed = seed + SEED_OFFSETS["gt"] + AA_SEED_OFFSET + ci      # exp030 の gt と同じ seed
        env = ShiftedGridWorld(p, n_noise, feature, kind)
        roll = _collect_oracle_states(model, env, aa_seed, cfg["validation"]["n_aa_samples"])
        env.close()
        trans = shift_states(obs_eval, feature, kind, np.random.default_rng(aa_seed))
        row = dict(base, condition=cname)
        a_roll = _agree(model, moet, roll)
        row.update(_summ("roll", roll, a_roll))
        row.update(_summ("trans", trans, _agree(model, moet, trans)))
        # 再現の確認用（exp030 の action_agreement と同じ計算）
        oa, _ = model.predict(roll, deterministic=True)
        row["roll_aa_check"] = action_agreement(roll, oa, moet)
        # c が示す角でのオラクルの行動の内訳（0:上 1:下 2:左 3:右）
        corner = _at_c_corner(roll)
        acts = oa[corner]
        for a in range(4):
            row[f"roll_corner_oracle_act{a}"] = float((acts == a).mean()) if len(acts) else np.nan
        rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--p-values", type=float, nargs="+", default=[0.0, 0.1, 0.2, 0.3])
    ap.add_argument("--n-workers", type=int, default=4)
    args = ap.parse_args()
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    jobs = [(s, p) for p in args.p_values for s in args.seeds]
    with ProcessPoolExecutor(args.n_workers) as ex:
        results = list(ex.map(run_one, *zip(*jobs), [cfg] * len(jobs)))
    df = pd.DataFrame([r for rs in results for r in rs])

    # exp030 の記録と突き合わせる
    ref = pd.read_csv(ROOT / cfg["output_dir"] / "results.csv")
    mism = 0
    for _, r in df.iterrows():
        row = ref[(ref.seed == r.seed) & np.isclose(ref.spurious_p, r.spurious_p)].iloc[0]
        for col, mine in ((f"gt__{r.condition}__aa_roll", r.roll_aa_check), (f"gt__{r.condition}__aa", r.trans_aa)):
            if abs(row[col] - mine) > 1e-9:
                mism += 1
                print(f"[MISMATCH] p={r.spurious_p} seed={r.seed} {col}: exp030={row[col]:.4f} here={mine:.4f}", flush=True)
    print(f"exp030 との一致：{2 * len(df) - mism}/{2 * len(df)}", flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "aa_states.csv", index=False)
    cols = ["train_frac_corner", "roll_aa", "roll_frac_corner", "roll_aa_corner", "roll_aa_other",
            "trans_aa", "trans_frac_corner", "trans_aa_other"] + [f"roll_corner_oracle_act{a}" for a in range(4)]
    with pd.option_context("display.width", 250, "display.max_columns", 50):
        print(df.groupby(["condition", "spurious_p"])[cols].mean().round(3).to_string(), flush=True)


if __name__ == "__main__":
    main()
