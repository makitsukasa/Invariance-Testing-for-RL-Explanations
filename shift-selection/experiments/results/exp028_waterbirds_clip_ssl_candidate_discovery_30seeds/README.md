# exp028: Waterbirds 候補発見（CLIP / 自己教師あり表現, 30 seeds）

## 目的
`exp026` を 30 シードへ拡張し、CLIP と自己教師あり表現による Waterbirds の候補発見が、PerformanceCheck 参照判定とどの程度整合するかを再確認する。

## 実験設定
- Script: `experiments/run_waterbirds_representation_candidate_discovery.py`
- Config: `experiments/configs/exp028_waterbirds_clip_ssl_candidate_discovery_30seeds.yaml`
- Output dir: `experiments/results/exp028_waterbirds_clip_ssl_candidate_discovery_30seeds/`
- Models:
  - CLIP: `openai/clip-vit-base-patch32`
  - SSL: `facebook/dinov2-small`
- Seeds: `0..29`
- `n_eval`: `[100, 300]`
- `mask_radii`: `[-3, -1, 0, 1, 3]`
- Confirmation reference: `exp022` の `PerformanceCheck`

## 主な結果
- 実行時間: `170.9 min`
- CLIP は全条件で background を `100%` top-1 に置いた。
  - `pc_align` は radius `-3/-1/0/1/3` で `80% / 63% / 57% / 50% / 30%`
  - `score_gap` は `0.108 -> 0.046`（`n_eval=100`）および `0.105 -> 0.044`（`n_eval=300`）
- 自己教師あり表現は全条件で foreground を top-1 に置き、background top-1 は `0%`
  - `pc_align` は radius `-3/-1/0/1/3` で `20% / 37% / 43% / 50% / 70%`
  - `score_gap` は全条件で負で、background より foreground 変化が大きい
- `n_eval=100` と `300` で傾向はほぼ同じであり、この範囲ではサンプル数より表現空間の違いの方が支配的だった。

## 出力
- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `results.png`
- `meta.json`
- `runtime_sessions.csv`
- `seed_logs/`
- `base_mask_cache.pt`

## メモ
- `exp026` の 10 シード版で見えていた「CLIP は background、自己教師あり表現は foreground を上位に置く」という差は、30 シードでもそのまま維持された。
- candidate discovery の候補順位は表現空間に依存しうる一方、PerformanceCheck 参照判定との整合率は mask radius に応じて系統的に変化しており、後段確認の必要性を補強する結果になっている。
