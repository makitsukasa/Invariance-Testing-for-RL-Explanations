# exp018: Waterbirds 30-seed run

## Purpose
Waterbirds spurious-feature detection experiment comparing Delta vs SHAP.

## Inputs
- Config: `experiments/configs/exp018_waterbirds_30seeds.yaml`
- Data root: `data/waterbirds/waterbird_complete95_forest2water2`

## Outputs
- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `stats.txt`
- `fig_scatter.pdf`, `fig_scatter.png`
- `fig_delta_dist.pdf`, `fig_delta_dist.png`
- `runtime_sessions.csv`
- `exp018_run.log`, `exp018_run.err`

## Main result
- Delta detect: 16/30 (53%)
- SHAP detect: 30/30 (100%)

## Notes
- Checkpoints are saved under `checkpoints/seed_{seed}.pt`.
- This run is the source of truth for the Waterbirds 30-seed comparison.
