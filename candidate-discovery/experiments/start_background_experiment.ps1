param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath,

    [Parameter(Mandatory = $true)]
    [string]$OutDir,

    [string]$EntryPoint = "experiments/entrypoints/run_gridworld_candidate_discovery.py",

    [switch]$NoResume
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path ".").Path
$python = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$entry = (Resolve-Path $EntryPoint).Path
$config = (Resolve-Path $ConfigPath).Path

$resolvedOutDir = Join-Path $repoRoot $OutDir
if (-not (Test-Path -LiteralPath $resolvedOutDir)) {
    New-Item -ItemType Directory -Path $resolvedOutDir -Force | Out-Null
}

$stdoutLog = Join-Path $resolvedOutDir "run.log"
$stderrLog = Join-Path $resolvedOutDir "run.err"
$launcherLog = Join-Path $resolvedOutDir "launcher.log"
$runnerScript = Join-Path $resolvedOutDir "background_runner.ps1"

$pythonLine = "& '$python' '$entry' --config '$config' --outdir '$OutDir'"
if ($NoResume) {
    $pythonLine += " --no-resume"
}
$pythonLine += " 1>> '$stdoutLog' 2>> '$stderrLog'"

$runnerLines = @(
    "Set-Location '$repoRoot'"
    $pythonLine
    '$exitCode = $LASTEXITCODE'
    'Add-Type -AssemblyName PresentationFramework'
    "[System.Windows.MessageBox]::Show('Experiment finished: $OutDir`nexit=' + `$exitCode, 'auto-spurious-discovery') | Out-Null"
    'exit $exitCode'
)

$runnerLines | Set-Content -Path $runnerScript -Encoding UTF8

$proc = Start-Process -WindowStyle Hidden -PassThru -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $runnerScript
)

@(
    "started_at=$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))"
    "pid=$($proc.Id)"
    "config=$config"
    "entry=$entry"
    "outdir=$resolvedOutDir"
    "stdout=$stdoutLog"
    "stderr=$stderrLog"
    "runner_script=$runnerScript"
) | Set-Content -Path $launcherLog -Encoding UTF8

Write-Output $proc.Id
