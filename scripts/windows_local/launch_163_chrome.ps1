param(
    [int]$Port = 9222,
    [string]$ProfileDir = 'C:\temp\mgap-163-chrome-profile'
)

$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
if (-not (Test-Path $chrome)) {
    throw "Chrome not found at $chrome"
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

Write-Host "Launching Chrome with remote debugging on port $Port"
Write-Host "Profile dir: $ProfileDir"
Write-Host "Then manually log into 163 mail and complete any verification."

Start-Process -FilePath $chrome -ArgumentList @(
    "--remote-debugging-port=$Port",
    '--remote-debugging-address=127.0.0.1',
    "--user-data-dir=$ProfileDir",
    'https://mail.163.com/'
)
