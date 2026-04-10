"""評価指標の実装。

1. action_agreement: Intuitive と MoET の行動一致率
2. kl_divergence: Intuitive の行動分布と MoET の行動分布の KL divergence
3. relative_perf_drop: 相対性能低下 = (J_intuitive - J_reasoned) / J_intuitive
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from stable_baselines3 import DQN

from .moet import SoftMoET
from .env import NoisyCartPoleEnv


def action_agreement(
    obs: np.ndarray,
    intuitive_actions: np.ndarray,
    moet: SoftMoET,
) -> float:
    """行動一致率を返す。"""
    moet_actions = moet.predict(obs)
    return float(np.mean(intuitive_actions == moet_actions))


def kl_divergence(
    obs: np.ndarray,
    model: DQN,
    moet: SoftMoET,
    n_actions: int,
) -> float:
    """Intuitive の経験的行動分布と MoET の経験的行動分布の KL divergence を返す。

    KL(P_intuitive || P_moet) の経験的推定。
    """
    intuitive_actions, _ = model.predict(obs, deterministic=True)
    moet_actions = moet.predict(obs)

    eps = 1e-8
    p = np.bincount(intuitive_actions, minlength=n_actions).astype(float)
    q = np.bincount(moet_actions, minlength=n_actions).astype(float)
    p = (p + eps) / (p + eps).sum()
    q = (q + eps) / (q + eps).sum()
    return float(np.sum(p * np.log(p / q)))


def evaluate_rollout(agent, env: gym.Env, n_episodes: int, seed: int) -> float:
    """エージェント（DQN または SoftMoET）のロールアウト平均報酬を返す。"""
    total_reward = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            if isinstance(agent, DQN):
                action, _ = agent.predict(obs, deterministic=True)
                action = int(action)
            else:
                action = int(agent.predict(obs[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            done = terminated or truncated
    return total_reward / n_episodes


def relative_perf_drop(
    j_intuitive: float,
    j_reasoned: float,
) -> float:
    """相対性能低下を返す。0 に近いほど良い。"""
    if j_intuitive == 0:
        return 0.0
    return (j_intuitive - j_reasoned) / j_intuitive
