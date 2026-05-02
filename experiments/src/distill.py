"""Oracle policy -> MoET distillation."""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from .moet import SoftMoET


def distill(
    moet: SoftMoET,
    obs: np.ndarray,
    actions: np.ndarray,
    epochs: int = 100,
    lr: float = 1e-2,
) -> SoftMoET:
    moet.fit_experts(obs, actions)

    optimizer = optim.Adam(moet.gating_params(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    x_t = torch.tensor(obs, dtype=torch.float32)
    y_t = torch.tensor(actions, dtype=torch.long)

    for epoch in range(epochs):
        optimizer.zero_grad()

        gates = moet.gating(x_t)
        expert_probas = moet.expert_proba(obs)
        expert_probas_t = torch.tensor(expert_probas.transpose(1, 0, 2), dtype=torch.float32)
        mixed_proba = (gates.unsqueeze(-1) * expert_probas_t).sum(dim=1).clamp(min=1e-8)

        loss = criterion(mixed_proba.log(), y_t)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 20 == 0:
            with torch.no_grad():
                gates_np = moet.gating(x_t).numpy()
            for k, expert in enumerate(moet.experts):
                weights = gates_np[:, k]
                if float(weights.sum()) < 1.0:
                    continue
                expert.fit(obs, actions, sample_weight=weights)

    return moet
