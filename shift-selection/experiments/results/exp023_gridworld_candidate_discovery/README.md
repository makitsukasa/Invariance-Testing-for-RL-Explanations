# exp023: 自動候補発見（GridWorld）

## 目的
正解付き Spurious GridWorld 上で、単純な候補発見法が真のスプリアス特徴 `c_spurious` を上位に回収できるかを調べる。あわせて、選ばれた候補を既存の `PerformanceCheck` に接続したときに、性能崩壊候補として確認されるかも見る。

## 実験設定
- Script: `experiments/run_gridworld_candidate_discovery.py`
- Config: `experiments/configs/exp023_gridworld_candidate_discovery.yaml`
- Output dir: `experiments/results/exp023_gridworld_candidate_discovery/`
- Seeds: `[0, 42, 123, 456, 789]`
- Methods: `mutual_info`, `linear_probe_drop`, `tree_probe_drop`, `random`
- Environment: `spurious_p=0.05`, `n_noise=7`, `grid_size=5`

## 主な出力
- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `results.png`
- `meta.json`
- `runtime_sessions.csv`
- `seed_logs/`
- `checkpoints/`

## 結果要約
- `linear_probe_drop` は top-1 回収率 `80%`、mean rank `1.20`。
- `tree_probe_drop` は top-1 回収率 `60%`、mean rank `1.40`。
- `mutual_info` は top-1 回収率 `40%` だが、top-k 回収率は `100%`。
- `random` は top-1 回収率 `20%`、top-k 回収率 `20%`。
- 実行時間は `1分55秒`。

## メモ
このディレクトリは `rl-shift-auto-detection` 側で直接管理する。現在のファイルは、このリポジトリ内での再実行結果に基づく。
