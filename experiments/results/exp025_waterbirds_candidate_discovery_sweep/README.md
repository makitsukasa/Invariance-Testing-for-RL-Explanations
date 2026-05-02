# exp025: Waterbirds 候補発見 sweep

## 目的
Waterbirds 上で、候補発見法が `background` をどれだけ安定して選べるかを調べる。`exp018` の checkpoint を再利用し、`exp022` の `Delta` 判定を confirmation reference として参照する。

## 実験設定
- Script: `experiments/run_waterbirds_candidate_discovery_sweep.py`
- Config: `experiments/configs/exp025_waterbirds_candidate_discovery_sweep.yaml`
- Output dir: `experiments/results/exp025_waterbirds_candidate_discovery_sweep/`
- Methods: `score_fraction`, `mean_prob_delta`, `pca_proxy`, `random`
- `n_eval`: `[100, 300]`
- `mask_radii`: `[-3, -1, 0, 1, 3]`
- Seeds: `0..29`

## 主な出力
- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `results.png`
- `meta.json`
- `runtime_sessions.csv`
- `seed_logs/`

## メモ
開始時は `EXPERIMENT_MAP.md` を `実行中` に更新し、完了後に実行時間と結果要約を反映する。
