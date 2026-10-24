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

## 結果要約
- 実行時間は `30分25秒`。
- `score_fraction` と `mean_prob_delta` は、全条件で `background` を `100%` top-1 に選択した。
- `pca_proxy` も `n_eval=100` で `97%`、`n_eval=300` で `100%` と高い top-1 回収率を示した。
- 一方で `exp022` の Delta 判定との整合率は、`mask_radius=-3` で `80%`、`0` で `57%`、`3` で `30%` まで下がった。
- したがって、Waterbirds では候補発見自体はかなり安定だが、「候補の存在」と「実際に性能へ効くか」はやはり別の情報であることが確認された。

## メモ
- `exp018` の checkpoint を再利用しており、この実験では新しい oracle checkpoint は保存しない。
- `base_mask_cache.pt` は `exp022` の前景マスク cache を再利用している。
