# exp006 — LunarLander PPO + gamma=0.999（差分シェーピングあり）

| 項目 | 詳細 |
|------|------|
| config | `experiments/configs/exp006_ppo_lunar.yaml` |
| script | `experiments/run_lunar_ppo.py` |
| seeds | 0, 42, 123, 456, 789（5 seeds） |
| oracle | PPO 1M steps, gamma=0.999, gae_lambda=0.98 |
| surrogate | MoET K=4, d=5, epochs=100, n=10000 |
| obs | 9次元（x, y, vx, vy, angle, ang_vel, leg_L, leg_R, c） |

**目的:**
exp003（DQN + gamma=0.99）の失敗原因（終端報酬が gamma^400 ≈ 0.018 に減衰）を、PPO + gamma=0.999 で解消できるかを検証。

**結果:**

| 指標 | 値 |
|------|-----|
| Stage 1 pass (AA ≥ 0.9) | 0% (0/5) |
| Stage 2 collapse | 0% (0/5) |
| 介入テスト c 選択成功 | 0% (0/5) |
| J_oracle 平均 | 269.0 ± 52.4 |
| J_S_train 平均 | −387.7 ± 142.3 |
| Δ_c 平均 | −30.3 ± 98.9 |

Per-seed:

| seed | AA | J_oracle | selected | correct |
|------|-----|----------|----------|---------|
| 0 | 0.671 | 262.1 | ang_vel | False |
| 42 | 0.594 | 183.0 | vy | False |
| 123 | 0.710 | 302.0 | ang_vel | False |
| 456 | 0.744 | 317.2 | leg_R | False |
| 789 | 0.779 | 280.6 | ang_vel | False |

**失敗原因:**
差分ポテンシャルシェーピングが `target_zone`（c 由来の変数）ではなく、環境内部の固定変数を参照していた。結果として c は観測に存在するだけで報酬に影響せず、oracle は c を無視した汎用着陸方策を学習。gamma 問題は解消されたが、前提条件（oracle が c に依存する）が成立しなかった。

→ exp007 で差分シェーピングを完全撤廃し、終端 zone_bonus のみに再設計。
