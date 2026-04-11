"""重力パラメータを変更できる CartPole 環境。

NoisyCartPoleEnv と同じインタフェースを持つが、noise_dim=0 固定で
gravity を自由に設定できる。分布シフト実験（exp003）用。
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces


class GravityCartPoleEnv(gym.Env):
    """CartPole-v1 の重力パラメータを変更できる環境。

    N=0（ノイズなし）で訓練された Intuitive policy を
    異なる重力条件で評価するために使う。
    """

    metadata = {"render_modes": []}

    def __init__(self, gravity: float = 9.8):
        super().__init__()
        self.gravity = gravity
        self.base_env = gym.make("CartPole-v1")
        self.base_env.unwrapped.gravity = gravity

        self.observation_space = self.base_env.observation_space
        self.action_space = self.base_env.action_space

    def reset(self, *, seed=None, options=None):
        obs, info = self.base_env.reset(seed=seed, options=options)
        return obs.astype(np.float32), info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.base_env.step(action)
        return obs.astype(np.float32), reward, terminated, truncated, info

    def close(self):
        self.base_env.close()
