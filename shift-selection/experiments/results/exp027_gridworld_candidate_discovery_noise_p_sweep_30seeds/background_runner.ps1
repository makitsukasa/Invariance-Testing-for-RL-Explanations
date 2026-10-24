Set-Location 'C:\Users\tsukasa\Documents\rl-shift-auto-detection'
& 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\.venv\Scripts\python.exe' 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\run_gridworld_candidate_discovery_noise_p_sweep.py' --config 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\configs\exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds.yaml' --outdir 'experiments\results\exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds' 1>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds\run.log' 2>> 'C:\Users\tsukasa\Documents\rl-shift-auto-detection\experiments\results\exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds\run.err'
$exitCode = $LASTEXITCODE
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('Experiment finished: experiments\results\exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds
exit=' + $exitCode, 'rl-shift-auto-detection') | Out-Null
exit $exitCode
