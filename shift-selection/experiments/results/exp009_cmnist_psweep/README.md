# exp009 — ColoredMNIST p sweep（ラベルノイズなし）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp009_cmnist_psweep.yaml` |
| script | `experiments/run_cmnist_psweep.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| p_values | 0.0, 0.1, 0.2, 0.3 |
| label_noise_p | 0.0（ラベルノイズなし） |
| Stage 2 test | spurious_p=1.0 |

**目的:** exp005（GridWorld p sweep）の ColoredMNIST 版。p によって検出率がどう変化するかを測定。

**結果:**

| p | AA>=0.9 | detect | Stage2 | e2e |
|---|---------|--------|--------|-----|
| 0.0 | 5/5 | 5/5 | 5/5 | 5/5 |
| 0.1 | 5/5 | 0/5 | 0/5 | 0/5 |
| 0.2 | 5/5 | 0/5 | 0/5 | 0/5 |
| 0.3 | 5/5 | 0/5 | 0/5 | 0/5 |

**失敗原因（p > 0.0）:**
p=0.0 以外で oracle が color を shortcut として使わず、digit structure（真の特徴）を学習する。
binary MNIST の構造分類は精度 99%+ で達成できるため、90% 止まりの color shortcut より structure の方が得になる。
→ p > 0 では「oracle が c に依存する」前提条件が成立しない。

→ exp010 で IRM 設定（label_noise_p=0.25 でラベルを 25% フリップし structure の精度上限を 75% に制限）を試みる。
