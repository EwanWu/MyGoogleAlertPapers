# 163 body sweep state ↔ artifact reconciliation (2026-04-25)

## Purpose

Reconcile the mismatch between:

- state file `body_fetched_count = 10026`
- artifact file `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full.jsonl`
  - raw line count = `7628`
  - valid JSON records = `7626`

and determine the canonical import input for downstream `import-local-bodies` use.

## Files checked

- `data/task_state/163_mail_read_local_state.json`
- `data/task_state/163_mail_read_local_state.json.pre_full_sweep_20260424_193900`
- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full.jsonl`
- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_failures.jsonl`
- `scripts/windows_local/read_163_scholar_with_manual_pause.py`

## Key findings

### 1. `body_fetched_count` is cumulative across runs, not a row-count of the current output JSONL

The script increments `state.body_fetched_count += 1` on each successful body extraction, but it does **not** reset that counter when switching to a new output file.

Evidence from the pre-full-sweep snapshot:

- pre-full-sweep state: `body_fetched_count = 2389`
- pre-full-sweep `artifacts.body_jsonl = /tmp/body_sweep_main_script_test.jsonl`

Evidence from the current state:

- current state: `body_fetched_count = 10026`
- current `artifacts.body_jsonl = data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full.jsonl`

Therefore, the top-level mismatch is primarily explained by **state accumulation across multiple earlier runs / different output files**.

### 2. The full-run delta implied by state is `7637`, not `10026`

Using the snapshot taken immediately before the 2026-04-24 full run:

- `10026 - 2389 = 7637`

So the current full-run campaign should be reconciled against about `7637` new successful fetches, not against the total `10026` counter.

### 3. The current full artifact contains `7628` raw lines, but only `7626` valid JSON records

Audit of `scholar_body_fetch_20260424_full.jsonl` found:

- raw line count: `7628`
- valid JSON records: `7626`
- invalid lines: `2`
- invalid line numbers: `768`, `5966`
- both invalid lines are NUL-filled corrupted lines rather than JSON objects

A cleaned artifact has been written to:

- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full_reconciled.jsonl`

with:

- `7626` valid JSON records
- zero invalid lines

### 4. The residual delta after removing pre-run accumulation is small but real

Comparing the full-run state delta with the artifact:

- state-implied new successes: `7637`
- raw artifact lines: `7628`
- cleaned valid records: `7626`

Residual gap:

- `7637 - 7628 = 9`
- `7637 - 7626 = 11`

This means the major discrepancy is explained, but there is still a small unresolved gap inside the full run itself.

### 5. The residual gap is most plausibly artifact corruption / incomplete preservation, not duplicate inflation

Checks on the reconciled file show:

- duplicate `mail_uid`: `0`
- duplicate `mail_key`: `0`
- duplicate `raw_mail_key`: `0`

So the cleaned full artifact does **not** look inflated by duplicate rows.

The two invalid NUL lines strongly suggest that the artifact had at least some write/corruption event(s). There are also visible timestamp jumps across those corruption sites, which makes it plausible that a small number of successful fetches counted in state were not preserved cleanly in the final JSONL.

I cannot prove the exact missing-record count from the artifact alone, but the remaining `9–11` record gap is small enough that the main reconciliation conclusion is stable.

## Range actually covered by the reconciled full artifact

The cleaned artifact spans:

- first valid record: `2026-04-24T11:39:27.612376+00:00`, page `12`
- last valid record: `2026-04-24T17:40:34.264482+00:00`, page `93`
- unique pages covered: `12..93` (82 pages)

So this file is a deep-page sweep artifact for the `12 -> 93` range, not a universal total-history body export.

## Canonical import input decision

For downstream import / early-ingest, the canonical input should be:

- **`data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full_reconciled.jsonl`**

Reason:

1. it is the current full-run artifact referenced by state
2. it has been cleaned to remove the two corrupted non-JSON lines
3. it contains `7626` structurally valid, non-duplicate records
4. it is a safer import target than the raw `full.jsonl`

The raw source file should still be retained for provenance:

- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full.jsonl`

but it should be treated as the **raw acquisition artifact**, not the canonical import input.

## Recommended interpretation going forward

### Known
- `10026` is **not** the canonical row count for the current full artifact.
- The current importable full artifact is `7626` valid records after reconciliation.
- The state counter includes historical earlier runs from other output targets.

### Inferred
- The remaining `9–11` record mismatch likely comes from partial artifact corruption or preservation loss during the full run.

### Operational rule
- For any downstream `import-local-bodies` or reproducible validation, use the reconciled file, not the raw state count and not the raw `full.jsonl`.

## Produced artifacts

- Reconciled canonical JSONL:
  - `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full_reconciled.jsonl`
- Machine-readable summary:
  - `data/task_state/163_body_sweep_reconciliation_20260425.json`
