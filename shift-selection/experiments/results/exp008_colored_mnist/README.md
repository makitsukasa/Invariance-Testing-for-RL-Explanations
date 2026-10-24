# exp008 — ColoredMNIST + CNN surrogate（基本動作確認）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp008_colored_mnist.yaml` |
| script | `experiments/run_colored_mnist.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| oracle | CNN（Conv×2 + FC×2）、10 epochs、ColoredMNIST spurious_p=0.0 |
| surrogate | CNN（同構造）、oracle 予測ラベルで 10 epochs 蒸留 |
| label_noise_p | 0.0（ラベルノイズなし） |
| spurious_p | 0.0（color が class と完全相関） |
| Stage 2 test | spurious_p=1.0（color が完全反転） |

**目的:** 非 RL・画像分類環境で介入テストが機能するかを確認。GridWorld exp002 の ColoredMNIST 版。

**結果:**

| 指標 | 値 |
|------|-----|
| Stage 1 pass (AA ≥ 0.9) | 5/5 |
| 介入テスト（hue 選択） | 5/5 |
| Stage 2 collapse | 5/5 |
| mean AA | 1.000 |
| mean J_oracle | 1.000 |
| mean Δ_hue | 0.500 |
| mean Δ_struct | 0.000 |

**観察:**
- spurious_p=0.0 では oracle が color shortcut を完全習得（J_oracle=1.000）
- surrogate も AA=1.000 で完全蒸留
- hue_shuffle で精度が半減（Δ_hue≈0.5）、structure_noise は無影響（Δ_struct≈0）
- Stage 2 では J_S=0.000（完全崩壊）：色反転で surrogate が全問不正解
