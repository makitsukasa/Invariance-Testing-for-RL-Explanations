"""Soft Mixture of Expert Trees (MoET) の実装。

ゲーティング: PyTorch の線形層 → softmax で各専門家への重みを計算。
専門家: scikit-learn の DecisionTreeClassifier（深さ制限あり）。

推論: 各専門家の行動確率を soft weight で重み付き平均し、argmax で行動を決定。
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from sklearn.tree import DecisionTreeClassifier


class SoftGating(nn.Module):
    def __init__(self, input_dim: int, n_experts: int):
        super().__init__()
        self.fc = nn.Linear(input_dim, n_experts)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.fc(x), dim=-1)


class SoftMoET:
    """Soft Mixture of Expert Trees。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間の次元）
    n_actions : int
        行動空間のサイズ
    n_experts : int
        専門家（決定木）の数
    max_depth : int
        各決定木の最大深さ
    """

    def __init__(self, input_dim: int, n_actions: int, n_experts: int, max_depth: int):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.n_experts = n_experts
        self.max_depth = max_depth

        self.gating = SoftGating(input_dim, n_experts)
        self.experts: list[DecisionTreeClassifier] = [
            DecisionTreeClassifier(max_depth=max_depth)
            for _ in range(n_experts)
        ]
        self._experts_fitted = False

    def fit_experts(self, X: np.ndarray, y: np.ndarray) -> None:
        """全専門家を同じデータで初期フィット（後でゲートで重み付けして再学習）。"""
        for expert in self.experts:
            expert.fit(X, y)
        self._experts_fitted = True

    def expert_proba(self, X: np.ndarray) -> np.ndarray:
        """各専門家の行動確率行列を返す。shape: (n_experts, n_samples, n_actions)"""
        probas = []
        for expert in self.experts:
            p = expert.predict_proba(X)
            # predict_proba は学習時に見たクラスしか列を持たないので n_actions に揃える
            full = np.zeros((len(X), self.n_actions), dtype=np.float32)
            for idx, cls in enumerate(expert.classes_):
                full[:, int(cls)] = p[:, idx]
            probas.append(full)
        return np.stack(probas, axis=0)  # (n_experts, n_samples, n_actions)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """soft gating + 専門家確率の重み付き平均を返す。shape: (n_samples, n_actions)"""
        x_t = torch.tensor(X, dtype=torch.float32)
        with torch.no_grad():
            gates = self.gating(x_t).numpy()  # (n_samples, n_experts)
        expert_probas = self.expert_proba(X)  # (n_experts, n_samples, n_actions)
        # 重み付き平均: gates を (n_samples, n_experts, 1) にして broadcast
        gates_exp = gates[:, :, np.newaxis]  # (n_samples, n_experts, 1)
        expert_probas_t = expert_probas.transpose(1, 0, 2)  # (n_samples, n_experts, n_actions)
        mixed = (gates_exp * expert_probas_t).sum(axis=1)  # (n_samples, n_actions)
        return mixed

    def predict(self, X: np.ndarray) -> np.ndarray:
        """行動を返す。shape: (n_samples,)"""
        return self.predict_proba(X).argmax(axis=1)

    def gating_params(self):
        return self.gating.parameters()
