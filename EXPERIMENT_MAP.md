# EXPERIMENT_MAP.md

実験 ID とディレクトリの対応表。新しい実験を追加したら必ずここを更新する。

---

## 実験一覧

### exp001 — SHAP シフト自動選択パイロット（SpuriousGridWorld）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp001_shap_gridworld.yaml` |
| script | `experiments/run_shap_pilot.py` |
| results | `experiments/results/exp001_shap_gridworld/` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps, spurious_p=0.0 |

**目的:** SHAP → シフト候補自動選択 → 前論文 Stage 2 評価のパイプラインが一周回るかを確認する最小実験。

**確認する問い:**
- Q1. SHAP は c（スプリアス特徴）を上位に出すか
- Q2. c をシフトしたとき Stage 2 で J_S 崩壊を検出できるか
- Q3. 非スプリアス特徴（x, y）のシフトでは崩壊しないか（対照）

**前論文との関係:** 前論文 exp002（Spurious GridWorld）の評価枠組みを流用。前論文では d=5 で AA=0.988±0.011 (train) を達成しており、本実験でも同条件を採用。

---

### exp002 — Per-feature 介入テスト 自動選択パイロット（SpuriousGridWorld）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp002_intervention_gridworld.yaml` |
| script | `experiments/run_intervention_pilot.py` |
| results | `experiments/results/exp002_intervention_gridworld/` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps, spurious_p=0.0 |

**目的:** SHAP（exp001: 60%）の代替として、各特徴を摂動したロールアウトで J_S 降下量を直接測定し、最大降下特徴をスプリアス候補として自動選択する。検出率が SHAP を上回るかを確認する。

**アルゴリズム:**
1. 各特徴 f を摂動しながらサロゲートをロールアウト（x/y: ランダム、c: 反転）
2. Δ_f = J_S_train - J_S_f_perturbed を計算
3. Δ が最大の特徴をスプリアス候補として選択

**確認する問い:**
- Q1. 介入テストは c（スプリアス特徴）を正しく選択できるか（SHAP の 60% と比較）
- Q2. 各特徴の J_S 降下量 Δ_x, Δ_y, Δ_c はどの程度か

---

## 命名規則

- `expNNN_<説明>` の連番で管理する
- 設定変更・再実験は新番号を振る（上書きしない）
- 廃棄した実験も番号は欠番にせずここに残す

## スクリプトと config の対応

| script | 対応 config prefix |
|--------|-------------------|
| `run_shap_pilot.py`         | `exp001_shap_gridworld`         |
| `run_intervention_pilot.py` | `exp002_intervention_gridworld` |
