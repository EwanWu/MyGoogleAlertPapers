param(
    [string]$CdpEndpoint = 'http://127.0.0.1:9222',
    [string]$OutputJsonl = 'data\raw_mail_exports\163_scholar_local\scholar_body_fetch_sweep.jsonl',
    [int]$PageLimit = 1,
    [int]$MaxTargets = 20,
    [int]$StartPage = 1,
    [switch]$StartFromCurrentPage
)

function Get-PythonCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @('py', '-3')
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @('python')
    }
    throw 'No Windows Python launcher found. Install Python for Windows or enable the py launcher.'
}

$repo = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $repo
$pycmd = Get-PythonCommand
$exe = $pycmd[0]
$baseArgs = @()
if ($pycmd.Length -gt 1) {
    $baseArgs = $pycmd[1..($pycmd.Length-1)]
}

Write-Host "Running 163 Scholar sequential body-fetch sweep..."
Write-Host "Repo: $repo"
Write-Host "CDP endpoint: $CdpEndpoint"
Write-Host "Output JSONL: $OutputJsonl"
Write-Host "Page limit: $PageLimit"
Write-Host "Max targets: $MaxTargets"
if ($StartFromCurrentPage) {
    Write-Host 'Start mode: current visible inbox page (resume semantics)'
} else {
    Write-Host "Start page: $StartPage"
}
Write-Host "Python launcher: $($pycmd -join ' ')"

$scriptArgs = @(
    '.\scripts\windows_local\read_163_scholar_with_manual_pause.py',
    'run-body-sweep',
    '--cdp-endpoint', $CdpEndpoint,
    '--output-jsonl', $OutputJsonl,
    '--page-limit', $PageLimit,
    '--max-targets', $MaxTargets
)
if ($StartFromCurrentPage) {
    $scriptArgs += '--start-from-current-page'
} else {
    $scriptArgs += @('--start-page', $StartPage)
}

$startedAt = [DateTimeOffset]::UtcNow
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $exe @baseArgs @scriptArgs
$exitCode = $LASTEXITCODE
$sw.Stop()
$completedAt = [DateTimeOffset]::UtcNow
Write-Host ("Wrapper timing: started={0} completed={1} elapsed_seconds={2:N3}" -f $startedAt.ToString('o'), $completedAt.ToString('o'), $sw.Elapsed.TotalSeconds)
exit $exitCode
