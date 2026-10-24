# exp004 — GridWorld + ノイズ特徴 10 次元（スケール確認）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp004_noise_gridworld.yaml` |
| script | `experiments/run_gridworld_noise.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps, spurious_p=0.0 |

**目的:** exp002（3特徴）と同一アルゴリズムを obs=(x, y, c, noise×7) の10次元に拡張し、特徴数を増やしても c を正しく選択できるかを確認する。ノイズ特徴は毎ステップ i.i.d. uniform [0,1]。

**結果:**
- Stage 1 (AA >= 0.9): 100% (5/5)
- 介入テストによる c 選択: **100% (5/5)**
- 平均 Δ: x=0.032, y=0.041, **c=0.529**, noise_0〜6≈0.000
