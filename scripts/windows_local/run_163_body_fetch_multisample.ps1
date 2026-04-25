param(
    [string]$CdpEndpoint = 'http://127.0.0.1:9222',
    [string]$InputJsonl = 'data\raw_mail_exports\163_scholar_local\scholar_index.jsonl',
    [string]$OutputJsonl = 'data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl',
    [int]$SearchPageLimit = 6,
    [switch]$ResetOutput
)

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Set-Location $repo

$failureJsonl = 'data\raw_mail_exports\163_scholar_local\scholar_body_fetch_failures.jsonl'
$timingDir = 'data\raw_mail_exports\163_scholar_local\timing'
$timingJson = Join-Path $timingDir 'body_fetch_multisample_timing.json'
if ($ResetOutput) {
    Remove-Item $OutputJsonl -Force -ErrorAction SilentlyContinue
    Remove-Item $failureJsonl -Force -ErrorAction SilentlyContinue
    Remove-Item $timingJson -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $timingDir -Force | Out-Null

$batches = @(
    @{ Label = 'page1-mixed';            StartOffset = 0;   Limit = 6 },
    @{ Label = 'page1-new-article';      StartOffset = 38;  Limit = 1 },
    @{ Label = 'page2-mixed';            StartOffset = 100; Limit = 5 },
    @{ Label = 'page3-mixed-plus-new';   StartOffset = 190; Limit = 7 }
)

Write-Host 'Running 163 Scholar multi-sample smoke test...'
Write-Host "Repo: $repo"
Write-Host "Input JSONL: $InputJsonl"
Write-Host "Output JSONL: $OutputJsonl"
Write-Host "Failure JSONL: $failureJsonl"
Write-Host "Timing JSON: $timingJson"
Write-Host "Batches: $($batches.Count) (expected total targets = $((($batches | ForEach-Object { $_.Limit }) | Measure-Object -Sum).Sum))"

$runStartedAt = [DateTimeOffset]::UtcNow
$runSw = [System.Diagnostics.Stopwatch]::StartNew()
$batchResults = @()
$hadBatchFailure = $false

foreach ($batch in $batches) {
    Write-Host ''
    Write-Host ("=== Batch: {0} | start={1} limit={2} ===" -f $batch.Label, $batch.StartOffset, $batch.Limit)
    $batchStartedAt = [DateTimeOffset]::UtcNow
    $batchSw = [System.Diagnostics.Stopwatch]::StartNew()
    & powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 `
        -CdpEndpoint $CdpEndpoint `
        -InputJsonl $InputJsonl `
        -OutputJsonl $OutputJsonl `
        -Limit $batch.Limit `
        -StartOffset $batch.StartOffset `
        -SearchPageLimit $SearchPageLimit
    $batchExitCode = $LASTEXITCODE
    $batchSw.Stop()
    $batchCompletedAt = [DateTimeOffset]::UtcNow
    $batchResults += [pscustomobject]@{
        label = $batch.Label
        start_offset = $batch.StartOffset
        limit = $batch.Limit
        started_at = $batchStartedAt.ToString('o')
        completed_at = $batchCompletedAt.ToString('o')
        elapsed_seconds = [Math]::Round($batchSw.Elapsed.TotalSeconds, 3)
        exit_code = $batchExitCode
    }
    Write-Host ("Batch timing: label={0} elapsed_seconds={1:N3} exit_code={2}" -f $batch.Label, $batchSw.Elapsed.TotalSeconds, $batchExitCode)
    if ($batchExitCode -ne 0) {
        $hadBatchFailure = $true
        Write-Warning "Batch had partial failures and will be recorded, but the wrapper will continue: $($batch.Label)"
    }
}

$runSw.Stop()
$runCompletedAt = [DateTimeOffset]::UtcNow
$summary = [pscustomobject]@{
    started_at = $runStartedAt.ToString('o')
    completed_at = $runCompletedAt.ToString('o')
    elapsed_seconds = [Math]::Round($runSw.Elapsed.TotalSeconds, 3)
    input_jsonl = $InputJsonl
    output_jsonl = $OutputJsonl
    failure_jsonl = $failureJsonl
    timing_json = $timingJson
    batch_count = $batches.Count
    expected_target_count = (($batches | ForEach-Object { $_.Limit }) | Measure-Object -Sum).Sum
    avg_seconds_per_expected_target = [Math]::Round($runSw.Elapsed.TotalSeconds / ((($batches | ForEach-Object { $_.Limit }) | Measure-Object -Sum).Sum), 3)
    batches = $batchResults
    status = $(if ($hadBatchFailure) { 'completed_with_failures' } else { 'completed' })
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -Path $timingJson -Encoding UTF8

Write-Host ''
Write-Host 'Multi-sample body fetch batches completed.'
Write-Host "Success JSONL: $OutputJsonl"
Write-Host "Failure JSONL: $failureJsonl"
Write-Host ("Run timing: started={0} completed={1} elapsed_seconds={2:N3}" -f $runStartedAt.ToString('o'), $runCompletedAt.ToString('o'), $runSw.Elapsed.TotalSeconds)
Write-Host "Timing JSON: $timingJson"
if ($hadBatchFailure) {
    exit 1
}
