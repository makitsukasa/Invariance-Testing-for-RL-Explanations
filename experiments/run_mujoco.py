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
from stable_baselines3 import DQN, PPO, SAC
from stable_baselines3.common.env_util import make_vec_env

from experiments.src.evaluate import action_agreement, relative_perf_drop
from experiments.run_comparison import make_model, fit_model

MODEL_LABEL = {"moet": "MoET", "linear": "Linear", "tree": "Tree"}
COLORS = {"moet": "steelblue", "linear": "tomato", "tree": "seagreen"}


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

    for seed in seeds:
        # Intuitive policy の学習 or 再利用
        model_path = output_dir / f"intuitive_lunar_seed{seed}"
        zip_path = output_dir / f"intuitive_lunar_seed{seed}.zip"
        if model_path.exists() or zip_path.exists():
            load_path = str(model_path if model_path.exists() else zip_path)
            env = make_lunar(gravity=train_gravity)
            if algorithm == "ppo":
                model = PPO.load(load_path, env=env)
            else:
                model = DQN.load(load_path, env=env)
            env.close()
            print(f"  [LunarLander seed={seed}] 既存モデルを再利用", flush=True)
        elif algorithm == "ppo":
            vec_env = make_vec_env(lambda: make_lunar(gravity=train_gravity), n_envs=n_envs)
            model = PPO(
                "MlpPolicy", vec_env,
                n_steps=1024, batch_size=64,
                gae_lambda=0.98, gamma=0.999,
                n_epochs=4, ent_coef=0.01,
                seed=seed, verbose=0,
            )
            model.learn(total_timesteps=n_steps)
            model.save(str(model_path))
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
            model.save(str(model_path))
            env.close()
            print(f"  [LunarLander seed={seed}] DQN 学習完了 ({n_steps} steps)", flush=True)

        eval_seed = seed + 10000

        # 蒸留データを訓練重力で収集（AA は各条件ごとに計算するため train eval は不要）
        obs_all, act_all = collect_lunar(model, train_gravity, distill_n, seed)

        for model_type in comp_cfg["model_types"]:
            rm = make_model(model_type, n_obs, n_actions, comp_cfg)
            rm = fit_model(rm, obs_all, act_all, comp_cfg)

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
    gravity_conds: list[dict] = cfg["hopper"]["gravity_conditions"]
    train_gravity: float = gravity_conds[0]["gravity"]
    n_actions = bins_per_dim ** 3
    n_obs = 11

    records = []

    for seed in seeds:
        # Intuitive policy の学習 or 再利用 (SAC)
        model_path = output_dir / f"intuitive_hopper_seed{seed}"
        zip_path = output_dir / f"intuitive_hopper_seed{seed}.zip"
        if model_path.exists() or zip_path.exists():
            raw_env = gym.make("Hopper-v5")
            model = SAC.load(str(model_path if model_path.exists() else zip_path), env=raw_env)
            raw_env.close()
            print(f"  [Hopper seed={seed}] 既存モデルを再利用", flush=True)
        else:
            raw_env = gym.make("Hopper-v5")
            model = SAC(
                "MlpPolicy", raw_env,
                learning_rate=3e-4, batch_size=256,
                buffer_size=100000, learning_starts=5000,
                seed=seed, verbose=0,
            )
            model.learn(total_timesteps=n_steps)
            model.save(str(model_path))
            raw_env.close()
            print(f"  [Hopper seed={seed}] SAC 学習完了 ({n_steps} steps)", flush=True)

        eval_seed = seed + 10000

        # 蒸留データと評価データを収集（訓練重力）
        obs_all, act_all = collect_hopper(model, distill_n, seed, bins_per_dim)
        obs_eval, act_eval = collect_hopper(model, eval_n, eval_seed, bins_per_dim)

        for model_type in comp_cfg["model_types"]:
            rm = make_model(model_type, n_obs, n_actions, comp_cfg)
            rm = fit_model(rm, obs_all, act_all, comp_cfg)

            rm_actions_eval = rm.predict(obs_eval)
            aa_train = float(np.mean(act_eval == rm_actions_eval))
            kl_train = _kl_empirical(act_eval, rm_actions_eval, n_actions)

            for gc in gravity_conds:
                cname = gc["name"]
                gravity = gc["gravity"]

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
                    "action_agreement": aa_train,
                    "kl_divergence": kl_train,
                    "relative_perf_drop": rpd,
                })

            print(
                f"  [Hopper,      {MODEL_LABEL[model_type]:6s}, seed={seed}]"
                f"  AA={aa_train:.3f}  J(train)={records[-len(gravity_conds)]['j_reasoned']:.1f}",
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
            for mt in ["moet", "tree", "linear"]:
                vals = sc[sc["model_type"] == mt]["action_agreement"]
                if vals.empty:
                    continue
                ax.bar(MODEL_LABEL[mt], vals.mean(), yerr=vals.std(),
                       color=COLORS[mt], alpha=0.8, capsize=5)
            ax.set_title(cond)
            ax.set_ylabel("Action Agreement (AA)")
            ax.set_ylim(0, 1.05)
            ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
        fig.suptitle(f"{env_name}: AA under gravity shifts")
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
        print("\n=== Hopper 実験 ===", flush=True)
        hopper_df = run_hopper(cfg, output_dir)
        all_records.append(hopper_df)

    df = pd.concat([d for d in all_records if not d.empty], ignore_index=True)
    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nmetrics.csv を保存: {csv_path}", flush=True)

    _plot_results(df, output_dir)
    _save_summary(df, output_dir)
