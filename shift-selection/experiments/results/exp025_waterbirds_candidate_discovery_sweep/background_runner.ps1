Set-Location 'C:\Users\tsukasa\Documents\rl-shift-auto-detection'
& 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\.venv\Scripts\python.exe' 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\run_waterbirds_candidate_discovery_sweep.py' --config 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\configs\exp025_waterbirds_candidate_discovery_sweep.yaml' --outdir 'experiments/results/exp025_waterbirds_candidate_discovery_sweep' 1>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp025_waterbirds_candidate_discovery_sweep\run.log' 2>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp025_waterbirds_candidate_discovery_sweep\run.err'
$exitCode = $LASTEXITCODE
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('Experiment finished: experiments/results/exp025_waterbirds_candidate_discovery_sweep
exit=' + $exitCode, 'rl-shift-auto-detection') | Out-Null
exit $exitCode
