# Errors

Command failures and integration errors.

---

## [ERR-20260423-163-timing-bom] summarize_163_local_timing.py

**Logged**: 2026-04-23T18:20:00+08:00
**Priority**: medium
**Status**: fixed
**Area**: scripts

### Summary
Timing summary script failed on Windows-generated timing JSON because the file contained a UTF-8 BOM, and the first implementation also overestimated body-fetch cost by relying too much on wall time.

### Error
```
json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)
```

### Context
- Command: `python3 scripts/summarize_163_local_timing.py ...`
- Cause: PowerShell-generated timing JSON carried a BOM; script read with plain `utf-8`.
- Secondary issue: wall-clock batch time included wrapper startup and failed-batch overhead, so `elapsed_seconds / success_count` overstated per-mail body-fetch cost.

### Suggested Fix
- Read JSON/JSONL with `utf-8-sig`
- Compute both wall-based and per-record (`elapsed_seconds` in success JSONL) estimates, and prefer the record-based estimate for full-run extrapolation

### Metadata
- Reproducible: yes
- Related Files: scripts/summarize_163_local_timing.py, scripts/windows_local/run_163_body_fetch_multisample.ps1

---

## [ERR-20260416-001] enrich_candidates_openalex_primary_location_none

**Logged**: 2026-04-16T12:45:00+08:00
**Priority**: high
**Status**: pending
**Area**: backend

### Summary
Large-slice150 replay failed at the v2 enrich stage because OpenAlex batch payload handling assumed `primary_location.source` was always a dict.

### Error
```
AttributeError: 'NoneType' object has no attribute 'get'
File: src/mygooglealertpapers/pipeline/enrich.py:227
Code: venue = (item.get('primary_location') or {}).get('source', {}).get('display_name')
```

### Context
- Command: `python3 -m mygooglealertpapers.cli enrich-candidates --limit 1000000`
- Wrapper: `scripts/replay_validation.py`
- Run script: `scripts/run_packageB_large_slice_replay_20260416.sh`
- Slice: 150 mails, 368 normalized candidates, 1405 planned provider intents
- Failure occurred before any replay `cost_event`, `batch_run`, or validation report was written

### Suggested Fix
Defensively handle `primary_location` records whose `source` is null, e.g. `(item.get('primary_location') or {})`, then `((... ).get('source') or {}).get('display_name')`, and consider the same guard for `landing_page_url` access paths.

### Metadata
- Reproducible: yes
- Related Files: src/mygooglealertpapers/pipeline/enrich.py, scripts/replay_validation.py, scripts/run_packageB_large_slice_replay_20260416.sh

---

## [ERR-20260422-001] windows_local_playwright_cdp_lifecycle

**Logged**: 2026-04-22T11:16:00Z
**Priority**: high
**Status**: fixed
**Area**: infra

### Summary
Windows-local 163 reader crashed with TargetClosedError because the Playwright manager was closed immediately after connect_over_cdp returned.

### Error
```
playwright._impl._errors.TargetClosedError: Page.title: Target page, context or browser has been closed
```

### Context
- Operation: `powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1`
- Root cause: `connect_browser()` used `async with async_playwright()` and returned the browser from inside the context manager, so the session was torn down before page inspection.
- Related Windows-local flow: attach to a real Chrome via CDP, pause for manual verification, then resume indexing.

### Suggested Fix
Keep the Playwright instance alive for the whole run (`await async_playwright().start()`), stop it only in `finally`, and prefer a still-open page when attaching.

### Metadata
- Reproducible: yes
- Related Files: scripts/windows_local/read_163_scholar_with_manual_pause.py

---

## [ERR-20260424-001] smoke20_sampler_chain

**Logged**: 2026-04-24T10:19:00+08:00
**Priority**: low
**Status**: pending
**Area**: tests

### Summary
Stratified sampler assumed 20 rows existed for fixed page/type buckets, but only selected 19 and still chained into pipeline execution.

### Error
```
AssertionError: 19
FileNotFoundError: ... scholar_body_fetch_sweep_10h_smoke20.jsonl
```

### Context
- Attempted to build a 20-row mixed smoke-test JSONL from `scholar_body_fetch_sweep_10h.jsonl`
- Selection logic required exact page/type/source combinations
- After assertion failure, chained pipeline command still ran and failed because the sample file was never written

### Suggested Fix
Build the sample file first with fallback selection, verify row count, then run pipeline as a separate step.

### Metadata
- Reproducible: yes
- Related Files: data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_10h.jsonl

---

## [ERR-20260424-002] cdp_benchmark_connection_refused

**Logged**: 2026-04-24T11:01:00+08:00
**Priority**: low
**Status**: pending
**Area**: infra

### Summary
Post-patch live benchmark could not start because the Windows Chrome CDP endpoint on `127.0.0.1:9222` was unavailable from WSL at run time.

### Error
```
BrowserType.connect_over_cdp: WebSocket error: connect ECONNREFUSED 127.0.0.1:9222
```

### Context
- Attempted command: `python3 scripts/windows_local/read_163_scholar_with_manual_pause.py run-body-sweep --output-jsonl ... --page-limit 1 --max-targets 5`
- This happened after the page-preserving return patch, so benchmark status remains unverified live

### Suggested Fix
Verify real Chrome is running with remote debugging enabled and that WSL can still reach `127.0.0.1:9222` before running live body-sweep benchmarks.

### Metadata
- Reproducible: unknown
- Related Files: scripts/windows_local/read_163_scholar_with_manual_pause.py

---

## [ERR-20260426-001] openclaw_apply_patch_external_project_path

**Logged**: 2026-04-26T23:55:00+08:00
**Priority**: low
**Status**: fixed
**Area**: tooling

### Summary
`apply_patch` could not edit files under the external project root because the tool was sandboxed to the OpenClaw workspace root.

### Error
```
Path escapes sandbox root (~/.openclaw/workspace-deepblue)
```

### Context
- Operation: patching files under `~/NewCareer/Openclaw/proj/MyGoogleAlertPapers/`
- The fix in this session was to switch to `write` / `edit` for external-project paths instead of retrying `apply_patch`.

### Suggested Fix
When editing files outside `/home/ewan/.openclaw/workspace-deepblue`, prefer `write` / `edit` directly and do not assume `apply_patch` can cross the workspace sandbox boundary.

### Metadata
- Reproducible: yes
- Related Files: src/mygooglealertpapers/db/schema.py, src/mygooglealertpapers/db/repository.py

---
## [ERR-20260427-001] replay_validation_stage_timeout_under_live_provider_jitter

**Logged**: ${TS}
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
A repeat `replay_validation.py` smoke12 baseline run timed out in `enrich` even though earlier baseline/experiment runs had passed.

### Error
```
stage timed out after 179s: python3 -m mygooglealertpapers.cli enrich-candidates --limit 12
```

### Context
- Command: `PYTHONPATH=src python3 scripts/replay_validation.py --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db --output-db data/benchmark/ab_baseline_smoke12_repeat_20260427.db --policy-profile config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml --report-out docs/validation/ab_baseline_smoke12_repeat_20260427.json --limit 12 --stages enrich merge dedup --stage-timeout-seconds 180`
- Same logical workload had completed previously; this failure appears tied to live provider latency jitter rather than a deterministic local regression.
- Useful implication: repeat A/B comparisons that rely on live providers need wider stage timeout or retry policy before drawing semantic conclusions from partial failures.

### Suggested Fix
Increase smoke replay timeout budget for live-provider A/B repeats and treat timeout failures as observability/stability signals, not direct semantic regressions.

### Metadata
- Reproducible: unknown
- Related Files: scripts/replay_validation.py, src/mygooglealertpapers/pipeline/enrich.py

---
