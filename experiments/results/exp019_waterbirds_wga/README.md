# exp019: Waterbirds worst-group accuracy rerun

## Purpose
Posthoc recomputation of Waterbirds worst-group accuracy from the exp018 training setup.

## Inputs
- Config: `experiments/configs/exp018_waterbirds_30seeds.yaml`
- exp018 checkpoints: `experiments/results/exp018_waterbirds_30seeds/checkpoints/`

## Outputs
- `worst_group_results.csv`
- `worst_group_summary.txt`
- `fig_wga.png`
- `fig_wga.pdf`

## Main result
- mean worst_group_acc: 0.3424
- std worst_group_acc: 0.0804

## Runtime
- 30 seeds, 3 workers
- Wall-clock runtime recorded in `EXPERIMENT_MAP.md`

## Notes
- This directory is intentionally separate from exp018 so the WGA posthoc result stays reproducible and easy to cite.
- `plot_wga.py` is a small helper that turns `worst_group_results.csv` into a seed-wise figure for the manuscript.
