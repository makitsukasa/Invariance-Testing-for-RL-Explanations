Set-Location 'C:\Users\tsukasa\Documents\auto-spurious-discovery'
& 'C:\Users\tsukasa\Documents\auto-spurious-discovery\.venv\Scripts\python.exe' 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\entrypoints\run_gridworld_candidate_discovery_noise_p_sweep.py' --config 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\configs\exp002_gridworld_noise_p_sweep.yaml' --outdir 'experiments/results/exp002' 1>> 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\results\exp002\run.log' 2>> 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\results\exp002\run.err'
$exitCode = $LASTEXITCODE
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('Experiment finished: experiments/results/exp002
exit=' + $exitCode, 'auto-spurious-discovery') | Out-Null
exit $exitCode
