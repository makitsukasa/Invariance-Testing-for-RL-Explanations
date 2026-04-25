# exp003 — LunarLander per-feature 介入テスト **[失敗・中止]**

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp003_intervention_lunar.yaml` |
| script | `experiments/run_lunar_pilot.py` |
| seeds | 42, 123, 456, 789, 0（5 seeds） |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| oracle | DQN 2M steps, 差分シェーピング補正 |

**目的:** exp002（GridWorld 3特徴）と同一アルゴリズムを9特徴の LunarLander に適用する。

**結果:** 検出率 0%（0/5 seeds）。J_oracle ≈ -10〜+104、AA ≈ 0.59〜0.71。

**失敗原因:** ゾーン信号のディスカウント問題。
- エピソード長 300〜500 steps × γ=0.99 → 終端ゾーンボーナス（±100）の episode 開始時有効値 ≈ 0.018
- 差分シェーピング補正（累積 ~33/episode）もフライト制御報酬（毎ステップ ±10〜50）に埋もれる
- GridWorld（〜15 steps）では 0.99^15≈0.86 で問題なかった

→ exp004（GridWorld + ノイズ特徴）に移行。LunarLander は PPO 切替か密な報酬設計を要する。
