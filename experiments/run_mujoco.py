"""実験7: MuJoCo/LunarLander 予備実験（連続制御への枠組み拡張）。

(c) LunarLander-v3: 離散行動・連続力学。重力シフトで分布シフト。
(a) MuJoCo Hopper-v5: 連続行動を 3^3=27 クラスにビニング。重力シフト。

使い方:
    python experiments/run.py --config experiments/configs/exp007_mujoco_preliminary.yaml
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stable_baselines3 import DQN, PPO, SAC, TD3
from stable_baselines3.common.env_util import make_vec_env

from experiments.src.evaluate import action_agreement, relative_perf_drop
from experiments.src.baselines import (
    LinearReasonedModel, SingleTreeReasonedModel, GBTReasonedModel,
    EBMReasonedModel, SoftDecisionTreeReasonedModel, SymbolicReasonedModel,
    EBMRegressionReasonedModel, SoftDecisionTreeRegressionReasonedModel, SymbolicRegressionReasonedModel,
    RegressionTreeModel, RegressionLinearModel, GBTRegressionReasonedModel,
)
from experiments.src.moet import SoftMoET
from experiments.src.distill import distill

MODEL_LABEL = {
    "moet": "MoET", "linear": "Linear", "tree": "Tree", "gbt": "GBT",
    "dt_viper": "DT-VIPER", "ebm": "EBM", "sdt": "SoftTree", "symbolic": "Symbolic",
    "reg_tree": "RegTree", "reg_linear": "RegLinear", "reg_ebm": "RegEBM",
    "reg_sdt": "RegSoftTree", "reg_symbolic": "RegSymbolic", "reg_gbt": "RegGBT",
}
COLORS = {
    "moet": "steelblue", "linear": "tomato", "tree": "seagreen", "gbt": "darkorange",
    "dt_viper": "forestgreen", "ebm": "royalblue", "sdt": "mediumpurple", "symbolic": "sienna",
    "reg_tree": "darkgreen", "reg_linear": "darkorchid", "reg_ebm": "cornflowerblue",
    "reg_sdt": "plum", "reg_symbolic": "peru", "reg_gbt": "darkorange",
}


def make_model(model_type: str, input_dim: int, n_actions: int, comp_cfg: dict):
    if model_type == "moet":
        return SoftMoET(input_dim, n_actions, comp_cfg["moet"]["n_experts"], comp_cfg["moet"]["max_depth"])
    elif model_type == "linear":
        return LinearReasonedModel(input_dim, n_actions)
    elif model_type == "tree":
        return SingleTreeReasonedModel(input_dim, n_actions, comp_cfg["tree"]["max_depth"])
    elif model_type == "gbt":
        gbt_cfg = comp_cfg.get("gbt", {})
        return GBTReasonedModel(
            input_dim, n_actions,
            max_iter=gbt_cfg.get("max_iter", 200),
            max_depth=gbt_cfg.get("max_depth", None),
            learning_rate=gbt_cfg.get("learning_rate", 0.1),
        )
    elif model_type in ("dt_viper", "tree_viper"):
        tree_cfg = comp_cfg.get("dt_viper", {})
        return SingleTreeReasonedModel(
            input_dim, n_actions, max_depth=tree_cfg.get("max_depth", 20)
        )
    elif model_type == "ebm":
        ebm_cfg = comp_cfg.get("ebm", {})
        return EBMReasonedModel(
            input_dim, n_actions,
            max_rounds=ebm_cfg.get("max_rounds", 300),
            outer_bags=ebm_cfg.get("outer_bags", 8),
            interactions=ebm_cfg.get("interactions", 0),
        )
    elif model_type == "sdt":
        sdt_cfg = comp_cfg.get("sdt", {})
        return SoftDecisionTreeReasonedModel(
            input_dim, n_actions,
            depth=sdt_cfg.get("depth", 5),
            epochs=sdt_cfg.get("epochs", 150),
            lr=sdt_cfg.get("lr", 1e-3),
            batch_size=sdt_cfg.get("batch_size", 512),
            entropy_coef=sdt_cfg.get("entropy_coef", 1e-3),
            seed=sdt_cfg.get("seed", 42),
        )
    elif model_type == "symbolic":
        sym_cfg = comp_cfg.get("symbolic", {})
        return SymbolicReasonedModel(
            input_dim, n_actions,
            population_size=sym_cfg.get("population_size", 1200),
            generations=sym_cfg.get("generations", 25),
            tournament_size=sym_cfg.get("tournament_size", 20),
            parsimony_coefficient=sym_cfg.get("parsimony_coefficient", 0.001),
            random_state=sym_cfg.get("random_state", 42),
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def fit_model(model, obs: np.ndarray, actions: np.ndarray, comp_cfg: dict):
    if isinstance(model, SoftMoET):
        return distill(model, obs, actions, epochs=comp_cfg["distill_epochs"])
    else:
        return model.fit(obs, actions)


def _kl_empirical(acts1: np.ndarray, acts2: np.ndarray, n_actions: int) -> float:
    """経験的行動分布間の KL(P1 || P2) を返す。"""
    eps = 1e-8
    p = np.bincount(acts1.astype(int), minlength=n_actions).astype(float)
    q = np.bincount(acts2.astype(int), minlength=n_actions).astype(float)
    p = (p + eps) / (p + eps).sum()
    q = (q + eps) / (q + eps).sum()
    return float(np.sum(p * np.log(p / q)))


# ---------------------------------------------------------------------------
# LunarLander
# ---------------------------------------------------------------------------

def run_lunarlander(cfg: dict, output_dir: Path) -> pd.DataFrame:
    from experiments.src.lunar_env import (
        make_env as make_lunar,
        collect_transitions as collect_lunar,
        evaluate_intuitive as eval_lunar_intuitive,
    )

    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_eval: int = cfg["evaluation"]["n_eval_episodes"]
    comp_cfg: dict = cfg["comparison"]
    distill_n: int = comp_cfg["distill_n_samples"]
    eval_n: int = comp_cfg["eval_n_samples"]
    n_steps: int = cfg["lunar"]["n_steps"]
    gravity_conds: list[dict] = cfg["lunar"]["gravity_conditions"]
    train_gravity: float = gravity_conds[0]["gravity"]
    n_actions = 4
    n_obs = 8

    records = []

    algorithm = cfg["lunar"].get("algorithm", "dqn").lower()
    n_envs = cfg["lunar"].get("n_envs", 1)

    # oracle_model_dir: 外部の学習済みモデルを参照する場合に指定
    oracle_dir_lunar = Path(cfg["lunar"].get("oracle_model_dir", str(output_dir)))

    for seed in seeds:
        # Intuitive policy の学習 or 再利用（oracle_model_dir を優先参照）
        for search_dir in [oracle_dir_lunar, output_dir]:
            model_path = search_dir / f"intuitive_lunar_seed{seed}"
            zip_path = search_dir / f"intuitive_lunar_seed{seed}.zip"
            if model_path.exists() or zip_path.exists():
                load_path = str(model_path if model_path.exists() else zip_path)
                env = make_lunar(gravity=train_gravity)
                if algorithm == "ppo":
                    model = PPO.load(load_path, env=env)
                else:
                    model = DQN.load(load_path, env=env)
                env.close()
                print(f"  [LunarLander seed={seed}] 既存モデルを再利用: {load_path}", flush=True)
                break
        else:
            # モデルが見つからない場合は新規学習して output_dir に保存
            new_model_path = output_dir / f"intuitive_lunar_seed{seed}"
            if algorithm == "ppo":
                vec_env = make_vec_env(lambda: make_lunar(gravity=train_gravity), n_envs=n_envs)
                model = PPO(
                    "MlpPolicy", vec_env,
                    n_steps=1024, batch_size=64,
                    gae_lambda=0.98, gamma=0.999,
                    n_epochs=4, ent_coef=0.01,
                    seed=seed, verbose=0,
                )
                model.learn(total_timesteps=n_steps)
                model.save(str(new_model_path))
                vec_env.close()
                print(f"  [LunarLander seed={seed}] PPO 学習完了 ({n_steps} steps)", flush=True)
            else:
                env = make_lunar(gravity=train_gravity)
                model = DQN(
                    "MlpPolicy", env,
                    learning_rate=6.3e-4, batch_size=128,
                    buffer_size=50000, learning_starts=0,
                    train_freq=4, gradient_steps=-1,
                    target_update_interval=250,
                    exploration_fraction=0.12,
                    exploration_final_eps=0.1,
                    policy_kwargs=dict(net_arch=[256, 256]),
                    seed=seed, verbose=0,
                )
                model.learn(total_timesteps=n_steps)
                model.save(str(new_model_path))
                env.close()
                print(f"  [LunarLander seed={seed}] DQN 学習完了 ({n_steps} steps)", flush=True)

        eval_seed = seed + 10000

        # 蒸留データを訓練重力で収集（AA は各条件ごとに計算するため train eval は不要）
        obs_all, act_all = collect_lunar(model, train_gravity, distill_n, seed)

        for model_type in comp_cfg["model_types"]:
            try:
                rm = make_model(model_type, n_obs, n_actions, comp_cfg)
                rm = fit_model(rm, obs_all, act_all, comp_cfg)
            except Exception as e:
                print(
                    f"  [Hopper, {model_type}] 学習スキップ: {type(e).__name__}: {e}",
                    flush=True,
                )
                continue

            for gc in gravity_conds:
                cname = gc["name"]
                gravity = gc["gravity"]

                # 各重力条件の状態で AA を計算（M2 対応: per-condition AA）
                obs_eval_cond, act_eval_cond = collect_lunar(model, gravity, eval_n, eval_seed)
                rm_actions_cond = rm.predict(obs_eval_cond)
                aa_cond = float(np.mean(act_eval_cond == rm_actions_cond))
                kl_cond = _kl_empirical(act_eval_cond, rm_actions_cond, n_actions)

                j_intuitive = eval_lunar_intuitive(model, gravity, n_eval, eval_seed)

                # Surrogate model のロールアウト評価
                eval_env = make_lunar(gravity=gravity)
                j_reasoned = 0.0
                for ep in range(n_eval):
                    obs, _ = eval_env.reset(seed=eval_seed + ep)
                    done = False
                    while not done:
                        action = int(rm.predict(obs[np.newaxis])[0])
                        obs, reward, terminated, truncated, _ = eval_env.step(action)
                        j_reasoned += reward
                        done = terminated or truncated
                eval_env.close()
                j_reasoned /= n_eval

                rpd = relative_perf_drop(j_intuitive, j_reasoned)

                records.append({
                    "env": "lunarlander",
                    "model_type": model_type,
                    "eval_condition": cname,
                    "gravity": gravity,
                    "seed": seed,
                    "j_intuitive": j_intuitive,
                    "j_reasoned": j_reasoned,
                    "action_agreement": aa_cond,
                    "kl_divergence": kl_cond,
                    "relative_perf_drop": rpd,
                })

            # train 条件の AA をサマリー表示
            train_aa = records[-len(gravity_conds)]["action_agreement"]
            print(
                f"  [LunarLander, {MODEL_LABEL[model_type]:6s}, seed={seed}]"
                f"  AA(train)={train_aa:.3f}  J(train)={records[-len(gravity_conds)]['j_reasoned']:.1f}",
                flush=True,
            )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Hopper ユーティリティ
# ---------------------------------------------------------------------------

def _collect_hopper_gravity(
    sac_model,
    gravity: float,
    n_samples: int,
    seed: int,
    bins_per_dim: int,
) -> tuple[np.ndarray, np.ndarray]:
    """指定重力の Hopper 環境でロールアウトし (obs, binned_action) を収集する。"""
    import gymnasium as gym
    from experiments.src.hopper_env import BinnedHopperEnv, ACTION_DIM

    binner = BinnedHopperEnv(bins_per_dim=bins_per_dim)
    raw_env = gym.make("Hopper-v5")
    raw_env.unwrapped.model.opt.gravity[2] = gravity
    obs_list, act_list = [], []
    rng = np.random.default_rng(seed)
    obs, _ = raw_env.reset(seed=int(rng.integers(1_000_000)))
    raw_env.unwrapped.model.opt.gravity[2] = gravity
    while len(obs_list) < n_samples:
        cont_action, _ = sac_model.predict(obs, deterministic=True)
        binned = binner.bin_continuous(cont_action)
        obs_list.append(obs.copy())
        act_list.append(binned)
        obs, _, terminated, truncated, _ = raw_env.step(cont_action)
        if terminated or truncated:
            obs, _ = raw_env.reset(seed=int(rng.integers(1_000_000)))
            raw_env.unwrapped.model.opt.gravity[2] = gravity
    raw_env.close()
    binner.close()
    return (
        np.array(obs_list[:n_samples], dtype=np.float32),
        np.array(act_list[:n_samples], dtype=np.int64),
    )


# ---------------------------------------------------------------------------
# Hopper
# ---------------------------------------------------------------------------

def run_hopper(cfg: dict, output_dir: Path) -> pd.DataFrame:
    from experiments.src.hopper_env import (
        BinnedHopperEnv,
        collect_transitions as collect_hopper,
        evaluate_intuitive as eval_hopper_intuitive,
        evaluate_reasoned as eval_hopper_reasoned,
        DEFAULT_BINS_PER_DIM,
    )
    import gymnasium as gym

    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_eval: int = cfg["evaluation"]["n_eval_episodes"]
    comp_cfg: dict = cfg["comparison"]
    distill_n: int = comp_cfg["distill_n_samples"]
    eval_n: int = comp_cfg["eval_n_samples"]
    n_steps: int = cfg["hopper"]["n_steps"]
    bins_per_dim: int = cfg["hopper"]["bins_per_dim"]
    dynamics_conds: list[dict] = cfg["hopper"].get("dynamics_conditions") or cfg["hopper"].get("gravity_conditions", [])
    if not dynamics_conds:
        raise ValueError("hopper.dynamics_conditions か hopper.gravity_conditions を設定してください。")
    train_cond = dynamics_conds[0]
    train_gravity: float = train_cond.get("gravity", -9.81)
    train_friction_scale: float | None = train_cond.get("friction_scale", None)
    gravity_conds = dynamics_conds  # 既存の離散 Hopper 実装との互換
    n_actions = bins_per_dim ** 3
    n_obs = 11

    records = []

    # oracle_model_dir: 外部の学習済みモデルを参照する場合に指定
    oracle_dir_hopper = Path(cfg["hopper"].get("oracle_model_dir", str(output_dir)))

    for seed in seeds:
        # Intuitive policy の学習 or 再利用（oracle_model_dir を優先参照）
        for search_dir in [oracle_dir_hopper, output_dir]:
            model_path = search_dir / f"intuitive_hopper_seed{seed}"
            zip_path = search_dir / f"intuitive_hopper_seed{seed}.zip"
            if model_path.exists() or zip_path.exists():
                raw_env = gym.make("Hopper-v5")
                model = SAC.load(str(model_path if model_path.exists() else zip_path), env=raw_env)
                raw_env.close()
                print(f"  [Hopper seed={seed}] 既存モデルを再利用: {model_path if model_path.exists() else zip_path}", flush=True)
                break
        else:
            new_model_path = output_dir / f"intuitive_hopper_seed{seed}"
            raw_env = gym.make("Hopper-v5")
            model = SAC(
                "MlpPolicy", raw_env,
                learning_rate=3e-4, batch_size=256,
                buffer_size=100000, learning_starts=5000,
                seed=seed, verbose=0,
            )
            model.learn(total_timesteps=n_steps)
            model.save(str(new_model_path))
            raw_env.close()
            print(f"  [Hopper seed={seed}] SAC 学習完了 ({n_steps} steps)", flush=True)

        eval_seed = seed + 10000

        # 蒸留データを訓練重力で収集
        obs_all, act_all = collect_hopper(model, distill_n, seed, bins_per_dim)

        for model_type in comp_cfg["model_types"]:
            rm = make_model(model_type, n_obs, n_actions, comp_cfg)
            rm = fit_model(rm, obs_all, act_all, comp_cfg)

            for gc in gravity_conds:
                cname = gc["name"]
                gravity = gc["gravity"]

                # 各重力条件の oracle rollout データで per-condition AA を計算
                if cname == "train":
                    obs_eval_cond, act_eval_cond = collect_hopper(model, eval_n, eval_seed, bins_per_dim)
                else:
                    obs_eval_cond, act_eval_cond = _collect_hopper_gravity(model, gravity, eval_n, eval_seed, bins_per_dim)
                rm_actions_cond = rm.predict(obs_eval_cond)
                aa_cond = float(np.mean(act_eval_cond == rm_actions_cond))
                kl_cond = _kl_empirical(act_eval_cond, rm_actions_cond, n_actions)

                j_intuitive = eval_hopper_intuitive(model, gravity, n_eval, eval_seed)
                j_reasoned = eval_hopper_reasoned(rm, gravity, n_eval, eval_seed, bins_per_dim)
                rpd = relative_perf_drop(j_intuitive, j_reasoned)

                records.append({
                    "env": "hopper",
                    "model_type": model_type,
                    "eval_condition": cname,
                    "gravity": gravity,
                    "seed": seed,
                    "j_intuitive": j_intuitive,
                    "j_reasoned": j_reasoned,
                    "action_agreement": aa_cond,
                    "kl_divergence": kl_cond,
                    "relative_perf_drop": rpd,
                })

            train_rec = next(r for r in reversed(records) if r["eval_condition"] == "train" and r["seed"] == seed and r["model_type"] == model_type)
            print(
                f"  [Hopper,      {MODEL_LABEL.get(model_type, model_type):6s}, seed={seed}]"
                f"  AA(train)={train_rec['action_agreement']:.3f}  J(train)={train_rec['j_reasoned']:.1f}",
                flush=True,
            )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Hopper 回帰型 Surrogate（連続行動・AA 再定義）
# ---------------------------------------------------------------------------

def _continuous_aa(a_oracle: np.ndarray, a_surrogate: np.ndarray, eps: float) -> float:
    """ε-agreement: ||a_s − a_o||₂ < ε の割合。
    離散 AA（exact match）の連続行動版アナログ。
    """
    diffs = np.linalg.norm(a_oracle - a_surrogate, axis=1)
    return float(np.mean(diffs < eps))


def make_regression_model(model_type: str, input_dim: int, action_dim: int, comp_cfg: dict):
    if model_type == "reg_tree":
        max_depth = comp_cfg.get("reg_tree", {}).get("max_depth", 5)
        return RegressionTreeModel(input_dim, action_dim, max_depth=max_depth)
    elif model_type == "reg_linear":
        return RegressionLinearModel(input_dim, action_dim)
    elif model_type == "reg_ebm":
        ebm_cfg = comp_cfg.get("reg_ebm", {})
        return EBMRegressionReasonedModel(
            input_dim, action_dim,
            max_rounds=ebm_cfg.get("max_rounds", 300),
            outer_bags=ebm_cfg.get("outer_bags", 8),
            interactions=ebm_cfg.get("interactions", 0),
        )
    elif model_type == "reg_sdt":
        sdt_cfg = comp_cfg.get("reg_sdt", {})
        return SoftDecisionTreeRegressionReasonedModel(
            input_dim, action_dim,
            depth=sdt_cfg.get("depth", 5),
            epochs=sdt_cfg.get("epochs", 150),
            lr=sdt_cfg.get("lr", 1e-3),
            batch_size=sdt_cfg.get("batch_size", 512),
            l2_leaf_coef=sdt_cfg.get("l2_leaf_coef", 1e-4),
            seed=sdt_cfg.get("seed", 42),
        )
    elif model_type == "reg_symbolic":
        sym_cfg = comp_cfg.get("reg_symbolic", {})
        return SymbolicRegressionReasonedModel(
            input_dim, action_dim,
            population_size=sym_cfg.get("population_size", 1200),
            generations=sym_cfg.get("generations", 25),
            tournament_size=sym_cfg.get("tournament_size", 20),
            parsimony_coefficient=sym_cfg.get("parsimony_coefficient", 0.001),
            random_state=sym_cfg.get("random_state", 42),
        )
    elif model_type == "reg_gbt":
        gbt_cfg = comp_cfg.get("reg_gbt", {})
        return GBTRegressionReasonedModel(
            input_dim, action_dim,
            max_iter=gbt_cfg.get("max_iter", 300),
            max_depth=gbt_cfg.get("max_depth", None),
            learning_rate=gbt_cfg.get("learning_rate", 0.1),
        )
    else:
        raise ValueError(f"Unknown regression model_type: {model_type}")


def _collect_dagger_iter(
    surrogate,
    oracle_model,
    n_samples: int,
    seed: int,
    gravity: float,
    friction_scale: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    """DAgger 1 イテレーション: surrogate が踏む状態分布で oracle にラベルを問い合わせる。

    surrogate が環境を歩き、各ステップで oracle の行動を正解ラベルとして収集する。
    これにより BC の covariate shift（oracle 状態分布 vs surrogate 状態分布のずれ）を修正する。
    """
    import gymnasium as gym
    from experiments.src.hopper_env import apply_hopper_dynamics

    env = gym.make("Hopper-v5")
    base_friction = env.unwrapped.model.geom_friction.copy()
    apply_hopper_dynamics(env, gravity=gravity, friction_scale=friction_scale, base_friction=base_friction)
    rng = np.random.default_rng(seed)
    obs_list, act_list = [], []
    obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    apply_hopper_dynamics(env, gravity=gravity, friction_scale=friction_scale, base_friction=base_friction)
    while len(obs_list) < n_samples:
        # surrogate の行動で状態を遷移させる（surrogate が踏む状態分布を生成）
        surrogate_action = surrogate.predict(obs[np.newaxis])[0]
        # この状態に対する oracle の正解ラベルを収集
        oracle_action, _ = oracle_model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        act_list.append(oracle_action.copy())
        obs, _, terminated, truncated, _ = env.step(surrogate_action)
        if terminated or truncated:
            obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
            apply_hopper_dynamics(env, gravity=gravity, friction_scale=friction_scale, base_friction=base_friction)
    env.close()
    return (
        np.array(obs_list[:n_samples], dtype=np.float32),
        np.array(act_list[:n_samples], dtype=np.float32),
    )


def run_hopper_regression_dagger(cfg: dict, output_dir: Path) -> pd.DataFrame:
    """DAgger による Hopper 蒸留実験。

    各イテレーションで surrogate が踏む状態分布を oracle にラベリングさせ、
    BC の covariate shift 問題を iterative に修正する。
    """
    from experiments.src.hopper_env import (
        collect_transitions_continuous,
        evaluate_intuitive as eval_hopper_intuitive,
        evaluate_reasoned_continuous,
    )
    import gymnasium as gym

    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_eval: int = cfg["evaluation"]["n_eval_episodes"]
    comp_cfg: dict = cfg["comparison"]
    distill_n: int = comp_cfg["distill_n_samples"]
    eval_n: int = comp_cfg["eval_n_samples"]
    dagger_cfg: dict = cfg.get("dagger", {})
    n_iters: int = dagger_cfg.get("iterations", 10)
    samples_per_iter: int = dagger_cfg.get("samples_per_iter", 10000)

    dynamics_conds: list[dict] = cfg["hopper"].get("dynamics_conditions") or cfg["hopper"].get("gravity_conditions", [])
    if not dynamics_conds:
        raise ValueError("hopper.dynamics_conditions か hopper.gravity_conditions を設定してください。")
    train_cond = dynamics_conds[0]
    train_gravity: float = train_cond.get("gravity", -9.81)
    train_friction_scale: float | None = train_cond.get("friction_scale", None)
    aa_eps: float = cfg["hopper"].get("aa_epsilon", 0.2)
    n_obs = 11
    action_dim = 3

    records = []
    action_diff_dir = output_dir / "action_diffs"
    action_diff_dir.mkdir(parents=True, exist_ok=True)
    oracle_model_path = cfg["hopper"].get("oracle_model_path", None)
    oracle_algo = cfg["hopper"].get("oracle_algo", "sac").lower()

    for seed in seeds:
        # oracle ロード
        if oracle_model_path:
            raw_env = gym.make("Hopper-v5")
            load_path = str((ROOT / oracle_model_path) if not Path(oracle_model_path).is_absolute() else Path(oracle_model_path))
            if oracle_algo == "td3":
                oracle = TD3.load(load_path, env=raw_env)
            elif oracle_algo == "ppo":
                oracle = PPO.load(load_path, env=raw_env)
            else:
                oracle = SAC.load(load_path, env=raw_env)
            raw_env.close()
        else:
            raise ValueError("hopper.oracle_model_path が必要です。")

        eval_seed = seed + 10000

        # AA 評価用の oracle 状態を一度だけ収集してイテレーション全体で共有
        obs_oracle_eval, act_oracle_eval = collect_transitions_continuous(
            oracle, eval_n, eval_seed,
            gravity=train_gravity, friction_scale=train_friction_scale,
        )

        for model_type in comp_cfg["model_types"]:
            try:
                rm = make_regression_model(model_type, n_obs, action_dim, comp_cfg)
            except Exception as e:
                print(f"  [DAgger, {model_type}] モデル生成スキップ: {e}", flush=True)
                continue

            # --- イテレーション 0: 通常 BC（oracle 状態分布） ---
            obs_all, act_all = collect_transitions_continuous(
                oracle, distill_n, seed,
                gravity=train_gravity, friction_scale=train_friction_scale,
            )
            rm.fit(obs_all, act_all)

            j_train = evaluate_reasoned_continuous(
                rm, train_gravity, n_eval, eval_seed, friction_scale=train_friction_scale,
            )
            rm_aa0 = rm.predict(obs_oracle_eval)
            aa_train = float(np.mean(np.linalg.norm(act_oracle_eval - rm_aa0, axis=1) < aa_eps))
            print(
                f"  [DAgger iter=0, {MODEL_LABEL.get(model_type, model_type)}, seed={seed}]"
                f"  n_total={len(obs_all)}  AA={aa_train:.3f}  J(train)={j_train:.1f}",
                flush=True,
            )

            # --- DAgger イテレーション ---
            for it in range(1, n_iters + 1):
                iter_seed = seed * 1000 + it  # イテレーションごとに異なるシードで収集
                new_obs, new_act = _collect_dagger_iter(
                    rm, oracle, samples_per_iter,
                    seed=iter_seed,
                    gravity=train_gravity,
                    friction_scale=train_friction_scale,
                )
                obs_all = np.concatenate([obs_all, new_obs], axis=0)
                act_all = np.concatenate([act_all, new_act], axis=0)
                rm.fit(obs_all, act_all)

                j_train = evaluate_reasoned_continuous(
                    rm, train_gravity, n_eval, eval_seed, friction_scale=train_friction_scale,
                )
                rm_aa_it = rm.predict(obs_oracle_eval)
                aa_train = float(np.mean(np.linalg.norm(act_oracle_eval - rm_aa_it, axis=1) < aa_eps))
                print(
                    f"  [DAgger iter={it}, {MODEL_LABEL.get(model_type, model_type)}, seed={seed}]"
                    f"  n_total={len(obs_all)}  AA={aa_train:.3f}  J(train)={j_train:.1f}",
                    flush=True,
                )

            # --- 最終モデルで全条件評価（run_hopper_regression と同一フォーマット） ---
            for gc in dynamics_conds:
                cname = gc["name"]
                gravity = gc.get("gravity", train_gravity)
                friction_scale = gc.get("friction_scale", None)

                obs_eval, act_eval = collect_transitions_continuous(
                    oracle, eval_n, eval_seed,
                    gravity=gravity, friction_scale=friction_scale,
                )
                rm_actions = rm.predict(obs_eval)
                l2_diffs = np.linalg.norm(act_eval - rm_actions, axis=1)
                aa_cond = float(np.mean(l2_diffs < aa_eps))
                diff_path = action_diff_dir / f"seed{seed}_{model_type}_{cname}.npz"
                np.savez_compressed(
                    diff_path,
                    l2_diffs=l2_diffs.astype(np.float32),
                    oracle_actions=act_eval.astype(np.float32),
                    surrogate_actions=rm_actions.astype(np.float32),
                )

                j_intuitive = eval_hopper_intuitive(
                    oracle, gravity, n_eval, eval_seed, friction_scale=friction_scale,
                )
                j_reasoned = evaluate_reasoned_continuous(
                    rm, gravity, n_eval, eval_seed, friction_scale=friction_scale,
                )
                rpd = relative_perf_drop(j_intuitive, j_reasoned)

                records.append({
                    "env": "hopper",
                    "model_type": model_type,
                    "eval_condition": cname,
                    "gravity": gravity,
                    "friction_scale": friction_scale if friction_scale is not None else 1.0,
                    "seed": seed,
                    "j_intuitive": j_intuitive,
                    "j_reasoned": j_reasoned,
                    "action_agreement": aa_cond,
                    "action_l2_mean": float(np.mean(l2_diffs)),
                    "action_l2_p90": float(np.quantile(l2_diffs, 0.9)),
                    "action_l2_p95": float(np.quantile(l2_diffs, 0.95)),
                    "relative_perf_drop": rpd,
                })

            train_rec = next(
                r for r in reversed(records)
                if r["eval_condition"] == "train" and r["seed"] == seed and r["model_type"] == model_type
            )
            print(
                f"  [DAgger FINAL, {MODEL_LABEL.get(model_type, model_type):10s}, seed={seed}]"
                f"  AA_eps(train)={train_rec['action_agreement']:.3f}"
                f"  J(train)={train_rec['j_reasoned']:.1f}",
                flush=True,
            )

    return pd.DataFrame(records)


def run_hopper_regression(cfg: dict, output_dir: Path) -> pd.DataFrame:
    """回帰型 Surrogate による Hopper 実験。

    binning なし・連続行動を直接模倣し、AA を ε-agreement で定義する。
    """
    from experiments.src.hopper_env import (
        collect_transitions_continuous,
        evaluate_intuitive as eval_hopper_intuitive,
        evaluate_reasoned_continuous,
    )
    import gymnasium as gym

    seeds: list[int] = cfg["evaluation"]["seeds"]
    n_eval: int = cfg["evaluation"]["n_eval_episodes"]
    comp_cfg: dict = cfg["comparison"]
    distill_n: int = comp_cfg["distill_n_samples"]
    eval_n: int = comp_cfg["eval_n_samples"]
    dynamics_conds: list[dict] = cfg["hopper"].get("dynamics_conditions") or cfg["hopper"].get("gravity_conditions", [])
    if not dynamics_conds:
        raise ValueError("hopper.dynamics_conditions か hopper.gravity_conditions を設定してください。")
    train_cond = dynamics_conds[0]
    train_gravity: float = train_cond.get("gravity", -9.81)
    train_friction_scale: float | None = train_cond.get("friction_scale", None)
    aa_eps: float = cfg["hopper"].get("aa_epsilon", 0.2)
    n_obs = 11
    action_dim = 3

    records = []
    action_diff_dir = output_dir / "action_diffs"
    action_diff_dir.mkdir(parents=True, exist_ok=True)
    oracle_dir_hopper = Path(cfg["hopper"].get("oracle_model_dir", str(output_dir)))
    oracle_model_path = cfg["hopper"].get("oracle_model_path", None)
    oracle_algo = cfg["hopper"].get("oracle_algo", "sac").lower()

    for seed in seeds:
        if oracle_model_path:
            raw_env = gym.make("Hopper-v5")
            load_path = str((ROOT / oracle_model_path) if not Path(oracle_model_path).is_absolute() else Path(oracle_model_path))
            if oracle_algo == "ppo":
                model = PPO.load(load_path, env=raw_env)
            elif oracle_algo == "td3":
                model = TD3.load(load_path, env=raw_env)
            else:
                model = SAC.load(load_path, env=raw_env)
            raw_env.close()
            print(f"  [Hopper seed={seed}] oracle_model_path を利用: {load_path} (algo={oracle_algo})", flush=True)
        else:
            for search_dir in [oracle_dir_hopper, output_dir]:
                model_path = search_dir / f"intuitive_hopper_seed{seed}"
                zip_path = search_dir / f"intuitive_hopper_seed{seed}.zip"
                if model_path.exists() or zip_path.exists():
                    raw_env = gym.make("Hopper-v5")
                    model = SAC.load(str(model_path if model_path.exists() else zip_path), env=raw_env)
                    raw_env.close()
                    print(f"  [Hopper seed={seed}] 既存モデルを再利用: {model_path if model_path.exists() else zip_path}", flush=True)
                    break
            else:
                raise FileNotFoundError(
                    f"Oracle model not found for seed={seed}. "
                    "Set hopper.oracle_model_dir or hopper.oracle_model_path in config."
                )

        eval_seed = seed + 10000

        # 蒸留データ（連続行動）を訓練条件（重力・摩擦）で収集
        obs_all, act_all = collect_transitions_continuous(
            model,
            distill_n,
            seed,
            gravity=train_gravity,
            friction_scale=train_friction_scale,
        )

        for model_type in comp_cfg["model_types"]:
            try:
                rm = make_regression_model(model_type, n_obs, action_dim, comp_cfg)
                rm.fit(obs_all, act_all)
            except Exception as e:
                print(
                    f"  [Hopper(Reg), {model_type}] 学習スキップ: {type(e).__name__}: {e}",
                    flush=True,
                )
                continue

            for gc in dynamics_conds:
                cname = gc["name"]
                gravity = gc.get("gravity", train_gravity)
                friction_scale = gc.get("friction_scale", None)

                # per-condition AA: 各力学条件の oracle rollout と比較
                obs_eval, act_eval = collect_transitions_continuous(
                    model,
                    eval_n,
                    eval_seed,
                    gravity=gravity,
                    friction_scale=friction_scale,
                )
                rm_actions = rm.predict(obs_eval)
                l2_diffs = np.linalg.norm(act_eval - rm_actions, axis=1)
                aa_cond = float(np.mean(l2_diffs < aa_eps))
                diff_path = action_diff_dir / f"seed{seed}_{model_type}_{cname}.npz"
                np.savez_compressed(
                    diff_path,
                    l2_diffs=l2_diffs.astype(np.float32),
                    oracle_actions=act_eval.astype(np.float32),
                    surrogate_actions=rm_actions.astype(np.float32),
                )

                j_intuitive = eval_hopper_intuitive(
                    model,
                    gravity,
                    n_eval,
                    eval_seed,
                    friction_scale=friction_scale,
                )
                j_reasoned = evaluate_reasoned_continuous(
                    rm,
                    gravity,
                    n_eval,
                    eval_seed,
                    friction_scale=friction_scale,
                )
                rpd = relative_perf_drop(j_intuitive, j_reasoned)

                records.append({
                    "env": "hopper",
                    "model_type": model_type,
                    "eval_condition": cname,
                    "gravity": gravity,
                    "friction_scale": friction_scale if friction_scale is not None else 1.0,
                    "seed": seed,
                    "j_intuitive": j_intuitive,
                    "j_reasoned": j_reasoned,
                    "action_agreement": aa_cond,
                    "action_l2_mean": float(np.mean(l2_diffs)),
                    "action_l2_p90": float(np.quantile(l2_diffs, 0.9)),
                    "action_l2_p95": float(np.quantile(l2_diffs, 0.95)),
                    "relative_perf_drop": rpd,
                })

            train_rec = next(
                r for r in reversed(records)
                if r["eval_condition"] == "train" and r["seed"] == seed and r["model_type"] == model_type
            )
            print(
                f"  [Hopper(Reg), {MODEL_LABEL.get(model_type, model_type):10s}, seed={seed}]"
                f"  AA_eps(train)={train_rec['action_agreement']:.3f}"
                f"  J(train)={train_rec['j_reasoned']:.1f}",
                flush=True,
            )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 可視化・サマリー
# ---------------------------------------------------------------------------

def _plot_results(df: pd.DataFrame, output_dir: Path) -> None:
    for env_name in df["env"].unique():
        sub = df[df["env"] == env_name]
        conds = sub["eval_condition"].unique()
        fig, axes = plt.subplots(1, len(conds), figsize=(5 * len(conds), 4), sharey=True)
        if len(conds) == 1:
            axes = [axes]
        for ax, cond in zip(axes, conds):
            sc = sub[sub["eval_condition"] == cond]
            for mt in sub["model_type"].unique():
                vals = sc[sc["model_type"] == mt]["action_agreement"]
                if vals.empty:
                    continue
                ax.bar(MODEL_LABEL[mt], vals.mean(), yerr=vals.std(),
                       color=COLORS[mt], alpha=0.8, capsize=5)
            ax.set_title(cond)
            ax.set_ylabel("Action Agreement (AA)")
            ax.set_ylim(0, 1.05)
            ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
        fig.suptitle(f"{env_name}: AA under dynamics shifts")
        plt.tight_layout()
        out = output_dir / f"aa_bar_{env_name}.png"
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"図を保存: {out}", flush=True)


def _save_summary(df: pd.DataFrame, output_dir: Path) -> None:
    lines = ["=== 予備実験（連続制御）サマリー ===\n"]
    for env_name in df["env"].unique():
        sub = df[df["env"] == env_name]
        lines.append(f"【{env_name}】")
        grp = sub.groupby(["model_type", "eval_condition"])["action_agreement"].agg(["mean", "std"])
        for (mt, cond), row in grp.iterrows():
            lines.append(
                f"  {MODEL_LABEL.get(mt, mt):6s}  {cond:12s}"
                f"  AA={row['mean']:.3f}±{row['std']:.3f}"
            )
        lines.append("")
    path = output_dir / "summary.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n" + "\n".join(lines), flush=True)


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def run_experiment(cfg: dict) -> None:
    output_dir = ROOT / cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    all_records = []

    if cfg.get("lunar"):
        print("=== LunarLander 実験 ===", flush=True)
        lunar_df = run_lunarlander(cfg, output_dir)
        all_records.append(lunar_df)

    if cfg.get("hopper"):
        if cfg["hopper"].get("dagger_mode", False):
            print("\n=== Hopper 実験 (DAgger Regression Surrogate) ===", flush=True)
            hopper_df = run_hopper_regression_dagger(cfg, output_dir)
        elif cfg["hopper"].get("regression_mode", False):
            print("\n=== Hopper 実験 (Regression Surrogate) ===", flush=True)
            hopper_df = run_hopper_regression(cfg, output_dir)
        else:
            print("\n=== Hopper 実験 ===", flush=True)
            hopper_df = run_hopper(cfg, output_dir)
        all_records.append(hopper_df)

    df = pd.concat([d for d in all_records if not d.empty], ignore_index=True)

    # --seed 1シードで並列実行した場合はシード別ファイルに保存（競合防止）
    seeds = cfg.get("evaluation", {}).get("seeds", [])
    if len(seeds) == 1:
        csv_path = output_dir / f"metrics_seed{seeds[0]}.csv"
    else:
        csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存: {csv_path}", flush=True)

    _plot_results(df, output_dir)
    _save_summary(df, output_dir)
