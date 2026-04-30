# exp021: Waterbirds specialized baseline comparison

## Purpose
Compare Delta / SHAP against a specialized spurious-feature baseline on Waterbirds.

## Inputs
- Shared config: `experiments/configs/exp021_waterbirds_specialized_scores.yaml`
- exp018 checkpoints: `experiments/results/exp018_waterbirds_30seeds/checkpoints/`
- exp018 comparison CSV: `experiments/results/exp018_waterbirds_30seeds/results.csv`

## Generation step
- Script: `experiments/run_waterbirds_specialized_scores.py`
- Output: `specialized_scores.csv`

## Comparison step
- Script: `experiments/run_waterbirds_specialized_baseline.py`
- Output: `results.csv`, `summary.txt`

## Notes
- The baseline score file is generated first, then merged with exp018 and the checkpoint metadata.
- This keeps the specialized baseline path reusable for future follow-up metrics.
