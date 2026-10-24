Set-Location 'C:\Users\tsukasa\Documents\rl-shift-auto-detection'
& 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\.venv\Scripts\python.exe' 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\run_gridworld_candidate_discovery_noise_p_sweep.py' --config 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\configs\exp024_gridworld_candidate_discovery_noise_p_sweep.yaml' --outdir 'experiments\results\exp024_gridworld_candidate_discovery_noise_p_sweep' 1>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp024_gridworld_candidate_discovery_noise_p_sweep\run.log' 2>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp024_gridworld_candidate_discovery_noise_p_sweep\run.err'
$exitCode = $LASTEXITCODE
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('Experiment finished: experiments\results\exp024_gridworld_candidate_discovery_noise_p_sweep
exit=' + $exitCode, 'rl-shift-auto-detection') | Out-Null
exit $exitCode
