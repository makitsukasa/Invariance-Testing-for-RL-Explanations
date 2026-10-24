# exp010 — ColoredMNIST IRM 設定 p sweep

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp010_cmnist_irm_psweep.yaml` |
| script | `experiments/run_cmnist_psweep.py exp010_cmnist_irm_psweep.yaml` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| p_values | 0.0, 0.1, 0.2, 0.3 |
| label_noise_p | 0.25（ラベルを 25% フリップ → structure 精度上限 ≈ 75%） |
| Stage 2 test | spurious_p=1.0 |

**目的:** exp009 の失敗を受け、IRM 論文設定（label_noise_p=0.25）で oracle に color shortcut を取らせる。
color accuracy (1-spurious_p) > structure accuracy (75%) の条件を維持しながら p を sweep する。

**期待値：** color accuracy > structure accuracy のとき oracle が color を使う。
- p=0.0: color=100% > 75% → ○
- p=0.1: color=90% > 75% → ○
- p=0.2: color=80% ≈ 75% → 境界、不安定
- p=0.3: color=70% < 75% → oracle が structure に切り替え → ×

**結果:**

| p | AA>=0.9 | detect | Stage2 | e2e | mean_AA | mean_J_oracle |
|---|---------|--------|--------|-----|---------|---------------|
| 0.0 | 5/5 | 5/5 | 5/5 | 5/5 | 1.000 | 1.000 |
| 0.1 | 5/5 | 5/5 | 5/5 | 5/5 | 0.999 | 0.901 |
| 0.2 | 5/5 | 4/5 | 5/5 | 4/5 | 0.965 | 0.790 |
| 0.3 | 5/5 | 4/5 | 4/5 | 3/5 | 0.947 | 0.735 |

**観察:**
- GridWorld exp005 と同様の gradual degradation が再現された
- p=0.2 は crossover 付近（color 80% vs structure 75%）で検出がぶれ始める（4/5）
- p=0.3 は color が structure を下回り、oracle が color を使わなくなる（3/5）
- Stage 2 は detect より安定して崩壊：誤選択でも c は依然 oracle に使われている場合がある

**exp005 GridWorld との比較:**

| p | GridWorld e2e | ColoredMNIST IRM e2e |
|---|--------------|---------------------|
| 0.0 | 5/5 | 5/5 |
| 0.1 | 5/5 | 5/5 |
| 0.2 | 5/5 | 4/5 |
| 0.3 | 1/5 | 3/5 |
