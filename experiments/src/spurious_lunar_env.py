"""SpuriousLunarLander v2.

LunarLander-v3 に2ゾーン着地タスクを乗せた環境 (exp007〜用)。

v1 からの変更:
- 差分 shaping 除去 (oracle が c に依存するよう強制しない)
- zone_bonus: 軟着陸成功 → +bonus, 失敗 → -bonus のみ
- c_mode: "correlated" | "random" | "dummy"  (dummy = c=0.5 固定、全条件で同次元を保証)
- weak_signal: "vx_nudge" | "z_weak"  (ベース obs から zone を弱く推定可能にする)

次元数:
- vx_nudge: 9 dim (8 base + c)
- z_weak  : 10 dim (8 base + z_weak + c)
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

N_ACTIONS = 4

_BASE_NAMES = ["x", "y", "vx", "vy", "angle", "ang_vel", "leg_L", "leg_R"]

# vx_nudge (default): obs[2] の normalization factor  (vel.x / 5 in gymnasium source)
_VX_OBS_TO_PHYSICS = 5.0


class SpuriousLunarLander(gym.Wrapper):
    """LunarLander-v3 + zone bonus + spurious feature c.

    Parameters
    ----------
    spurious_p : float
        Noise rate for c (only effective when c_mode="correlated").
    c_mode : str
        "correlated" : c = target_zone XOR Bernoulli(spurious_p)
        "random"     : c ~ Uniform({0,1}) each episode
        "dummy"      : c = 0.5 (fixed, no zone info)
    weak_signal : str
        "vx_nudge" : add zone-correlated bias to obs[2] at reset
        "z_weak"   : add noisy zone feature z_weak as explicit obs dim
        "none"      : no weak signal (zones indistinguishable without c)
    zone_bonus : float
        +bonus for correct zone landing, -bonus for wrong (at terminal soft-landing).
    vx_nudge_scale : float
        Magnitude of obs[2] bias for vx_nudge (obs-space units, ~0.1-0.5).
    z_weak_noise_std : float
        Std of Gaussian noise added to zone indicator for z_weak feature.
    eval_mode : str | None
        None      : normal
        "reversed": c is flipped (1-c); tests Stage 2 collapse
        "random"  : c is random
    """

    def __init__(
        self,
        spurious_p: float = 0.0,
        c_mode: str = "correlated",
        weak_signal: str = "vx_nudge",
        zone_bonus: float = 200.0,
        vx_nudge_scale: float = 0.25,
        z_weak_noise_std: float = 1.0,
        eval_mode: str | None = None,
    ):
        env = gym.make("LunarLander-v3")
        super().__init__(env)
        self.spurious_p = spurious_p
        self.c_mode = c_mode
        self.weak_signal = weak_signal
        self.zone_bonus = zone_bonus
        self.vx_nudge_scale = vx_nudge_scale
        self.z_weak_noise_std = z_weak_noise_std
        self.eval_mode = eval_mode

        n_extra = 2 if weak_signal == "z_weak" else 1
        n_obs = 8 + n_extra
        low  = np.concatenate([env.observation_space.low,  np.full(n_extra, -3.0)]).astype(np.float32)
        high = np.concatenate([env.observation_space.high, np.full(n_extra,  3.0)]).astype(np.float32)
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        self.n_obs = n_obs
        self.spurious_idx = n_obs - 1  # c is always the last feature
        if weak_signal == "z_weak":
            self.feature_names = _BASE_NAMES + ["z_weak", "c (spurious)"]
        else:
            self.feature_names = _BASE_NAMES + ["c (spurious)"]

        self._target_zone: int = 0
        self._c: float = 0.5
        self._rng: np.random.Generator = np.random.default_rng(0)

    # ------------------------------------------------------------------
    def _make_c(self, target_zone: int) -> float:
        if self.c_mode == "dummy":
            return 0.5
        if self.c_mode == "random":
            return float(self._rng.integers(0, 2))
        # "correlated"
        noise = int(self._rng.random() < self.spurious_p)
        base_c = target_zone ^ noise
        if self.eval_mode == "reversed":
            return float(1 - base_c)
        if self.eval_mode == "random":
            return float(self._rng.integers(0, 2))
        return float(base_c)

    def _make_z_weak(self) -> float:
        raw = self._target_zone + self._rng.normal(0.0, self.z_weak_noise_std)
        return float(np.clip(raw, -3.0, 3.0))

    def _append_extra(self, obs: np.ndarray) -> np.ndarray:
        if self.weak_signal == "z_weak":
            extra = np.array([self._make_z_weak(), self._c], dtype=np.float32)
        else:
            extra = np.array([self._c], dtype=np.float32)
        return np.concatenate([obs, extra]).astype(np.float32)

    # ------------------------------------------------------------------
    def reset(self, *, seed: int | None = None, options=None):
        obs, info = self.env.reset(seed=seed, options=options)
        self._rng = np.random.default_rng(seed)

        self._target_zone = int(self._rng.integers(0, 2))
        self._c = self._make_c(self._target_zone)

        obs = obs.copy()

        if self.weak_signal == "vx_nudge":
            direction = 2 * self._target_zone - 1  # -1 or +1
            obs[2] += self.vx_nudge_scale * direction
            try:
                lander = self.env.unwrapped.lander
                delta_phys = self.vx_nudge_scale * _VX_OBS_TO_PHYSICS * direction
                vx, vy = float(lander.linearVelocity[0]), float(lander.linearVelocity[1])
                lander.linearVelocity = (vx + delta_phys, vy)
            except Exception:
                pass

        return self._append_extra(obs), info

    def step(self, action: int):
        obs, reward, terminated, truncated, info = self.env.step(action)

        if terminated and reward > 0:  # soft landing (+100 base)
            x = float(obs[0])
            correct = (self._target_zone == 0 and x < 0.0) or \
                      (self._target_zone == 1 and x >= 0.0)
            reward += self.zone_bonus if correct else -self.zone_bonus

        return self._append_extra(obs), reward, terminated, truncated, info
