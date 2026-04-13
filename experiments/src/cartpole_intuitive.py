from pathlib import Path

import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy

from .cartpole_env import NoisyCartPoleEnv


def train_intuitive(noise_dim: int, n_steps: int, seed: int, save_path: Path) -> DQN:
    """DQN を学習し、学習中のベストモデルを保存して返す。

    RL Zoo CartPole-v1 DQN パラメータは ~50k steps でピークに達した後に劣化する
    ことがあるため、EvalCallback でベストチェックポイントを保存する。
    """
    save_path.parent.mkdir(parents=True, exist_ok=True)
    env = NoisyCartPoleEnv(noise_dim=noise_dim)
    eval_env = NoisyCartPoleEnv(noise_dim=noise_dim)
    best_model_dir = save_path.parent / f"{save_path.name}_best"
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(best_model_dir),
        log_path=None,
        eval_freq=5_000,
        n_eval_episodes=20,
        deterministic=True,
        verbose=0,
    )
    model = DQN(
        "MlpPolicy",
        env,
        learning_rate=2.3e-3,
        batch_size=64,
        buffer_size=100_000,
        learning_starts=1_000,
        target_update_interval=10,
        train_freq=256,
        gradient_steps=128,
        exploration_fraction=0.16,
        exploration_final_eps=0.04,
        seed=seed,
        verbose=0,
    )
    model.learn(total_timesteps=n_steps, callback=eval_callback)
    eval_env.close()
    env.close()
    # ベストモデルを読み込んで保存
    best_model_path = best_model_dir / "best_model"
    if (best_model_dir / "best_model.zip").exists():
        best_env = NoisyCartPoleEnv(noise_dim=noise_dim)
        model = DQN.load(str(best_model_path), env=best_env)
        best_env.close()
    model.save(str(save_path))
    return model


def load_intuitive(noise_dim: int, load_path: Path) -> DQN:
    env = NoisyCartPoleEnv(noise_dim=noise_dim)
    model = DQN.load(str(load_path), env=env)
    return model


def evaluate_intuitive(model: DQN, noise_dim: int, n_episodes: int, seed: int) -> float:
    """平均エピソード報酬を返す。"""
    env = NoisyCartPoleEnv(noise_dim=noise_dim)
    mean_reward, _ = evaluate_policy(model, env, n_eval_episodes=n_episodes, deterministic=True)
    env.close()
    return float(mean_reward)


def collect_transitions(model: DQN, noise_dim: int, n_samples: int, seed: int) -> tuple:
    """Intuitive policy でロールアウトし、(obs, action) ペアを収集する。"""
    np.random.seed(seed)
    env = NoisyCartPoleEnv(noise_dim=noise_dim)
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
