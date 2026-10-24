"""Soft Mixture of Expert Trees (MoET)."""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from sklearn.tree import DecisionTreeClassifier


class SoftGating(nn.Module):
    def __init__(self, input_dim: int, n_experts: int) -> None:
        super().__init__()
        self.fc = nn.Linear(input_dim, n_experts)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.fc(x), dim=-1)


class SoftMoET:
    def __init__(self, input_dim: int, n_actions: int, n_experts: int, max_depth: int) -> None:
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.n_experts = n_experts
        self.max_depth = max_depth

        self.gating = SoftGating(input_dim, n_experts)
        self.experts: list[DecisionTreeClassifier] = [
            DecisionTreeClassifier(max_depth=max_depth) for _ in range(n_experts)
        ]

    def fit_experts(self, x: np.ndarray, y: np.ndarray) -> None:
        for expert in self.experts:
            expert.fit(x, y)

    def expert_proba(self, x: np.ndarray) -> np.ndarray:
        probas = []
        for expert in self.experts:
            p = expert.predict_proba(x)
            full = np.zeros((len(x), self.n_actions), dtype=np.float32)
            for idx, cls in enumerate(expert.classes_):
                full[:, int(cls)] = p[:, idx]
            probas.append(full)
        return np.stack(probas, axis=0)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        x_t = torch.tensor(x, dtype=torch.float32)
        with torch.no_grad():
            gates = self.gating(x_t).numpy()
        expert_probas = self.expert_proba(x)
        mixed = (gates[:, :, np.newaxis] * expert_probas.transpose(1, 0, 2)).sum(axis=1)
        return mixed

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.predict_proba(x).argmax(axis=1)

    def gating_params(self):
        return self.gating.parameters()
