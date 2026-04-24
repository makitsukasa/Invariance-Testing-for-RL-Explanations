# EXPERIMENT_MAP.md

論文の実験番号と実験ディレクトリの対応表。
数値の出典・事後計算項目・既知の不整合・未使用ディレクトリを記録する。

最終更新: 2026-04-25（exp016 追加：Hopper GBT+DAgger）

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
| 対応ディレクトリ（BC d=12）| `results/exp011_hopper_surrogates/`（構造制約ボトルネック確認用、本文 Table 参照なし） |
| 対応ディレクトリ（BC d=5） | `results/exp012_hopper_weak_tree/`（同上） |
| 対応ディレクトリ（GBT+DAgger）| `results/exp016_hopper_gbt_dagger/` ← **Table A7・A8 の出典** |
| config（BC d=12）| `configs/exp011_hopper_surrogates.yaml` |
| config（BC d=5） | `configs/exp012_hopper_weak_tree.yaml` |
| config（GBT+DAgger）| `configs/exp016_hopper_gbt_dagger.yaml`（GBT, DAgger 10イテレーション×10,000サンプル、標準10シード） |
| シード | すべて標準 10 シード（42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526） |
| キー数値の出典（BC R²）| exp011: RegTree train R²=0.922±0.008 / exp012: R²=0.698±0.010（付録5本文のみ言及） |
| キー数値の出典（GBT+DAgger）| `exp016/metrics_seed*.csv`（10シード統合）+ `exp016/action_diffs/` から R² 事後計算。train: R²=0.968±0.004、AA=0.808±0.019、J_S=3527±25（oracle比99.7%）。Table A7・A8 の出典 |
| oracle | `results/rlzoo_models/td3/Hopper-v3_1/Hopper-v3.zip`（全シード共通の固定 TD3 モデル） |
| 旧実験（未使用）| `exp013_hopper_more_samples/`（seed=42 のみ、BC covariate shift 確認）、`exp014_hopper_dagger/`（RegTree+DAgger）は付録5入れ替えにより未使用 |

---

### 実験9（仮称）：Faithfulness vs. Invariance 比較（付録6）

| 項目 | 詳細 |
|------|------|
| 対応ディレクトリ | `results/exp015_faithfulness_comparison/` |
| oracle 再利用元 | `results/exp002_spurious_gridworld/`（intuitive_p{p}_seed{s}、eval_states_p{p}_seed{s}.npy） |
| surrogate 設定 | MoET K=4, d=5（論文主実験と同一）、BC 蒸留 100 epochs / 10,000 samples |
| シード | 42, 123, 456, 789, 1011, 1314, 1617, 1920, 2223, 2526（10シード） |
| 対象条件 | spurious_p ∈ {0.0, 0.2, 0.5} |
| 指標 | Comprehensiveness faithfulness（feature c マスク時の AA 低下量）＋ exp002 の reversed_c 不変性結果 |
| スクリプト | `scripts/compute_faithfulness.py` |
| キー数値の出典 | `exp015/faithfulness_results.csv`、`exp015/summary.txt` |
| 目的 | Comprehensiveness は訓練分布内評価のみ → スプリアス依存を検出できない。不変性評価が補完することを実証 |

---

## R² と p 値は事後計算

| 指標 | 計算元 | スクリプト |
|------|--------|-----------|
| R²（Hopper exp011/exp012）| `action_diffs/*.npz` | `scripts/compute_r2.py` |
| Welch t 検定・p 値 | 各実験の `metrics.csv` | `scripts/compute_pvalues.py` |
| Comprehensiveness faithfulness（exp015）| exp002 oracle + 再蒸留 | `scripts/compute_faithfulness.py` |

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
