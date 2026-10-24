# exp002 — Per-feature 介入テスト 自動選択パイロット（SpuriousGridWorld）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp002_intervention_gridworld.yaml` |
| script | `experiments/run_intervention_pilot.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps, spurious_p=0.0 |

**目的:** SHAP（exp001: 60%）の代替として、各特徴を摂動したロールアウトで J_S 降下量を直接測定し、最大降下特徴をスプリアス候補として自動選択する。

**アルゴリズム:**
1. 各特徴 f を**全て uniform random [0,1]** で摂動しながらサロゲートをロールアウト（特徴型の事前知識なし）
2. Δ_f = J_S_train - J_S_f_perturbed を計算
3. Δ が最大の特徴をスプリアス候補として選択

**結果:**
- Stage 1 (AA >= 0.9): 100% (5/5)
- 介入テストによる c 選択: **100% (5/5)**
- 平均 Δ: x=-0.215, y=-0.091, **c=+0.511**

SHAP 60% → 介入テスト 100%。x/y の摂動は報酬をほぼ維持するが、c のランダム化は一貫して降下する。
