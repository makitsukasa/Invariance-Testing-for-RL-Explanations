Set-Location 'C:\Users\tsukasa\Documents\auto-spurious-discovery'
& 'C:\Users\tsukasa\Documents\auto-spurious-discovery\.venv\Scripts\python.exe' 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\entrypoints\run_gridworld_candidate_discovery.py' --config 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\configs\exp001_gridworld_candidate_discovery.yaml' --outdir 'experiments/results/exp001' 1>> 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\results\exp001\run.log' 2>> 'C:\Users\tsukasa\Documents\auto-spurious-discovery\experiments\results\exp001\run.err'
$exitCode = $LASTEXITCODE
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show('Experiment finished: experiments/results/exp001
exit=' + $exitCode, 'auto-spurious-discovery') | Out-Null
exit $exitCode
