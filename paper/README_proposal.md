# README の更新案（2026-10-26 に適用済み）

リポジトリ直下の `README.md` を、統合した論文（`paper/draft_ja.md`）に合わせて書き直す案です。了承を得て `README.md` に反映しました。反映の際、本文の最終修正に合わせて次の 3 点を加えました。下の「案の本文」は了承時の版のまま残しており、反映後の正本は `README.md` です。

- 表の「シフト下の AA の測り方」の行に、事前登録からの変更の経緯を加えた。
- 表に「3 次元と 10 次元の違い」の行を加え、原因は特定できないことを書いた。
- 陽性の判定は因果的な証明ではないこと（ノイズ特徴が判定条件を満たした例）を加えた。あわせて、旧草稿の一覧に `memo.md` を、セットアップに `scipy` と MuJoCo の注記を加えた。

## 方針
- 冒頭の主張を、統合した論文の限定した主張に合わせる。「スプリアス依存を検出する枠組み」という書き方をやめ、「AA が高くても分布シフト下の性能は保証されない」「不変性テストで検出できる場合がある」「Δ をシフト対象の選定に使える」「診断の成立は評価状態の分布と判定条件に依存する」を並べる。
- 主な結果に、肯定的な結果だけでなく、exp030 の手順全体の検出率（11/120）、$p = 0.3$ で確認できなかったこと、AA の測り方による違いを載せる。
- 連続制御（実験 7・8）は論文から外したので、「主要な実験結果」から外し、旧草稿の付録として残っていることだけを書く。
- 「SHAP は依存の有効性を検出できない」という対比の表現を、測る量の違いの説明に改める。
- 草稿の一覧に `paper/` を加え、旧草稿（`draft.md`・`shift-selection/draft.md`）は訂正前の版であることを明記する。

## 案の本文

---

# Invariance Testing for RL Explanations

強化学習で学習した方策（オラクル）を解釈可能なモデル（サロゲート）に蒸留して説明するとき、行動一致率（AA）が高いことは分布シフト下での性能を保証しません。このリポジトリは、その問題を調べる不変性テストと、シフトすべき特徴を性能低下 Δ で選ぶ手順の実験一式です。

論文の草稿（日本語）は `paper/draft_ja.md` です。

## 主張と、確認できた範囲

| | 確認できたこと | 確認できなかったこと・制約 |
|---|---|---|
| AA と分布シフト | GridWorld 3 次元で、AA 0.988 のサロゲートが、スプリアス特徴 $c$ の反転で AA 0.942 を保ったまま $J_S = -1.000$ に崩壊した。スプリアスのない CartPole では崩壊しなかった | 判定は閾値の近く（AA の 95% CI の下限 0.902）。10 シード |
| Δ によるシフト対象の選定（exp030、事前登録） | $p \le 0.2$ で、Δ で選んだ特徴は、環境側のシフトで実際に性能が崩壊する特徴にランダムより多く当たった（全体 87/117、期待値 21.6） | $p = 0.3$ ではランダムと区別できなかった（10/28、期待値 8.4）。原因は未検証 |
| 診断手順全体（exp030、事前登録） | ランダムより多く検出した（11/120、期待値 1.4） | 検出率は全 run の 9%。段階 1（AA ≥ 0.9）で 69/120 run が終了し、通過した run でもシフト下の AA が 0.9 を下回った |
| シフト下の AA の測り方 | 状態の変換で測る方法は「サロゲートがオラクルと同じように特徴の変化に反応するか」を、ロールアウトで測る方法は実際に訪れる状態での忠実度を測る | 二つの測り方で、手順全体の検出数は 11 と 26、$p = 0$ では 5 と 1 と大きく異なる |

本研究は、スプリアス依存がないことの保証、候補特徴の自動発見、Δ が一般に SHAP より優れていることは主張しません。

## 診断の手順
1. 段階 1：訓練分布で AA ≥ 0.9 を確かめる。
2. 選定：候補特徴を Δ（特徴を一様分布で置換したときの平均リターンの低下）で順位づける。
3. 段階 2：1 位の特徴をシフトし、AA(D_shift) > 0.9 かつ $J_S$(shift) < 0.8 × $J_S$(train) なら「スプリアス依存の疑い」と判定する。AA(D_shift) をどの状態分布で測るかを明記する。

## ディレクトリ

| パス | 内容 |
|---|---|
| `paper/` | 統合した論文の草稿（`draft_ja.md`）、構成案（`outline.md`） |
| `experiments/` | GridWorld 3 次元・CartPole の実験（論文の 6.1 節）。`run_gridworld.py`、`run_gravity.py` など |
| `shift-selection/` | Δ による選定の実験（旧 RL-Shift-Auto-Detection）。exp029（同じモデルでの Δ と SHAP）、exp030（選定と評価を独立にした事前登録の検証）を含む。スクリプトは `shift-selection/` をカレントディレクトリにして実行する |
| `candidate-discovery/` | 候補特徴の自動発見の試み（旧 auto-spurious-discovery）。前身の記録 |
| `draft.md`・`draft_en.md` | 旧草稿（不変性テスト）。訂正前の版で、LunarLander・MuJoCo Hopper の予備的な結果を付録に含む |
| `shift-selection/draft.md` | 旧草稿（Δ による選定）。訂正前の版。訂正の内容は `shift-selection/ERRATA.md` |

## 主な実験の再実行

```bash
# GridWorld 3 次元・CartPole（リポジトリ直下で）
python experiments/run_gridworld.py --config experiments/configs/exp002_spurious_gridworld.yaml
python experiments/run_gravity.py   --config experiments/configs/exp003_cartpole_gravity.yaml

# exp030（shift-selection/ で。120 run、4 並列で約 3 時間）
python experiments/run_shift_target_validation.py --config experiments/configs/exp030_shift_target_validation.yaml
python experiments/compute_stats_shift_target.py experiments/results/exp030_shift_target_validation/results.csv --save
```

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install gymnasium stable-baselines3 scikit-learn numpy pandas matplotlib torch pyyaml shap
```

exp029・exp030 は Python 3.13、shap 0.51、stable-baselines3 2.8、PyTorch 2.11（CPU）で実行しました。

## 訂正の記録
- exp011・exp016 の SHAP の集約の誤り、旧草稿の数値・記述の食い違い（Δ の top-2 は 101/120、GridWorld のモデルは DQN と MoET、$c$ は確率 $p$ で反転）：`shift-selection/ERRATA.md`
- exp030 の補足分析（AA の測り方の食い違いの原因、$p = 0.3$ の原因の切り分け）：`shift-selection/experiments/results/exp030_shift_target_validation/supplement.md`

---
