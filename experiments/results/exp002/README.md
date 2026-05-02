# exp002: GridWorld noise-p sweep

## 目的

Spurious GridWorld 上で `spurious_p` とノイズ次元数 `n_noise` を同時に sweep し、
`exp001` で観測した候補発見法の差が、どの条件まで保たれるかを確認する。

## 対応ファイル

- 実行スクリプト: `experiments/entrypoints/run_gridworld_candidate_discovery_noise_p_sweep.py`
- 設定ファイル: `experiments/configs/exp002_gridworld_noise_p_sweep.yaml`
- 部分結果: `experiments/results/exp002/results_partial.csv`
- 実行メタ情報: `experiments/results/exp002/meta.json`
- 実行セッション: `experiments/results/exp002/runtime_sessions.csv`
- seed ごとのログ: `experiments/results/exp002/seed_logs/`
- 学習済みモデル: `experiments/results/exp002/checkpoints/`

## 記録項目

- 実験設定
- 実行時間
- 条件ごとの結果
- 中断後の再開有無
- `top-1 hit`, `top-k hit`, 真のスプリアス特徴の順位
- `spurious_p` と `n_noise` に対する劣化の仕方
- 失敗原因
- 考察

## 現在の状態

完了

- 開始時刻: `2026-05-02 22:26:24`
- 完了時刻: `2026-05-02 22:38:56`
- 実行時間: `12分31秒`
- 出力先: `experiments/results/exp002/`
- 進捗管理: `meta.json`, `results_partial.csv`, `seed_logs/`

## 実行設定

- seeds: `[0, 42, 123, 456, 789]`
- `spurious_p`: `[0.05, 0.15, 0.25]`
- `n_noise`: `[3, 7, 15]`
- workers: `4`
- estimated minutes per task: `1.5`

## 結果要約

- 完了 task 数: `45 / 45`
- 低相関条件 `p=0.05` では `tree_probe_drop` と `linear_probe_drop` が強く、特に `tree_probe_drop` は `noise=7,15` で top-1 hit `100%`
- `p` を `0.15`, `0.25` に上げると全体に top-1 hit が低下し、候補発見が難しくなる傾向が確認できた
- `mutual_info` はほぼ全条件で top-3 hit `100%` を維持する一方、top-1 は弱い
- `random` は条件に依らず低性能で、ベースラインとして妥当

## 短い考察

`exp001` で見えた手法差は、`spurious_p` と `n_noise` を振っても完全には消えなかった。
一方で `p` を上げると `tree_probe_drop` でも top-1 hit が崩れる条件があり、候補発見難易度が相関強度に強く依存することが分かった。
