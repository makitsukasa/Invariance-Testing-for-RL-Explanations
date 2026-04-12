"""MuJoCo Hopper-v5 + 行動ビニング環境ユーティリティ。

(a) オプション: 連続行動を bins_per_dim^3 の離散クラスにビニングし、
既存の分類器ベース Reasoned model をそのまま適用できるようにする。

行動ビニング方式:
  - Hopper の行動空間: Box(3,) in [-1, 1]^3 (3関節のトルク)
  - 各次元を bins_per_dim 個の等幅 bin に分割
  - 離散行動インデックス = d0 * B^2 + d1 * B + d2
  - n_actions = bins_per_dim^3 (デフォルト: 3^3 = 27)
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym

ACTION_DIM = 3
DEFAULT_BINS_PER_DIM = 3
DEFAULT_GRAVITY = -9.81

GRAVITY_CONDITIONS = {
    "train": DEFAULT_GRAVITY,
    "gravity_lo": -5.0,
    "gravity_hi": -20.0,
}


class BinnedHopperEnv(gym.Env):
    """Hopper-v5 ラッパー: Reasoned model 向け離散行動インタフェースを提供する。

    step(discrete_action) を受け取り、対応するビン中心の連続行動に変換して
    MuJoCo エンジンに渡す。Intuitive policy (SAC) の学習には使わず、
    Reasoned model のロールアウト評価専用。
    """

    def __init__(self, gravity: float | None = None, bins_per_dim: int = DEFAULT_BINS_PER_DIM):
        super().__init__()
        self._gravity = gravity
        self.bins_per_dim = bins_per_dim
        self.n_actions = bins_per_dim ** ACTION_DIM

        self._base = gym.make("Hopper-v5")
        self.observation_space = self._base.observation_space
        self.action_space = gym.spaces.Discrete(self.n_actions)

        # ビン境界とビン中心
        self._edges = np.linspace(-1.0, 1.0, bins_per_dim + 1)
        self._centers = (self._edges[:-1] + self._edges[1:]) / 2.0

        # discrete_action → (b0, b1, b2) のルックアップテーブル
        self._combos = np.array(
            np.unravel_index(np.arange(self.n_actions), (bins_per_dim,) * ACTION_DIM)
        ).T  # shape: (n_actions, ACTION_DIM)

    def _apply_gravity(self) -> None:
        if self._gravity is not None:
            self._base.unwrapped.model.opt.gravity[2] = self._gravity

    def reset(self, **kwargs):
        obs, info = self._base.reset(**kwargs)
        self._apply_gravity()
        return obs, info

    def step(self, discrete_action: int):
        continuous_action = self._centers[self._combos[int(discrete_action)]].astype(np.float32)
        return self._base.step(continuous_action)

    def close(self):
        self._base.close()

    def render(self):
        return self._base.render()

    # ---- ユーティリティ ----

    def bin_continuous(self, continuous_action: np.ndarray) -> int:
        """連続行動ベクトルを離散行動インデックスに変換する。"""
        idx = 0
        for d in range(ACTION_DIM):
            b = int(np.clip(np.digitize(continuous_action[d], self._edges[1:-1]), 0, self.bins_per_dim - 1))
            idx = idx * self.bins_per_dim + b
        return idx


# ---------------------------------------------------------------------------
# データ収集・評価ユーティリティ
# ---------------------------------------------------------------------------

def collect_transitions(
    sac_model,
    n_samples: int,
    seed: int,
    bins_per_dim: int = DEFAULT_BINS_PER_DIM,
) -> tuple[np.ndarray, np.ndarray]:
    """SAC モデルのロールアウトから (obs, binned_action) を収集する。

    蒸留用データ: Intuitive policy (SAC) の連続行動をビニングして
    Reasoned model の教師ラベルとして使う。
    """
    binner = BinnedHopperEnv(bins_per_dim=bins_per_dim)
    raw_env = gym.make("Hopper-v5")
    obs_list, act_list = [], []
    rng = np.random.default_rng(seed)
    obs, _ = raw_env.reset(seed=int(rng.integers(1_000_000)))
    while len(obs_list) < n_samples:
        cont_action, _ = sac_model.predict(obs, deterministic=True)
        binned = binner.bin_continuous(cont_action)
        obs_list.append(obs.copy())
        act_list.append(binned)
        obs, _, terminated, truncated, _ = raw_env.step(cont_action)
        if terminated or truncated:
            obs, _ = raw_env.reset(seed=int(rng.integers(1_000_000)))
    raw_env.close()
    binner.close()
    return (
        np.array(obs_list[:n_samples], dtype=np.float32),
        np.array(act_list[:n_samples], dtype=np.int64),
    )


def evaluate_intuitive(
    sac_model,
    gravity: float,
    n_episodes: int,
    seed: int,
) -> float:
    """SAC モデルの Hopper 平均累積報酬を返す（連続行動で評価）。"""
    env = gym.make("Hopper-v5")
    env.reset()
    env.unwrapped.model.opt.gravity[2] = gravity
    total = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        env.unwrapped.model.opt.gravity[2] = gravity
        done = False
        while not done:
            action, _ = sac_model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            total += reward
            done = terminated or truncated
    env.close()
    return total / n_episodes


def evaluate_reasoned(
    rm,
    gravity: float,
    n_episodes: int,
    seed: int,
    bins_per_dim: int = DEFAULT_BINS_PER_DIM,
) -> float:
    """Reasoned model の BinnedHopperEnv ロールアウト平均累積報酬を返す。"""
    env = BinnedHopperEnv(gravity=gravity, bins_per_dim=bins_per_dim)
    total = 0.0
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False
        while not done:
            action = int(rm.predict(obs[np.newaxis])[0])
            obs, reward, terminated, truncated, _ = env.step(action)
            total += reward
            done = terminated or truncated
    env.close()
    return total / n_episodes
