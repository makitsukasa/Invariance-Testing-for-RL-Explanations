"""Spurious GridWorld 環境。

状態: (agent_x, agent_y, c) — ゴール位置は隠蔽
c = goal_id XOR Bernoulli(p)  でスプリアス相関を制御

ゴールは2択（左上 or 右下）でエピソードごとにランダム選択。
エージェントは c からゴールを推測するしかないため、
p=0 のとき c に強依存した policy が学習される。

eval_mode:
  None     : 通常（train 分布）
  "random" : c をランダム化（スプリアス除去）
  "reversed": c を反転（相関反転）
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

# ゴール候補（左上・右下）
_GOALS = [(0, 0), (4, 4)]


class SpuriousGridWorld(gym.Env):
    """5×5 グリッドのナビゲーションタスク。

    Parameters
    ----------
    spurious_p : float
        スプリアスノイズ率（0.0 = 完全相関, 0.5 = 無関係）
    grid_size : int
        グリッドサイズ（デフォルト 5）
    max_steps : int
        1エピソードの最大ステップ数
    eval_mode : str or None
        None: 通常, "random": c をランダム化, "reversed": c を反転
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        spurious_p: float = 0.0,
        grid_size: int = 5,
        max_steps: int = 100,
        eval_mode: str | None = None,
    ):
        super().__init__()
        self.spurious_p = spurious_p
        self.grid_size = grid_size
        self.max_steps = max_steps
        self.eval_mode = eval_mode

        # 状態: (agent_x, agent_y, c) を [0, 1] に正規化
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0], dtype=np.float32),
        )
        # 行動: 0=上, 1=下, 2=左, 3=右
        self.action_space = spaces.Discrete(4)

        self._agent_pos: tuple[int, int] = (0, 0)
        self._goal_pos: tuple[int, int] = _GOALS[0]
        self._goal_id: int = 0
        self._c: int = 0
        self._steps: int = 0

    # ------------------------------------------------------------------
    def _make_c(self, goal_id: int) -> int:
        if self.eval_mode == "random":
            return int(np.random.randint(0, 2))
        elif self.eval_mode == "reversed":
            return 1 - goal_id
        else:
            # train: c = goal_id XOR Bernoulli(p)
            noise = int(np.random.random() < self.spurious_p)
            return goal_id ^ noise

    def _obs(self) -> np.ndarray:
        ax, ay = self._agent_pos
        return np.array(
            [ax / (self.grid_size - 1), ay / (self.grid_size - 1), float(self._c)],
            dtype=np.float32,
        )

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            np.random.seed(seed)

        # ゴールをランダム選択
        self._goal_id = int(np.random.randint(0, len(_GOALS)))
        self._goal_pos = _GOALS[self._goal_id]

        # スプリアス特徴を生成
        self._c = self._make_c(self._goal_id)

        # エージェントはゴール以外のセルにランダム配置
        while True:
            ax = int(np.random.randint(0, self.grid_size))
            ay = int(np.random.randint(0, self.grid_size))
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
