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
1. 各特徴 f を**全て uniform random**で摂動しながらサロゲートをロールアウト（特徴型の事前知識なし）
2. Δ_f = J_S_train - J_S_f_perturbed を計算
3. Δ が最大の特徴をスプリアス候補として選択

**確認する問い:**
- Q1. 介入テストは c（スプリアス特徴）を正しく選択できるか（SHAP の 60% と比較）
- Q2. 各特徴の J_S 降下量 Δ_x, Δ_y, Δ_c はどの程度か

---

### exp003 — LunarLander per-feature 介入テスト（SpuriousLunarLander）**[失敗・中止]**

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp003_intervention_lunar.yaml` |
| script | `experiments/run_lunar_pilot.py` |
| results | `experiments/results/exp003_intervention_lunar/` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 2M steps, 差分シェーピング補正 |

**目的:** exp002（GridWorld 3特徴）と同一アルゴリズムを9特徴の LunarLander に適用する。

**結果:** 検出率 0%（0/5 seeds）。DQN oracle が 2M steps でもゾーン依存方策を学習できず（J_oracle ≈ -10〜+104、AA ≈ 0.59〜0.71）。

**失敗原因:** ゾーン信号のディスカウント問題。LunarLander のエピソード長（300〜500 steps）と γ=0.99 の組み合わせで、終端ゾーンボーナス（±100）の episode 開始時有効値が 0.99^400 × 100 ≈ 0.018 まで減衰する。差分シェーピング補正（累積 ~33/episode）もフライト制御報酬（毎ステップ ±10〜50）に埋もれ、DQN がゾーン依存性を学習できなかった。→ exp004 に移行。

---

### exp004 — GridWorld + ノイズ特徴 10 次元（スケール確認）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp004_noise_gridworld.yaml` |
| script | `experiments/run_gridworld_noise.py` |
| results | `experiments/results/exp004_noise_gridworld/` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 50k steps, spurious_p=0.0 |

**目的:** exp002（3特徴）と同一アルゴリズムを obs=(x, y, c, noise×7) の10次元に拡張し、特徴数を増やしても c を正しく選択できるかを確認する。ノイズ特徴は毎ステップ i.i.d. uniform [0,1] で再サンプリング。

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
| `run_lunar_pilot.py`        | `exp003_intervention_lunar`     |
