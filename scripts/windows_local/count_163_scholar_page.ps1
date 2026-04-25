param(
    [string]$CdpEndpoint = 'http://127.0.0.1:9222',
    [int]$ScrollSteps = 0
)

function Get-PythonCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @('py', '-3') }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @('python') }
    throw 'No Windows Python launcher found.'
}

$repo = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $repo
$pycmd = Get-PythonCommand
$exe = $pycmd[0]
$baseArgs = @()
if ($pycmd.Length -gt 1) { $baseArgs = $pycmd[1..($pycmd.Length-1)] }
& $exe @baseArgs .\scripts\windows_local\count_163_scholar_page.py --cdp-endpoint $CdpEndpoint --scroll-steps $ScrollSteps
