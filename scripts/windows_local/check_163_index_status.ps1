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
& $exe @baseArgs .\scripts\windows_local\read_163_scholar_with_manual_pause.py status
