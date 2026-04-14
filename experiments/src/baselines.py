"""SoftMoET と同じインタフェースを持つベースライン Reasoned model。

- LinearReasonedModel: sklearn LogisticRegression
- SingleTreeReasonedModel: sklearn DecisionTreeClassifier (単一木)
- GBTReasonedModel: sklearn HistGradientBoostingClassifier (勾配ブースティング木)

どちらも .predict(obs) / .predict_proba(obs) を実装しており、
evaluate.py の action_agreement / kl_divergence / evaluate_rollout で
そのまま利用できる。
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import HistGradientBoostingClassifier


class LinearReasonedModel:
    """ロジスティック回帰による Reasoned model。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    n_actions : int
        行動空間のサイズ
    C : float
        正則化の逆強度（デフォルト 1.0）
    """

    def __init__(self, input_dim: int, n_actions: int, C: float = 1.0):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.model = LogisticRegression(max_iter=2000, C=C, solver="lbfgs")
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples,)"""
        return self.predict_proba(obs).argmax(axis=1)


class SingleTreeReasonedModel:
    """単一決定木による Reasoned model。

    Parameters
    ----------
    input_dim : int
        入力次元数
    n_actions : int
        行動空間のサイズ
    max_depth : int
        決定木の最大深さ
    """

    def __init__(self, input_dim: int, n_actions: int, max_depth: int = 5):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.max_depth = max_depth
        self.model = DecisionTreeClassifier(max_depth=max_depth)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SingleTreeReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples,)"""
        return self.predict_proba(obs).argmax(axis=1)


class RegressionTreeModel:
    """多出力決定木回帰による Reasoned model（連続行動空間用）。

    DecisionTreeRegressor を使用し、連続行動ベクトルを直接予測する。
    binning 不要で、Hopper 等の連続制御タスクに適用できる。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    action_dim : int
        行動空間の次元数（例: Hopper は 3）
    max_depth : int
        決定木の最大深さ
    """

    def __init__(self, input_dim: int, action_dim: int, max_depth: int = 5):
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.max_depth = max_depth
        self.model = DecisionTreeRegressor(max_depth=max_depth)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RegressionTreeModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, action_dim)"""
        pred = self.model.predict(obs)
        if pred.ndim == 1:
            pred = pred[:, np.newaxis]
        return np.clip(pred, -1.0, 1.0).astype(np.float32)


class RegressionLinearModel:
    """多出力線形回帰による Reasoned model（連続行動空間用）。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    action_dim : int
        行動空間の次元数
    """

    def __init__(self, input_dim: int, action_dim: int):
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.model = LinearRegression()
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RegressionLinearModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, action_dim)"""
        pred = self.model.predict(obs)
        if pred.ndim == 1:
            pred = pred[:, np.newaxis]
        return np.clip(pred, -1.0, 1.0).astype(np.float32)


class GBTReasonedModel:
    """勾配ブースティング木による Reasoned model。

    HistGradientBoostingClassifier を使用。MoET や単一決定木より高い再現性が
    期待される説明可能モデル。LunarLander のような連続力学系でも収束実績がある。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    n_actions : int
        行動空間のサイズ
    max_iter : int
        ブースティング反復数
    max_depth : int | None
        個々の決定木の最大深さ（None で無制限）
    learning_rate : float
        学習率
    """

    def __init__(
        self,
        input_dim: int,
        n_actions: int,
        max_iter: int = 200,
        max_depth: int | None = None,
        learning_rate: float = 0.1,
    ):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.model = HistGradientBoostingClassifier(
            max_iter=max_iter,
            max_depth=max_depth,
            learning_rate=learning_rate,
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GBTReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples,)"""
        return self.predict_proba(obs).argmax(axis=1)
