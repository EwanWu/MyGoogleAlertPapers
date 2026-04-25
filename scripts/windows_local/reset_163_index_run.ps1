$repo = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $repo

$state = Join-Path $repo 'data\task_state\163_mail_read_local_state.json'
$index = Join-Path $repo 'data\raw_mail_exports\163_scholar_local\scholar_index.jsonl'
$archiveDir = Join-Path $repo 'data\raw_mail_exports\163_scholar_local\archive'
New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

if (Test-Path $index) {
    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dst = Join-Path $archiveDir "scholar_index_$ts.jsonl"
    Move-Item $index $dst
    Write-Host "Archived old index -> $dst"
} else {
    Write-Host 'No existing index file to archive.'
}

if (Test-Path $state) {
    Remove-Item $state
    Write-Host "Removed state file -> $state"
} else {
    Write-Host 'No existing state file to remove.'
}

Write-Host 'Reset complete. In Chrome, navigate back to the unread-mail first page, then rerun run_163_index.ps1.'
