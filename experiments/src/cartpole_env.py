import gymnasium as gym
import numpy as np
from gymnasium import spaces


class NoisyCartPoleEnv(gym.Env):
    """CartPole-v1 の状態にガウスノイズ特徴を追加した拡張環境。

    状態: s' = (s, η),  η ~ N(0, I_N)
    s は元の4次元状態、N は noise_dim で指定する追加次元数。
    """

    metadata = {"render_modes": []}

    def __init__(self, noise_dim: int = 0):
        super().__init__()
        self.base_env = gym.make("CartPole-v1")
        self.noise_dim = noise_dim
        total_dim = 4 + noise_dim

        high = np.concatenate([
            self.base_env.observation_space.high,
            np.full(noise_dim, np.inf),
        ])
        low = np.concatenate([
            self.base_env.observation_space.low,
            np.full(noise_dim, -np.inf),
        ])
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        self.action_space = self.base_env.action_space

    def _augment(self, obs: np.ndarray) -> np.ndarray:
        if self.noise_dim == 0:
            return obs.astype(np.float32)
        noise = np.random.randn(self.noise_dim).astype(np.float32)
        return np.concatenate([obs, noise]).astype(np.float32)

    def reset(self, *, seed=None, options=None):
        obs, info = self.base_env.reset(seed=seed, options=options)
        return self._augment(obs), info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.base_env.step(action)
        return self._augment(obs), reward, terminated, truncated, info

    def close(self):
        self.base_env.close()
