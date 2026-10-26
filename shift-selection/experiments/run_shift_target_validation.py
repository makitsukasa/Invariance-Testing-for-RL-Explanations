"""exp030: 選定と評価を独立させた、シフト対象の選定の検証。

設計：experiments/plans/exp030_shift_target_validation.md

exp029 と同じ 120 run のオラクル（DQN）とサロゲート（SoftMoET）を同じ順序で再学習し、
10 特徴すべてに環境側の分布シフト（各 2 種類）を適用して評価する。どの選定法（Δ・SHAP・
ランダム）が何を選んだかはこのスクリプトでは使わない。選定は exp029 の results.csv に
記録済みで、compute_stats_shift_target.py で突き合わせる。

評価は 2 組の seed で行う。
    gt : 正解の評価。エピソードの seed は seed + 100,000 + エピソード番号（500 エピソード）
    pl : 手順用の再テスト。seed + 200,000 + エピソード番号（200 エピソード）
同じ組の中では、シフトなしを含む全条件で同じエピソードの seed を使う（共通乱数）。
Δ・SHAP の乱数（seed + 30,000、seed + 40,000 + 特徴番号 × 1,000 + エピソード番号）とは重ならない。

各条件で、サロゲートの平均リターン J_S、オラクルの平均リターン J_O（同じエピソード seed）、
行動一致率 AA を記録する。AA は論文A（experiments/run_gridworld.py の eval_states_for_condition）と
同じく、訓練分布の評価状態（AA(train) と同じ 2,000 状態）にシフトを状態の変換として適用して測る。
開始位置のシフトは状態の変換として書けないので、シフトした環境でオラクルを走らせて集めた状態で測る。
補助として、全条件でロールアウトの状態での一致率（aa_roll）も記録する。

Usage:
    python experiments/run_shift_target_validation.py --config experiments/configs/exp030_shift_target_validation.yaml
    python experiments/run_shift_target_validation.py --config ... --seeds 0 --p-values 0.0 --output-dir <dir>
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import gymnasium as gym
import numpy as np
import pandas as pd
import yaml

from experiments.src.gridworld_env import _GOALS, SpuriousGridWorld
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill
from experiments.src.evaluate import action_agreement, evaluate_rollout
from experiments.run_shap_psweep import _collect_transitions, _feature_names, _train_oracle

SEED_OFFSETS = {"gt": 100_000, "pl": 200_000}
AA_SEED_OFFSET = 700          # 条件内で、AA 用の状態収集に使う reset の seed（エピソードの seed とは重ならない）
REPRO_COLS = ("aa_train", "j_s_train", "j_oracle_train")


# --- シフト条件 -----------------------------------------------------------------

def shift_conditions(n_noise: int) -> list[tuple[str, int | None, str]]:
    """(条件名, 特徴番号, シフトの種類)。番号 0 はシフトなし。以降は特徴ごとに 2 種類。"""
    names = _feature_names(n_noise)
    short = ["agent_x", "agent_y", "c"] + [f"noise_{i}" for i in range(n_noise)]
    kinds = {0: ("start_lo", "start_hi"), 1: ("start_lo", "start_hi"), 2: ("reversed", "random")}
    conds: list[tuple[str, int | None, str]] = [("none", None, "none")]
    for k in range(len(names)):
        for kind in kinds.get(k, ("low", "high")):
            conds.append((f"{short[k]}__{kind}", k, kind))
    return conds


class ShiftedGridWorld(SpuriousGridWorld):
    """SpuriousGridWorld の 1 特徴だけにデータ生成側の分布シフトを入れる。

    c        : reversed（c = 1 - goal_id）/ random（c ~ Bernoulli(0.5)）。親の eval_mode をそのまま使う
    noise_i  : low（U(0, 0.5)）/ high（U(0.5, 1)）。他の noise は U(0, 1) のまま
    agent_x/y: start_lo（開始位置のその座標を {0, 1} に限る）/ start_hi（{3, 4} に限る）
    観測値を毎ステップ書き換える Δ の置換とは異なり、観測は常に環境の状態と一致する。
    """

    def __init__(self, spurious_p: float, n_noise: int, feature: int | None, kind: str):
        eval_mode = kind if feature == 2 else None
        super().__init__(spurious_p=spurious_p, n_noise=n_noise, eval_mode=eval_mode)
        self.feature = feature
        self.kind = kind

    def _obs(self) -> np.ndarray:
        obs = super()._obs()
        if self.feature is not None and self.feature >= 3:
            u = obs[self.feature]                     # 親と同じ乱数の消費で U(0,1) を引き、写像する
            obs[self.feature] = 0.5 * u if self.kind == "low" else 0.5 + 0.5 * u
        return obs

    def _start_ok(self, ax: int, ay: int) -> bool:
        if self.feature not in (0, 1):
            return True
        v = ax if self.feature == 0 else ay
        return v <= 1 if self.kind == "start_lo" else v >= self.grid_size - 2

    def reset(self, *, seed=None, options=None):
        if self.feature not in (0, 1):
            return super().reset(seed=seed, options=options)
        gym.Env.reset(self, seed=seed)
        if seed is not None:
            np.random.seed(seed)
        self._goal_id = int(np.random.randint(0, len(_GOALS)))
        self._goal_pos = _GOALS[self._goal_id]
        self._c = self._make_c(self._goal_id)
        while True:
            ax = int(np.random.randint(0, self.grid_size))
            ay = int(np.random.randint(0, self.grid_size))
            if (ax, ay) != self._goal_pos and self._start_ok(ax, ay):
                break
        self._agent_pos = (ax, ay)
        self._steps = 0
        return self._obs(), {}


def _collect_oracle_states(model, env: gym.Env, seed: int, n_samples: int) -> np.ndarray:
    obs_list = []
    obs, _ = env.reset(seed=seed)
    while len(obs_list) < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        obs, _, terminated, truncated, _ = env.step(int(action))
        if terminated or truncated:
            obs, _ = env.reset()
    return np.array(obs_list, dtype=np.float32)


def shift_states(obs: np.ndarray, feature: int | None, kind: str, rng: np.random.Generator) -> np.ndarray | None:
    """訓練分布の状態に、その条件のシフトを状態の変換として適用する（論文A の eval_states_for_condition と同じ考え方）。

    開始位置のシフトは状態の変換として書けないので None を返す（その場合はロールアウトの状態を使う）。
    """
    out = obs.copy()
    if feature is None:
        return out
    if feature == 2:
        out[:, 2] = 1.0 - out[:, 2] if kind == "reversed" else rng.integers(0, 2, len(out)).astype(np.float32)
        return out
    if feature >= 3:
        out[:, feature] = 0.5 * out[:, feature] if kind == "low" else 0.5 + 0.5 * out[:, feature]
        return out
    return None


def _aa(model, moet, states: np.ndarray) -> float:
    oracle_actions, _ = model.predict(states, deterministic=True)
    return action_agreement(states, oracle_actions, moet)


def evaluate_condition(model, moet, spurious_p, n_noise, feature, kind, obs_train: np.ndarray,
                       ep_seed: int, aa_seed: int, n_episodes: int, n_aa: int) -> dict[str, float]:
    """ep_seed は条件によらず同じ値を渡す（共通乱数）。シフトした特徴以外のエピソードの乱数は条件間で揃う。"""
    env = ShiftedGridWorld(spurious_p, n_noise, feature, kind)
    j_s = evaluate_rollout(moet, env, n_episodes, ep_seed)
    j_o = evaluate_rollout(model, env, n_episodes, ep_seed)
    roll_states = _collect_oracle_states(model, env, aa_seed, n_aa)
    env.close()
    aa_roll = _aa(model, moet, roll_states)
    shifted = shift_states(obs_train, feature, kind, np.random.default_rng(aa_seed))
    aa = aa_roll if shifted is None else _aa(model, moet, shifted)
    return {"js": j_s, "jo": j_o, "aa": aa, "aa_roll": aa_roll}


# --- 1 run --------------------------------------------------------------------

def run_one_seed(seed: int, spurious_p: float, cfg: dict) -> tuple[dict, list[str]]:
    logs: list[str] = [f"\n{'='*60}", f"Seed {seed}  (spurious_p={spurious_p})", f"{'='*60}"]
    t0 = time.perf_counter()
    times: dict[str, float] = {}

    def lap(name: str) -> None:
        times[f"time_{name}"] = time.perf_counter() - t0 - sum(times.values())

    n_noise   = cfg["env"]["n_noise"]
    n_obs     = 3 + n_noise
    n_distill = cfg["surrogate"]["n_distill_samples"]
    n_eval    = cfg["evaluation"]["n_eval_samples"]
    ev        = cfg["validation"]

    # --- exp029（= exp016）と同じ順序で学習する ----------------------------------
    model = _train_oracle(seed, spurious_p, n_noise, cfg["oracle"]["n_steps"])
    lap("oracle_train")

    obs_distill, act_distill = _collect_transitions(model, spurious_p, n_noise, seed,          n_distill)
    obs_eval, _              = _collect_transitions(model, spurious_p, n_noise, seed + 10_000, n_eval)

    moet = SoftMoET(n_obs, 4, cfg["surrogate"]["n_experts"], cfg["surrogate"]["max_depth"])
    moet = distill(moet, obs_distill, act_distill, epochs=cfg["surrogate"]["distill_epochs"])
    lap("surrogate_train")

    # 再現の確認用（exp029 と同じ計算）
    n_train_ep = cfg["evaluation"]["n_eval_episodes"]
    oracle_actions, _ = model.predict(obs_eval, deterministic=True)
    aa_train = action_agreement(obs_eval, oracle_actions, moet)
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_s_train = evaluate_rollout(moet, env, n_train_ep, seed + 20_000)
    env.close()
    env = SpuriousGridWorld(spurious_p=spurious_p, n_noise=n_noise)
    j_oracle_train = evaluate_rollout(model, env, n_train_ep, seed + 20_000)
    env.close()
    lap("repro")

    result: dict = {"seed": seed, "spurious_p": spurious_p, "aa_train": aa_train,
                    "j_s_train": j_s_train, "j_oracle_train": j_oracle_train}

    # --- 評価 --------------------------------------------------------------------
    conds = shift_conditions(n_noise)
    for set_name, offset in SEED_OFFSETS.items():
        n_ep = ev[f"n_episodes_{set_name}"]
        for ci, (cname, feature, kind) in enumerate(conds):
            vals = evaluate_condition(model, moet, spurious_p, n_noise, feature, kind, obs_eval,
                                      seed + offset, seed + offset + AA_SEED_OFFSET + ci,
                                      n_ep, ev["n_aa_samples"])
            for m, v in vals.items():
                result[f"{set_name}__{cname}__{m}"] = v
        lap(f"eval_{set_name}")

    result.update(times)
    result["time_total"] = time.perf_counter() - t0

    logs.append(f"  AA={aa_train:.3f}, J_S_train={j_s_train:.3f}, J_oracle_train={j_oracle_train:.3f}")
    base = result["gt__none__js"]
    for cname, _, _ in conds:
        js, jo, aa = (result[f"gt__{cname}__{m}"] for m in ("js", "jo", "aa"))
        logs.append(f"  {cname:<20} J_S={js:+.3f} (ratio {js / base if base > 0 else float('nan'):+.2f})  "
                    f"J_O={jo:+.3f}  AA={aa:.3f}")
    logs.append("  time: " + ", ".join(f"{k[5:]}={v:.0f}s" for k, v in times.items()))
    return result, logs


def _check_repro(rec: dict, ref: pd.DataFrame | None) -> str | None:
    if ref is None:
        return None
    row = ref[(ref["seed"] == rec["seed"]) & (np.isclose(ref["spurious_p"], rec["spurious_p"]))]
    if len(row) != 1:
        return f"exp029 に p={rec['spurious_p']} seed={rec['seed']} の行がない"
    diffs = {c: abs(float(row[c].iloc[0]) - rec[c]) for c in REPRO_COLS}
    bad = {c: d for c, d in diffs.items() if d > 1e-9}
    return f"exp029 と一致しない: {bad}" if bad else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument("--p-values", type=float, nargs="+")
    parser.add_argument("--output-dir")
    parser.add_argument("--n-workers", type=int)
    parser.add_argument("--n-episodes-gt", type=int, help="動作確認用に正解の評価のエピソード数を上書きする")
    parser.add_argument("--n-episodes-pl", type=int, help="動作確認用に手順用の再テストのエピソード数を上書きする")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.n_episodes_gt:
        cfg["validation"]["n_episodes_gt"] = args.n_episodes_gt
    if args.n_episodes_pl:
        cfg["validation"]["n_episodes_pl"] = args.n_episodes_pl

    output_dir = Path(args.output_dir) if args.output_dir else ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds     = args.seeds or cfg["evaluation"]["seeds"]
    p_values  = args.p_values or cfg["env"]["p_values"]
    n_workers = args.n_workers or cfg.get("n_workers", 4)
    ref_path  = ROOT / cfg["validation"]["exp029_results"]
    ref = pd.read_csv(ref_path) if ref_path.exists() else None

    print(f"Experiment : {cfg['name']}", flush=True)
    print(f"Seeds      : {seeds}", flush=True)
    print(f"p_values   : {p_values}", flush=True)
    print(f"n_workers  : {n_workers}", flush=True)
    print(f"episodes   : gt={cfg['validation']['n_episodes_gt']}, pl={cfg['validation']['n_episodes_pl']}", flush=True)
    print(f"exp029     : {ref_path if ref is not None else 'なし（再現の確認をしない）'}", flush=True)

    records: dict = {}
    seed_logs: dict = {}
    t_start = time.perf_counter()

    tasks = [(s, p) for p in p_values for s in seeds]
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(run_one_seed, s, p, cfg): (s, p) for s, p in tasks}
        for future in as_completed(futures):
            key = futures[future]
            rec, logs = future.result()
            problem = _check_repro(rec, ref)
            rec["repro_ok"] = problem is None
            records[key] = rec
            seed_logs[key] = logs
            print(f"[DONE {len(records)}/{len(tasks)} {time.perf_counter() - t_start:.0f}s] "
                  f"p={rec['spurious_p']}, seed={rec['seed']}: AA={rec['aa_train']:.3f} "
                  f"repro={'OK' if problem is None else 'NG'} ({rec['time_total']:.0f}s)", flush=True)
            pd.DataFrame(list(records.values())).sort_values(["spurious_p", "seed"]).to_csv(
                output_dir / "results_partial.csv", index=False)
            if problem is not None:
                print(f"[STOP] p={rec['spurious_p']}, seed={rec['seed']}: {problem}", flush=True)
                executor.shutdown(wait=False, cancel_futures=True)
                sys.exit(1)

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
