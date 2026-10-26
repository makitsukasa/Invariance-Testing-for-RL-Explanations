# Invariance Testing for RL Explanations

強化学習で学習した方策（オラクル）を解釈可能なモデル（サロゲート）に蒸留して説明するとき、行動一致率（AA）が高いことは分布シフト下での性能を保証しません。このリポジトリは、その問題を調べる不変性テストと、シフトすべき特徴を性能低下 Δ で選ぶ手順の実験一式です。

論文の草稿（日本語）は `paper/draft_ja.md` です。

## 主張と、確認できた範囲

| | 確認できたこと | 確認できなかったこと・制約 |
|---|---|---|
| AA と分布シフト | GridWorld 3 次元で、AA 0.988 のサロゲートが、スプリアス特徴 $c$ の反転で AA 0.942 を保ったまま $J_S = -1.000$ に崩壊した。スプリアスのない CartPole では崩壊しなかった | 判定は閾値の近く（AA の 95% CI の下限 0.902）。10 シード |
| Δ によるシフト対象の選定（exp030、事前登録） | $p \le 0.2$ で、Δ で選んだ特徴は、環境側のシフトで実際に性能が崩壊する特徴にランダムより多く当たった（全体 87/117、期待値 21.6） | $p = 0.3$ ではランダムと区別できなかった（10/28、期待値 8.4）。原因は未検証 |
| 診断手順全体（exp030、事前登録） | ランダムより多く検出した（11/120、期待値 1.4） | 検出率は全 run の 9%。段階 1（AA ≥ 0.9）で 69/120 run が終了し、通過した run でもシフト下の AA が 0.9 を下回った |
| シフト下の AA の測り方 | 状態の変換で測る方法は「サロゲートがオラクルと同じように特徴の変化に反応するか」を、ロールアウトで測る方法は実際に訪れる状態での忠実度を測る | 二つの測り方で、手順全体の検出数は 11 と 26、$p = 0$ では 5 と 1 と大きく異なる。事前登録ではロールアウトで測ると定めていたが、動作確認の後、本実行の前に状態の変換に改めた（経緯は論文の 5.4 節） |
| 3 次元と 10 次元の違い | 3 次元では判定条件が成り立ち、10 次元ではほとんど成り立たなかった | 特徴の数・学習ステップ数・$p$ の値などが同時に変わっているので、原因は特定できない |

不変性テストの陽性の判定は、スプリアス依存の疑いを示すもので、因果的な証明ではありません。exp030 では、ゴールと独立に生成したノイズ特徴が判定条件を満たした例もありました。本研究で $c$ がスプリアスだと言えるのは、環境をそう設計したからです。

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
| `shift-selection/` | Δ による選定の実験（旧 RL-Shift-Auto-Detection を履歴ごと取り込んだもの）。exp029（同じモデルでの Δ と SHAP）、exp030（選定と評価を独立にした事前登録の検証）を含む。スクリプトは `shift-selection/` をカレントディレクトリにして実行する |
| `candidate-discovery/` | 候補特徴の自動発見の試み（旧 auto-spurious-discovery を履歴ごと取り込んだもの）。前身の記録で、詳細は `candidate-discovery/README.md` |
| `draft.md`・`draft_en.md` | 旧草稿（不変性テスト）。訂正前の版で、LunarLander・MuJoCo Hopper の予備的な結果を付録に含む。査読対応のメモは `memo.md` |
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
pip install gymnasium stable-baselines3 scikit-learn numpy pandas matplotlib torch pyyaml shap scipy
# 旧草稿の MuJoCo Hopper の実験を再実行する場合は mujoco も入れる
```

exp029・exp030 は Python 3.13、shap 0.51、stable-baselines3 2.8、PyTorch 2.11（CPU）で実行しました。

## 訂正の記録
- exp011・exp016 の SHAP の集約の誤り、旧草稿の数値・記述の食い違い（Δ の top-2 は 101/120、GridWorld のモデルは DQN と MoET、$c$ は確率 $p$ で反転）：`shift-selection/ERRATA.md`
- exp030 の補足分析（AA の測り方の食い違いの原因、$p = 0.3$ の原因の切り分け）：`shift-selection/experiments/results/exp030_shift_target_validation/supplement.md`
