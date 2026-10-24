# exp007 — SpuriousLunarLander v2 アブレーション（差分シェーピング除去 + zone_bonus sweep）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp007_ablation_lunar.yaml` |
| script | `experiments/run_lunar_ablation.py` |
| seeds | 42, 123, 456, 789（4 seeds） |
| oracle | PPO 1M steps, gamma=0.999, gae_lambda=0.98 |
| surrogate | MoET K=8, d=6, epochs=200, n=20000 |
| obs | 9次元（x, y, vx, vy, angle, ang_vel, leg_L, leg_R, c） |
| 実行時間 | 4時間10分（21分/batch、4並列 × torch.set_num_threads(2)） |

**目的:**
差分シェーピングを除去し終端 zone_bonus のみで oracle にゾーン選択を学ばせられるかを検証。
zone_bonus と条件（c の有無・相関強度）を sweep し、oracle が c に依存する条件を特定する。

**conditions:**
- `no_c`: c=0.5 固定（dummy）、ゾーンボーナスあり
- `c_random`: c は毎ステップ random、ゾーンボーナスあり
- `c_correlated_p00`: c=zone（p=0.0 完全相関）、ゾーンボーナスあり
- `c_correlated_p01`: c が 10% の確率で反転（p=0.1）、ゾーンボーナスあり

**結果サマリー（各セル = 4 seeds の mean AA / mean J_oracle）:**

| condition | zone_bonus=100 | zone_bonus=200 | zone_bonus=300 |
|-----------|---------------|---------------|---------------|
| no_c | AA=0.816 / J=221 | AA=0.750 / J=215 | AA=0.807 / J=239 |
| c_random | AA=0.768 / J=214 | AA=0.735 / J=245 | AA=0.741 / J=220 |
| c_corr p00 | AA=0.773 / J=226 | AA=0.737 / J=172 | AA=0.691 / J=188 |
| c_corr p01 | AA=0.685 / J=187 | AA=0.733 / J=212 | AA=0.779 / J=216 |

- **全 48 runs: correct=False（検出率 0%）、collapse=False（0%）**
- AA は最大 0.886（no_c/zb100/seed456）で閾値 0.9 に未到達
- Δ_c は c_correlated 条件でも**負**（c をランダム化するとサロゲート性能が上がる）
- 介入テストは `ang_vel`、`angle`、`vx` などを誤選択し続ける

**失敗原因:**
LunarLander 標準の毎ステップフライト制御報酬（加速・着陸脚接触など）が 1 エピソードで累積 ~200 程度になる。終端 zone_bonus=100–300 を加えても、oracle は「どちらのゾーンでも上手く着地する」汎用方策を学ぶ方が高報酬になり、ゾーン選択（= c への依存）を獲得しない。

**結論:**
「oracle が c に依存するが c はスプリアス」という前提条件が、標準 LunarLander のシェーピング構造と根本的に相性が悪い。zone_bonus をさらに大きくする（>500–1000）か、環境を変えることが必要。→ ColoredMNIST（非RL）への移行を検討。
