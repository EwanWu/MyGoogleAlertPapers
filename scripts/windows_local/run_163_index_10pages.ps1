$repo = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $repo
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1 -PageLimit 10
