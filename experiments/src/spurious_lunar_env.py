"""SpuriousLunarLander: LunarLander-v3 に2ゾーン着地タスクを乗せた環境。

GridWorld の2ゴール構造のアナログ。

エピソードごとに target_zone ∈ {0, 1} をランダム選択:
  zone 0: x < 0 (左側) に着地するのが正解 → x_target = -X_TARGET_OFFSET
  zone 1: x >= 0 (右側) に着地するのが正解 → x_target = +X_TARGET_OFFSET

LunarLander の標準 shaping は -100*sqrt(x²+y²) で常に x=0 に引っ張る。
これを x_target を中心とした -100*sqrt((x-xt)²+y²) に差し替えることで、
shaping 全体がゾーン方向を向くようにする（Box2D 非改変）。

c = target_zone XOR Bernoulli(spurious_p) を obs の末尾に追加。

eval_mode:
  None     : 通常
  "reversed": c を反転（c = 1 - (target_zone XOR noise)）
  "random"  : c をランダム
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

N_BASE_OBS = 8
N_OBS = 9          # base 8 + c
N_ACTIONS = 4
SPURIOUS_IDX = 8
FEATURE_NAMES = ["x", "y", "vx", "vy", "angle", "ang_vel", "leg_L", "leg_R", "c (spurious)"]

X_TARGET_OFFSET = 0.3   # target_zone=0 → x_target=-0.3, zone=1 → x_target=+0.3
LANDING_ZONE_BONUS = 100.0  # 着地成功時の正解ゾーンボーナス（誤答はペナルティ）


class SpuriousLunarLander(gym.Wrapper):
    """LunarLander-v3 + ゾーン依存 shaping + スプリアス特徴 c。

    shaping の x 成分を zone 目標位置 x_target 基準に補正することで、
    報酬構造全体がゾーン方向に整合する。

    Parameters
    ----------
    spurious_p  : float  スプリアスノイズ率（0.0 = 完全相関）
    eval_mode   : str | None  None / "reversed" / "random"
    """

    def __init__(
        self,
        spurious_p: float = 0.0,
        eval_mode: str | None = None,
    ):
        env = gym.make("LunarLander-v3")
        super().__init__(env)
        self.spurious_p = spurious_p
        self.eval_mode = eval_mode

        low  = np.append(env.observation_space.low,  0.0).astype(np.float32)
        high = np.append(env.observation_space.high, 1.0).astype(np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self._target_zone: int = 0
        self._c: float = 0.0
        self._x_target: float = 0.0
        self._prev_x: float = 0.0
        self._prev_y: float = 0.0

    def _make_c(self, target_zone: int, rng: np.random.Generator) -> float:
        noise = int(rng.random() < self.spurious_p)
        base_c = target_zone ^ noise
        if self.eval_mode == "reversed":
            return float(1 - base_c)
        elif self.eval_mode == "random":
            return float(rng.integers(0, 2))
        return float(base_c)

    def reset(self, *, seed: int | None = None, options=None):
        obs, info = self.env.reset(seed=seed, options=options)
        rng = np.random.default_rng(seed)
        self._target_zone = int(rng.integers(0, 2))
        self._c = self._make_c(self._target_zone, rng)
        self._x_target = -X_TARGET_OFFSET if self._target_zone == 0 else X_TARGET_OFFSET
        self._prev_x = float(obs[0])
        self._prev_y = float(obs[1])
        return np.append(obs, self._c).astype(np.float32), info

    def step(self, action: int):
        obs, reward, terminated, truncated, info = self.env.step(action)
        x, y = float(obs[0]), float(obs[1])
        xt = self._x_target
        px, py = self._prev_x, self._prev_y

        if not terminated:
            # 標準 shaping の x 成分 (-100*sqrt(x²+y²)) を
            # ゾーン基準 (-100*sqrt((x-xt)²+y²)) に差し替える補正
            zone_now  = -100.0 * np.sqrt((x  - xt) ** 2 + y  ** 2)
            std_now   = -100.0 * np.sqrt( x  ** 2        + y  ** 2)
            zone_prev = -100.0 * np.sqrt((px - xt) ** 2 + py ** 2)
            std_prev  = -100.0 * np.sqrt( px ** 2        + py ** 2)
            reward += (zone_now - zone_prev) - (std_now - std_prev)
        elif reward > 0:   # 軟着陸 (+100)
            correct = (self._target_zone == 0 and x < 0.0) or \
                      (self._target_zone == 1 and x >= 0.0)
            reward += LANDING_ZONE_BONUS if correct else -LANDING_ZONE_BONUS

        self._prev_x = x
        self._prev_y = y
        return np.append(obs, self._c).astype(np.float32), reward, terminated, truncated, info
