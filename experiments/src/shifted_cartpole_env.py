"""物理パラメータ（重力・ポール長）を変更できる CartPole 環境。

分布シフト実験（exp003）用。N=0 固定。
"""

import gymnasium as gym
import numpy as np


class ShiftedCartPoleEnv(gym.Env):
    """CartPole-v1 の重力とポール長を任意に設定できる環境。

    Parameters
    ----------
    gravity : float
        重力加速度（デフォルト 9.8）
    pole_length : float
        ポールの半長（デフォルト 0.5）
    """

    metadata = {"render_modes": []}

    def __init__(self, gravity: float = 9.8, pole_length: float = 0.5):
        super().__init__()
        self.base_env = gym.make("CartPole-v1")
        env = self.base_env.unwrapped
        env.gravity = gravity
        env.length = pole_length
        env.polemass_length = env.masspole * pole_length

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
