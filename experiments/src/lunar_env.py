"""LunarLander-v3 環境ユーティリティ。

(c) オプション: 離散行動・連続力学の環境として MuJoCo 不要で使える。
重力パラメータを変えることで分布シフトを実現する。
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym

N_OBS = 8
N_ACTIONS = 4
DEFAULT_GRAVITY = -10.0

GRAVITY_CONDITIONS = {
    "train": DEFAULT_GRAVITY,
    "gravity_lo": -5.0,
    "gravity_hi": -20.0,
}


def make_env(gravity: float = DEFAULT_GRAVITY) -> gym.Env:
    return gym.make("LunarLander-v3", gravity=gravity)


def collect_transitions(
    model,
    gravity: float,
    n_samples: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """指定重力の LunarLander でロールアウトし (obs, action) を収集する。"""
    env = make_env(gravity=gravity)
    obs_list, act_list = [], []
    rng = np.random.default_rng(seed)
    obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    while len(obs_list) < n_samples:
        action, _ = model.predict(obs, deterministic=True)
        obs_list.append(obs.copy())
        act_list.append(int(action))
        obs, _, terminated, truncated, _ = env.step(int(action))
        if terminated or truncated:
            obs, _ = env.reset(seed=int(rng.integers(1_000_000)))
    env.close()
    return (
        np.array(obs_list[:n_samples], dtype=np.float32),
        np.array(act_list[:n_samples], dtype=np.int64),
    )


def evaluate_intuitive(
    model,
    gravity: float,
    n_episodes: int,
    seed: int,
) -> float:
    """DQN モデルの LunarLander 平均累積報酬を返す。"""
    env = make_env(gravity=gravity)
    total = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(int(action))
            total += reward
            done = terminated or truncated
    env.close()
    return total / n_episodes
