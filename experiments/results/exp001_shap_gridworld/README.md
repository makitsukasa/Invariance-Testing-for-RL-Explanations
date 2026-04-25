# exp001 — SHAP シフト自動選択パイロット（SpuriousGridWorld）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp001_shap_gridworld.yaml` |
| script | `experiments/run_shap_pilot.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps, spurious_p=0.0 |

**目的:** SHAP → シフト候補自動選択 → 前論文 Stage 2 評価のパイプラインが一周回るかを確認する最小実験。

**確認する問い:**
- Q1. SHAP は c（スプリアス特徴）を上位に出すか
- Q2. c をシフトしたとき Stage 2 で J_S 崩壊を検出できるか
- Q3. 非スプリアス特徴（x, y）のシフトでは崩壊しないか（対照）

**結果:**
- Stage 1 (AA >= 0.9): 100% (5/5)
- SHAP による c 選択: **60% (3/5)**
- Stage 2 崩壊検出（c シフト時）: 100% (5/5)

**前論文との関係:** 前論文 exp002（Spurious GridWorld）の評価枠組みを流用。前論文では d=5 で AA=0.988±0.011 を達成しており、本実験でも同条件を採用。SHAP が 60% 止まりだったことが介入テスト（exp002）の動機。
