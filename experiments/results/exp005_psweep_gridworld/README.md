# exp005 — spurious_p sweep + end-to-end パイプライン実証

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp005_psweep_gridworld.yaml` |
| script | `experiments/run_gridworld_psweep.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| p_values | 0.0, 0.1, 0.2, 0.3 |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps |
| obs | (x, y, c, noise×7) = 10次元 |

**目的:**
- Q1. spurious_p が上がるほど検出率はどう落ちるか（ロバスト性）
- Q2. 介入テストで c を選択できたとき、Stage 2 も崩壊するか（end-to-end 実証）

**結果:**

| p | AA>=0.9 | detect c | Stage 2 collapse | e2e |
|---|---------|----------|-----------------|-----|
| 0.0 | 100% | 100% | 100% | 100% |
| 0.1 |  80% | 100% | 100% | 100% |
| 0.2 |  20% | 100% | 100% | 100% |
| 0.3 |   0% |  20% |  80% |  20% |

**観察:**
- p ≤ 0.2 では介入テスト・Stage 2 ともに 100% 成功（end-to-end 完全）
- p=0.2 で AA が 20% に落ちるが、介入テストはなお 100% 正確：サロゲートの蒸留品質が低くても検出が機能することを示す
- p=0.3 でオラクルが c を使う強さが閾値を下回り、検出・e2e ともに崩壊
- Stage 2 collapse は常に c 反転でテストしているため、誤選択時でも「c はまだ使われている」なら collapse=True になりうる点に注意
