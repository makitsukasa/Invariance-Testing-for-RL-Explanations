from pathlib import Path

import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy

from .cartpole_env import NoisyCartPoleEnv


def train_intuitive(noise_dim: int, n_steps: int, seed: int, save_path: Path) -> DQN:
    """DQN を学習して保存し、モデルを返す。"""
    env = NoisyCartPoleEnv(noise_dim=noise_dim)
    model = DQN(
        "MlpPolicy",
        env,
        seed=seed,
        verbose=0,
    )
    model.learn(total_timesteps=n_steps)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(save_path))
    env.close()
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
