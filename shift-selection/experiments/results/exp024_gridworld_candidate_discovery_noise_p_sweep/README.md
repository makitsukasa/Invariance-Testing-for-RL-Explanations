# exp024: 自動候補発見の `spurious_p` / noise sweep（GridWorld）

## 目的
Spurious GridWorld 上で `spurious_p` とノイズ次元数を同時に sweep し、候補発見法の差がどの条件まで保たれるかを確認する。後段の `PerformanceCheck` に渡す前段として、どの候補発見法が安定かを見る。

## 実験設定
- Script: `experiments/run_gridworld_candidate_discovery_noise_p_sweep.py`
- Config: `experiments/configs/exp024_gridworld_candidate_discovery_noise_p_sweep.yaml`
- Output dir: `experiments/results/exp024_gridworld_candidate_discovery_noise_p_sweep/`
- Seeds: `[0, 42, 123, 456, 789]`
- `spurious_p`: `[0.05, 0.15, 0.25]`
- `n_noise`: `[3, 7, 15]`
- Methods: `mutual_info`, `linear_probe_drop`, `tree_probe_drop`, `random`

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
- 強相関 (`spurious_p=0.05`。c = goal_id XOR Bernoulli(p) なので p が小さいほど相関が強い。2026-10-24 に「低相関」から訂正) では `linear_probe_drop` と `tree_probe_drop` が強く、`n_noise=15` ではともに top-1 回収率 `100%`。
- `spurious_p` が `0.15`, `0.25` に上がると、probe 系も top-1 回収率が低下する。
- `mutual_info` は strict な top-1 では弱い条件がある一方、全条件で top-k 回収率 `100%` を維持する。
- `random` は全体として弱く、基準法として妥当な挙動を示す。
- 実行時間は `13分36秒`。

## メモ
このディレクトリは `rl-shift-auto-detection` 側で直接管理する。再実行時には metadata、runtime log、checkpoint path もこのリポジトリ基準で更新される。
