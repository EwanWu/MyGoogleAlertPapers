param(
    [string]$CdpEndpoint = 'http://127.0.0.1:9222',
    [int]$PageLimit = 3
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

Write-Host "Running 163 scholar indexer..."
Write-Host "Repo: $repo"
Write-Host "CDP endpoint: $CdpEndpoint"
Write-Host "Page limit: $PageLimit"
Write-Host "Python launcher: $($pycmd -join ' ')"

& $exe @baseArgs .\scripts\windows_local\read_163_scholar_with_manual_pause.py run-index --cdp-endpoint $CdpEndpoint --page-limit $PageLimit
