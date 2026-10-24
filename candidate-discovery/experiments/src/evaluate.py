"""Evaluation helpers shared by gridworld experiments."""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from stable_baselines3.common.base_class import BaseAlgorithm


def action_agreement(obs: np.ndarray, oracle_actions: np.ndarray, surrogate) -> float:
    surrogate_actions = surrogate.predict(obs)
    return float(np.mean(oracle_actions == surrogate_actions))


def evaluate_rollout(agent, env: gym.Env, n_episodes: int, seed: int) -> float:
    total_reward = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            if isinstance(agent, BaseAlgorithm):
                action, _ = agent.predict(obs, deterministic=True)
                action = int(action)
            else:
                action = int(agent.predict(obs[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total_reward += reward
            done = terminated or truncated
    return total_reward / n_episodes
