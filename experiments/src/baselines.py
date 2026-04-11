"""SoftMoET と同じインタフェースを持つベースライン Reasoned model。

- LinearReasonedModel: sklearn LogisticRegression
- SingleTreeReasonedModel: sklearn DecisionTreeClassifier (単一木)

どちらも .predict(obs) / .predict_proba(obs) を実装しており、
evaluate.py の action_agreement / kl_divergence / evaluate_rollout で
そのまま利用できる。
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


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
