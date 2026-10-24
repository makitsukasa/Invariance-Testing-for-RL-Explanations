# exp026: Waterbirds 候補発見（CLIP / SSL 表現ベース）

## 目的
Waterbirds 上で、表現ベースの候補発見 proxy を前段に置き、PerformanceCheck との接続可能性を追加検証する。

## 実験設定
- Script: `experiments/run_waterbirds_representation_candidate_discovery.py`
- Config: `experiments/configs/exp026_waterbirds_clip_ssl_candidate_discovery.yaml`
- Output dir: `experiments/results/exp026_waterbirds_clip_ssl_candidate_discovery/`
- Models:
  - CLIP: `openai/clip-vit-base-patch32`
  - SSL: `facebook/dinov2-small`
- `n_eval`: `[100, 300]`
- `mask_radii`: `[-3, -1, 0, 1, 3]`
- Seeds: `0..9`
- Confirmation reference: `exp022` の `Delta`

## 主な出力
- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `results.png`
- `meta.json`
- `runtime_sessions.csv`
- `seed_logs/`

## 結果要約
- 実行時間は `57分32秒`
- `clip_vit_b32` は全条件で `background` を `100%` top-1 に選択した
- CLIP の `exp022` Delta 判定との整合率は `mask_radius=-3/-1/0/1/3` で `90/80/60/70/40%` だった
- `ssl_dinov2_small` は全条件で `foreground` を top-1 に選択し、`background` top-1 は `0%` だった
- SSL の Delta 整合率は `10/20/40/30/60%` で、CLIP とは逆方向の proxy を返した
- `n_eval=100` と `n_eval=300` の結果はほぼ一致しており、この範囲ではサンプル数より表現の性質の違いが支配的だった
- したがって、Waterbirds では「どの候補を強く示すか」は表現依存であり、後段の PerformanceCheck が候補の機能的必要性を切り分ける役割を持つことが再確認された

## メモ
- `base_mask_cache.pt` は `exp022` の mask cache を再利用している
- モデル重み cache は `data/model_cache/huggingface/` を使う
- 実行には `transformers`, `huggingface_hub`, `safetensors` が必要
