param(
    [string]$CdpEndpoint = 'http://127.0.0.1:9222',
    [string]$InputJsonl = 'data\raw_mail_exports\163_scholar_local\scholar_index.jsonl',
    [string]$OutputJsonl = 'data\raw_mail_exports\163_scholar_local\scholar_body_fetch.jsonl',
    [int]$Limit = 10,
    [int]$StartOffset = 0,
    [int]$SearchPageLimit = 6
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

Write-Host "Running 163 Scholar body-fetch sample..."
Write-Host "Repo: $repo"
Write-Host "CDP endpoint: $CdpEndpoint"
Write-Host "Input JSONL: $InputJsonl"
Write-Host "Output JSONL: $OutputJsonl"
Write-Host "Limit: $Limit"
Write-Host "Start offset: $StartOffset"
Write-Host "Search page limit: $SearchPageLimit"
Write-Host "Python launcher: $($pycmd -join ' ')"

$startedAt = [DateTimeOffset]::UtcNow
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $exe @baseArgs .\scripts\windows_local\read_163_scholar_with_manual_pause.py run-body-fetch --cdp-endpoint $CdpEndpoint --input-jsonl $InputJsonl --output-jsonl $OutputJsonl --limit $Limit --start-offset $StartOffset --search-page-limit $SearchPageLimit
$exitCode = $LASTEXITCODE
$sw.Stop()
$completedAt = [DateTimeOffset]::UtcNow
Write-Host ("Wrapper timing: started={0} completed={1} elapsed_seconds={2:N3}" -f $startedAt.ToString('o'), $completedAt.ToString('o'), $sw.Elapsed.TotalSeconds)
exit $exitCode
