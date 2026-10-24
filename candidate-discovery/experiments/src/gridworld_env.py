"""Spurious GridWorld used for candidate discovery smoke experiments.

Observation:
    (agent_x, agent_y, c, noise_0, ..., noise_{n-1})

`c` is a spurious binary cue correlated with the hidden goal identity.
The agent does not observe the goal directly, so a policy can easily latch onto `c`.
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

_GOALS = [(0, 0), (4, 4)]


class SpuriousGridWorld(gym.Env):
    """Small navigation task with a controllable spurious cue."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        spurious_p: float = 0.0,
        grid_size: int = 5,
        max_steps: int = 50,
        eval_mode: str | None = None,
        n_noise: int = 0,
    ) -> None:
        super().__init__()
        self.spurious_p = float(spurious_p)
        self.grid_size = int(grid_size)
        self.max_steps = int(max_steps)
        self.eval_mode = eval_mode
        self.n_noise = int(n_noise)

        n_obs = 3 + self.n_noise
        self.observation_space = spaces.Box(
            low=np.zeros(n_obs, dtype=np.float32),
            high=np.ones(n_obs, dtype=np.float32),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(4)
        self._rng = np.random.default_rng()

        self._agent_pos: tuple[int, int] = (0, 0)
        self._goal_pos: tuple[int, int] = _GOALS[0]
        self._goal_id: int = 0
        self._c: int = 0
        self._steps: int = 0

    def _make_c(self, goal_id: int) -> int:
        if self.eval_mode == "random":
            return int(self._rng.integers(0, 2))
        if self.eval_mode == "reversed":
            return 1 - goal_id
        noise = int(self._rng.random() < self.spurious_p)
        return goal_id ^ noise

    def _obs(self) -> np.ndarray:
        ax, ay = self._agent_pos
        base = [ax / (self.grid_size - 1), ay / (self.grid_size - 1), float(self._c)]
        noise = self._rng.uniform(0.0, 1.0, self.n_noise).tolist() if self.n_noise else []
        return np.array(base + noise, dtype=np.float32)

    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng = np.random.default_rng(seed)

        self._goal_id = int(self._rng.integers(0, len(_GOALS)))
        self._goal_pos = _GOALS[self._goal_id]
        self._c = self._make_c(self._goal_id)

        while True:
            ax = int(self._rng.integers(0, self.grid_size))
            ay = int(self._rng.integers(0, self.grid_size))
            if (ax, ay) != self._goal_pos:
                break

        self._agent_pos = (ax, ay)
        self._steps = 0
        return self._obs(), {}

    def step(self, action: int):
        ax, ay = self._agent_pos
        dx, dy = [(0, -1), (0, 1), (-1, 0), (1, 0)][int(action)]
        ax = int(np.clip(ax + dx, 0, self.grid_size - 1))
        ay = int(np.clip(ay + dy, 0, self.grid_size - 1))
        self._agent_pos = (ax, ay)
        self._steps += 1

        reached = (ax, ay) == self._goal_pos
        timeout = self._steps >= self.max_steps

        reward = 1.0 if reached else -0.01
        terminated = reached
        truncated = timeout and not reached
        return self._obs(), reward, terminated, truncated, {}
