"""Soft Mixture of Expert Trees (MoET)。

ゲーティング: PyTorch 線形層 → softmax。
専門家: scikit-learn DecisionTreeClassifier（深さ制限あり）。
推論: 各専門家の行動確率を soft weight で重み付き平均し argmax。
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
        for expert in self.experts:
            expert.fit(X, y)
        self._experts_fitted = True

    def expert_proba(self, X: np.ndarray) -> np.ndarray:
        """shape: (n_experts, n_samples, n_actions)"""
        probas = []
        for expert in self.experts:
            p = expert.predict_proba(X)
            full = np.zeros((len(X), self.n_actions), dtype=np.float32)
            for idx, cls in enumerate(expert.classes_):
                full[:, int(cls)] = p[:, idx]
            probas.append(full)
        return np.stack(probas, axis=0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        x_t = torch.tensor(X, dtype=torch.float32)
        with torch.no_grad():
            gates = self.gating(x_t).numpy()
        expert_probas = self.expert_proba(X)
        gates_exp = gates[:, :, np.newaxis]
        expert_probas_t = expert_probas.transpose(1, 0, 2)
        mixed = (gates_exp * expert_probas_t).sum(axis=1)
        return mixed

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.predict_proba(X).argmax(axis=1)

    def gating_params(self):
        return self.gating.parameters()
