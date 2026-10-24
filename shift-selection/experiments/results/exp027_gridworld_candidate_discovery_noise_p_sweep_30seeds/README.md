# exp027: GridWorld 候補発見 sweep（30 seeds）

## 目的
`exp024` を 30 シードへ拡張し、Spurious GridWorld における候補発見手法の順位安定性を、`spurious_p` と `n_noise` の両軸で再確認する。

## 実験設定
- Script: `experiments/run_gridworld_candidate_discovery_noise_p_sweep.py`
- Config: `experiments/configs/exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds.yaml`
- Output dir: `experiments/results/exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds/`
- Seeds: `0..29`
- `spurious_p`: `[0.05, 0.15, 0.25]`
- `n_noise`: `[3, 7, 15]`
- Methods: `mutual_info`, `linear_probe_drop`, `tree_probe_drop`, `random`

## 主な結果
- 実行時間: `74.5 min`
- `linear_probe_drop` は最も安定して強く、`p=0.05, noise=15` で `top-1 97%`、`p=0.15, noise=15` でも `53%` を示した。
- `tree_probe_drop` も低相関条件では強く、`p=0.05, noise=7/15` で `73% / 100%` の `top-1` 回収率を示した。
- `mutual_info` は `p=0.05, noise=15` で `100%` だが、`p=0.15` 以上では `top-1` が大きく崩れた。
- 多くの条件で `top-k` は高水準を保っており、候補を広く拾う段階と、`top-1` をそのまま信じる段階は分けて考える必要がある。

## 出力
- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `results.png`
- `meta.json`
- `runtime_sessions.csv`
- `seed_logs/`
- `checkpoints/`

## メモ
- `exp024` の 5 シード版より主張を強めるための拡張実験。
- candidate discovery の単独性能というより、確認手続きと組み合わせたときの前段候補の安定性を見る補助証拠として使う。
