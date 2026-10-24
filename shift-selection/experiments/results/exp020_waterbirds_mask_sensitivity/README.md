# exp020: Waterbirds mask sensitivity

## Purpose
Evaluate how robust Delta is to GrabCut mask perturbations on Waterbirds.

## Inputs
- Config: `experiments/configs/exp020_waterbirds_mask_sensitivity.yaml`
- Source checkpoints: `experiments/results/exp018_waterbirds_30seeds/checkpoints/`

## Outputs
- `results.csv`
- `fig_mask_sensitivity.png`
- `summary.txt`

## Result
- Seed: `0`
- Validation accuracy: `0.8215`
- Mask radii: `[-3, -1, 0, 1, 3]`
- Decision flips (`delta_bg <= delta_fg`): `0/5`
- Across all radii, `delta_bg > delta_fg`

## Notes
- This experiment checks whether small mask dilation/erosion changes the Delta decision.
- It reuses exp018 checkpoints rather than retraining the oracle.
- The observed decision stayed stable under the tested perturbation range.
