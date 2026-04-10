"""Intuitive policy → MoET の蒸留（behavioral cloning）。

学習手順:
1. 全専門家を Intuitive の行動で初期フィット
2. ゲーティングパラメータを交差エントロピーで最適化
3. 専門家をゲート重みで重み付けしたサンプルで再フィット（EM風の反復）
"""

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
    """Intuitive の (obs, action) から MoET を蒸留する。

    Parameters
    ----------
    moet : SoftMoET
        未学習の MoET インスタンス
    obs : np.ndarray, shape (n_samples, input_dim)
    actions : np.ndarray, shape (n_samples,)  int ラベル
    epochs : int
        ゲーティング最適化の epoch 数
    lr : float
        ゲーティング学習率

    Returns
    -------
    SoftMoET
        学習済み MoET
    """
    # Step 1: 全専門家を初期フィット
    moet.fit_experts(obs, actions)

    optimizer = optim.Adam(moet.gating_params(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    x_t = torch.tensor(obs, dtype=torch.float32)
    y_t = torch.tensor(actions, dtype=torch.long)

    for epoch in range(epochs):
        optimizer.zero_grad()

        # soft gating weights: (n_samples, n_experts)
        gates = moet.gating(x_t)

        # 各専門家の log-prob
        expert_probas = moet.expert_proba(obs)  # (n_experts, n_samples, n_actions)
        expert_probas_t = torch.tensor(
            expert_probas.transpose(1, 0, 2), dtype=torch.float32
        )  # (n_samples, n_experts, n_actions)

        # 重み付き混合確率
        gates_exp = gates.unsqueeze(-1)  # (n_samples, n_experts, 1)
        mixed_proba = (gates_exp * expert_probas_t).sum(dim=1)  # (n_samples, n_actions)
        mixed_proba = mixed_proba.clamp(min=1e-8)

        loss = criterion(mixed_proba.log(), y_t)
        loss.backward()
        optimizer.step()

        # Step 3 (EM風): ゲート重みで重み付けして専門家を再フィット（5 epochごと）
        if (epoch + 1) % 20 == 0:
            with torch.no_grad():
                gates_np = moet.gating(x_t).numpy()  # (n_samples, n_experts)
            for k, expert in enumerate(moet.experts):
                weights = gates_np[:, k]
                # weights が小さすぎる場合はスキップ
                if weights.sum() < 1.0:
                    continue
                expert.fit(obs, actions, sample_weight=weights)

    return moet
