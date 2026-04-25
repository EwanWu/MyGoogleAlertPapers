# 163 mail local-read workflow (manual verification + resumable)

## Goal

Read 163 mailbox content on the **Windows local machine** using a **real Chrome session**, pause when manual verification/login is required, then resume unfinished indexing work after the human finishes verification.

This workflow exists because:
- IMAP is blocked by 163 risk control on the current US egress IP
- WSL-side browser automation can open the login page but cannot reliably pass verification or reuse the authenticated Windows Chrome session
- The stable path is therefore: **Windows real Chrome login** -> **local controlled extraction** -> **sync outputs back into the repo**

## Files

- Launcher: `scripts/windows_local/launch_163_chrome.ps1`
- Runner: `scripts/windows_local/run_163_index.ps1`
- Body-fetch sample runner: `scripts/windows_local/run_163_body_fetch_sample.ps1`
- Body-fetch sweep runner: `scripts/windows_local/run_163_body_fetch_sweep.ps1`
- Status checker: `scripts/windows_local/check_163_index_status.ps1`
- Page counter / diagnostics: `scripts/windows_local/count_163_scholar_page.ps1`
- Controller: `scripts/windows_local/read_163_scholar_with_manual_pause.py`
- State file: `data/task_state/163_mail_read_local_state.json`
- Output index: `data/raw_mail_exports/163_scholar_local/scholar_index.jsonl`
- Body output: `data/raw_mail_exports/163_scholar_local/scholar_body_fetch.jsonl`
- Body-fetch failures: `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_failures.jsonl`
- Diagnostics: `data/raw_mail_exports/163_scholar_local/diagnostics/`
- Validation note: `docs/validation/163-local-scholar-index-validation-20260423.md`

## Current validated state (2026-04-23)

The workflow has now been validated on the current 163 inbox layout.

- 3-page unread Scholar index result: `277` rows
- Per-page counts: `94 / 96 / 87`
- Page-size setting during validation: `100` rows/page
- Page-1 counting validation: `total_letter_nodes_visible=100`, `scholar_sender_visible=94`, `unique_scholar_sequence_dedup_across_scan=94`
- Cross-page overlap check: `mail_key` and `sequence_key` overlap were both `0` across `1-2`, `1-3`, and `2-3`

Current interpretation: the 277-row run is a credible 3-page index result for the present layout, not the earlier undercounted `135` regression.

## Recommended execution order on Windows

### 1. Start a dedicated Chrome profile with remote debugging

In PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\launch_163_chrome.ps1
```

This opens a **dedicated** Chrome profile at `C:\temp\mgap-163-chrome-profile`.

### 2. Human login / verification

In that Chrome window:
- log into `mail.163.com`
- complete slider or any additional verification
- land in inbox or mail UI
- keep the browser open

### 3. Run the controller

In the repo root on the same Windows machine:

```bash
python scripts/windows_local/read_163_scholar_with_manual_pause.py run-index --cdp-endpoint http://127.0.0.1:9222 --page-limit 3
```

Behavior:
- if login/verification is still needed, the script exits with `waiting_manual_verification`
- it writes screenshot/html diagnostics
- after human finishes verification, rerun the **same command**
- if inbox is accessible, it extracts visible rows and appends them to `scholar_index.jsonl`

### 4. Check state

```bash
python scripts/windows_local/read_163_scholar_with_manual_pause.py status
```

### 5. Reset state if needed

```bash
python scripts/windows_local/read_163_scholar_with_manual_pause.py reset
```

## Important limitations

### Current extractor stage

The current script is a **resumable execution controller + calibrated Scholar list indexer** for the validated 163 layout.
It does **not yet** guarantee perfect selector coverage on every possible 163 layout.

What it now solves on the validated layout:
- manual verification checkpoint
- resumable state file
- diagnostics capture when blocked
- first-pass extraction of Scholar candidate rows across full in-DOM page rows, not just the current viewport
- page-by-page indexing loop with checkpoint updates
- local-sequence-based dedupe across scroll snapshots

What required live calibration and is now explicitly fixed:
- viewport-only filtering that collapsed page counts to about `45` rows
- overly narrow subject filtering that missed the major Scholar subtype `新的相关研究工作`

What still needs further work:
- live validation of the new body-fetch path on the current 163 layout
- body extraction at scale
- full end-to-end replay against more 163 layout variants
- any search/filter selector specific to future 163 UI changes

## Why this is still the right first artifact

For the 8000+ mail problem, the first priority is not full-body extraction.
The first priority is:
1. stable authenticated access
2. resumable indexing
3. evidence capture when blocked
4. checkpoint-safe continuation after manual intervention

This artifact is designed for exactly that.

## Operational guidance

- Prefer indexing first, not opening thousands of bodies immediately.
- Keep batch size small at first, e.g. `--page-limit 3`.
- If 163 triggers another verification wall, finish it manually and rerun.
- If extraction quality is poor, inspect diagnostics and calibrate selectors on the live inbox DOM.
- If a future run regresses toward about `135` rows for 3 pages, first suspect selector regression rather than missing pagination.
- Use `count_163_scholar_page.ps1 -ScrollSteps 12` before deeper debugging when you need to distinguish:
  - page-size / DOM exposure problems
  - undercount from filtering
  - duplicate inflation during scroll-based indexing

## Body-fetch sweep path (current default for larger runs)

The current recommended wrapper for larger body-fetch runs is:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -PageLimit 12 -MaxTargets 200
```

New start semantics are now supported directly in the wrapper:

### Start from a specific inbox page

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartPage 12 -PageLimit 1 -MaxTargets 20
```

Use this when you already know the next work should begin from page `N` and you do not want to repay the traversal cost from page 1.

### Resume from the currently visible inbox page

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartFromCurrentPage -PageLimit 1 -MaxTargets 20
```

Use this when the real Chrome window is already parked on the target inbox page and you want explicit resume semantics.

### Direct Python equivalents

```bash
python scripts/windows_local/read_163_scholar_with_manual_pause.py run-body-sweep --start-page 12 --page-limit 1 --max-targets 20
python scripts/windows_local/read_163_scholar_with_manual_pause.py run-body-sweep --start-from-current-page --page-limit 1 --max-targets 20
```

Behavior:
- sweep rows from the chosen start page forward for `page_limit` pages
- prefer `history.back()` after each opened mail to preserve the current page
- only fall back to `goto(inbox_url)` if page preservation fails
- writes import-local-bodies-compatible rows to the target JSONL
- writes failures plus diagnostics to `scholar_body_fetch_failures.jsonl`
- prints `return_method_counts` so live runs can confirm whether page-preserving return is actually being used

## CDP note for WSL-driven control

If you are running the control side from WSL instead of native Windows PowerShell, be careful: WSL proxy variables can make `http://127.0.0.1:9222/json/version` look reachable while CDP WebSocket traffic still fails.

On the current machine, the reliable path was:
- Windows Chrome listens on `127.0.0.1:9222`
- Windows `portproxy` exposes `0.0.0.0:9223 -> 127.0.0.1:9222`
- WSL connects to `http://<WindowsHostIP>:9223`

Do not assume HTTP reachability to `/json/version` implies Playwright CDP will work from WSL.

## Older small-sample body-fetch path

For tiny validation samples, the old sample runner still exists:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -Limit 10
```

Direct Python:

```bash
python scripts/windows_local/read_163_scholar_with_manual_pause.py run-body-fetch --limit 10
```

This path starts from `scholar_index.jsonl` and searches by subject/date. It remains useful for narrow smoke tests, but for larger or resumed runs the sweep wrapper above is now the preferred entrypoint.
