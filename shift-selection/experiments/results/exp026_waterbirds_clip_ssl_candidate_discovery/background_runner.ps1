Set-Location 'C:\Users\tsukasa\Documents\rl-shift-auto-detection'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
& 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\.venv\Scripts\python.exe' 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\run_waterbirds_representation_candidate_discovery.py' --config 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\configs\exp026_waterbirds_clip_ssl_candidate_discovery.yaml' --outdir 'experiments/results/exp026_waterbirds_clip_ssl_candidate_discovery' --no-resume 1>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp026_waterbirds_clip_ssl_candidate_discovery\run.log' 2>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp026_waterbirds_clip_ssl_candidate_discovery\run.err'
`$exitCode = $LASTEXITCODE
exit `$exitCode
