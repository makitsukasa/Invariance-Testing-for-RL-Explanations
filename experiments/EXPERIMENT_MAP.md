# EXPERIMENT_MAP.md

論文の実験番号と実験ディレクトリの対応表。
数値の出典・事後計算項目・既知の不整合・未使用ディレクトリを記録する。

最終更新: 2026-04-18（exp009/exp011 を標準10シードで再実行、exp012 summary.txt 修正済み）

---

## 論文実験番号 ↔ ディレクトリ対応表

### 実験1：CartPole ノイズ拡張（再現性の構造的上限）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp004_cartpole_comparison/`（実験4と共通ソース） |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| キー数値の出典 | `exp004/summary.txt`: MoET N=0: AA=0.915±0.028、MoET N=16: AA=0.820±0.032。実験1は exp004 の MoET 列を用いてノイズ次元 N=0〜16 での AA 変化を示す |

exp001 系ディレクトリはすべて**未使用**（後述 §未使用ディレクトリ 参照）。

---

### 実験2：スプリアス GridWorld（スプリアス依存の検出）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp002_spurious_gridworld/` |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| キー数値の出典 | `summary.txt` の `p=0.0, reversed_c, K=4, d=5`: AA=0.942±0.056 / `p=0.0, train, K=4, d=5`: AA=0.988±0.011。J_S 値は metrics.csv から集計 |

---

### 実験3：CartPole 物理パラメータシフト（非スプリアス環境の不変性）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp003_cartpole_gravity/` |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| キー数値の出典 | `summary.txt`: train AA=0.915±0.028（J_I=428.1, J_R=417.9）、pole_short AA=0.846±0.115 など |
| 注意 | J_oracle(train)=428.1±148.5 の高分散（CV≈35%）は DQN の確率的収束不安定性によるもの。約 2/10 シードが未収束。W-C2 指摘（exp003 収束失敗フィルタリング）の対象 |

---

### 実験4：CartPole モデル比較（付録1）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp004_cartpole_comparison/`（実験1と共通ソース） |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| キー数値の出典 | `summary.txt`: MoET N=0: AA=0.915±0.028、Tree N=0: AA=0.902±0.031、Linear N=0: AA=0.842±0.033。Section 6.1「実験1」の N=0 数値もここが出典 |
| 統計検定 | 付録1 の Welch t 検定・Holm-Bonferroni 補正の計算元は metrics.csv。p 値は `scripts/compute_pvalues.py` で再現可能 |

---

### 実験5：GridWorld モデル比較（付録2）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp005_gridworld_comparison/` |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| キー数値の出典 | `summary.txt`: MoET p=0.5 reversed_c: AA=0.940±0.132、Linear p=0.5 reversed_c: AA=0.742±0.220 |

---

### 実験6：蒸留データ量感度分析（付録3）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp006_distill_sensitivity/` |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| キー数値の出典 | `summary.txt`: CartPole N=0, MoET, n=10k: AA=0.915±0.028（Table A5 の該当行） |

---

### 実験7：LunarLander-v3 拡張（付録4）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp009_gbt_continuous/` |
| config | `configs/exp009_gbt_continuous.yaml`（LunarLander 専用。hopper セクションなし） |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（標準 10 シード。2026-04-18 に 10 シードへ統一済み） |
| キー数値の出典 | `metrics_seed*.csv` を集計した `metrics.csv` および `summary.txt`。GBT train: AA=0.876±0.026、gravity_hi: AA=0.886±0.019、gravity_lo: AA=0.706±0.049。J_S（GBT train）≈240.2±13.4 は metrics.csv の j_reasoned から |
| oracle | `results/exp007_lunarlander_ppo/` の PPO 学習済みモデル（seeds 42-1011）。seeds 1314-2526 は初回実行時に exp009_gbt_continuous/ に保存 |

---

### 実験8：MuJoCo Hopper-v5 拡張（付録5）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ（d=12）| `results/exp011_hopper_surrogates/` |
| 対応ディレクトリ（d=5） | `results/exp012_hopper_weak_tree/` |
| config（d=12）| `configs/exp011_hopper_surrogates.yaml`（標準 10 シードに更新済み） |
| config（d=5） | `configs/exp012_hopper_weak_tree.yaml`（標準 10 シード） |
| シード（exp011）| 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（標準 10 シード。2026-04-18 に再実行・再集計済み） |
| シード（exp012）| 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（標準 10 シード） |
| キー数値の出典（AA）| `exp011/summary.txt`（2026-04-18 再集計）: RegTree train AA=0.703±0.009 / `exp012/summary.txt`（2026-04-18 修正）: RegTree train AA=0.649±0.016 |
| キー数値の出典（R²）| **R² は summary.txt には記録されない。`scripts/compute_r2.py` で action_diffs/ から事後計算。** exp011 標準10シード: RegTree train R²=0.922±0.008、gravity_lo R²=−0.124±0.225。exp012: RegTree train R²=0.698±0.010。`r2_summary.csv` に保存済み |
| oracle | `results/rlzoo_models/td3/Hopper-v3_1/Hopper-v3.zip`（全シード共通の固定 TD3 モデル） |

---

## 既知の数値不整合

### [不整合1] 実験1テキスト数値の出典（対応済み）

- 実験1・実験4 ともに `exp004_cartpole_comparison/` を正規ソースとして採用
- exp001_cartpole_noise は未使用と整理（後述 §未使用ディレクトリ 参照）
- draft.md の N=16 値を exp004 に合わせて 0.819±0.033 → **0.820±0.032** に修正済み

### [不整合2] exp012 summary.txt の ±nan（対応済み）

- 原因: 旧 summary.txt が 1 シードのみで生成されたバグ
- 対応: 2026-04-18 に全 10 シードから再集計し修正済み（train AA=0.649±0.016）

### [不整合3] exp011 非標準シードセット（対応済み）

- 旧シード: 42, 123, 456, 789, 1011, 2024, 2718, 3141, 6553, 9001
- 2026-04-18 に標準シード（42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526）で再実行・再集計。config も更新済み
- 論旨への影響なし（R² 値は旧来とほぼ同値）

### [不整合4] 実験7（LunarLander）の 5 シード（対応済み）

- 旧: 5 シードのみ（42, 123, 456, 789, 1011）
- 2026-04-18 に標準 10 シードで再実行。config も更新済み
- 結果は exp009_gbt_continuous に統一

---

## R² と p 値は事後計算

| 指標 | 計算元 | スクリプト |
|------|--------|-----------|
| R²（Hopper exp011/exp012）| `action_diffs/*.npz` | `scripts/compute_r2.py` |
| Welch t 検定・p 値 | 各実験の `metrics.csv` | `scripts/compute_pvalues.py` |

---

## 未使用ディレクトリ

| ディレクトリ | 用途 | 備考 |
|-------------|------|------|
| `exp001_cartpole_noise/` | CartPole N×K×d グリッドサーチ | **未使用**。実験1・4 の正規ソースは exp004 |
| `exp001_n0/` | N=0 単体実行 | **未使用** |
| `exp001_n0_check/` | 収束確認 | **未使用** |
| `exp001_n4/` | N=4 単体実行 | **未使用** |
| `exp001_n8/` | N=8 単体実行 | **未使用** |
| `exp001_n16/` | N=16 単体実行 | **未使用**（旧 draft で N=16 値の出典だったが exp004 に統一） |
| `conv_check_1m/` | 学習ステップ数 1M での収束確認 | 予備実験 |
| `conv_check_200k/` | 学習ステップ数 200k での収束確認 | 予備実験 |
| `conv_check_50k/` | 学習ステップ数 50k での収束確認 | 予備実験 |
| `exp007_lunarlander_ppo/` | LunarLander PPO oracle の学習（exp009 で再利用） | oracle モデルのみ使用。summary 等は未使用 |
| `exp007_lunarlander_v2/` | LunarLander の中間バージョン | 廃棄 |
| `exp007_mujoco_v2/` | MuJoCo Hopper の中間バージョン | 廃棄 |
| `exp010_regression_hopper/` | Hopper 回帰サロゲートの予備実験 | exp011/exp012 の前身 |
| `rlzoo_models/` | RL Zoo 事前学習済み TD3 モデル | exp011/exp012 の oracle として使用 |
