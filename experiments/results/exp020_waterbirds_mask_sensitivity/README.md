# exp020: Waterbirds mask sensitivity

## Purpose
Evaluate how robust Delta is to GrabCut mask perturbations on Waterbirds.

## Planned inputs
- Config: `experiments/configs/exp020_waterbirds_mask_sensitivity.yaml`
- Source checkpoints: `experiments/results/exp018_waterbirds_30seeds/checkpoints/`

## Planned outputs
- `results.csv`
- `fig_mask_sensitivity.png`
- `summary.txt`

## Notes
- This experiment is designed to test whether small mask dilation/erosion changes the Delta decision.
- It reuses exp018 checkpoints rather than retraining the oracle.
