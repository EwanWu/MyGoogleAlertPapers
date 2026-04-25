# 163 local Scholar index validation (2026-04-23)

## Scope

Validate the Windows-local 163 mail indexing path for unread Google Scholar alerts after repeated undercount regressions.

## Final result

The calibrated 3-page run is now producing a credible index.

- final 3-page index count: `277`
- page breakdown: `94 / 96 / 87`
- page-size setting during validation: `100` rows per page
- output file: `data/raw_mail_exports/163_scholar_local/scholar_index.jsonl`

## Evidence chain

### 1. Single-page counting validation

Command used:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\count_163_scholar_page.ps1 -ScrollSteps 12
```

Observed on page 1:

- `total_letter_nodes_visible = 100`
- `scholar_sender_visible = 94`
- `dedup_within_snapshot = 94`
- `unique_scholar_sequence_dedup_across_scan = 94`

Interpretation:

- the page already exposes all 100 row nodes in DOM
- scroll did not reveal additional Scholar rows beyond those 94
- page 1 likely really contains 94 unread Scholar mails out of 100 rows

### 2. Final 3-page index output

Command used:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\reset_163_index_run.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1 -PageLimit 3
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\check_163_index_status.ps1
```

Observed result:

- `indexed_count = 277`
- `page_no = 3`
- page counts from `scholar_index.jsonl`: `94 / 96 / 87`

### 3. Composition by Scholar alert subtype

- page 1: `43 related_work + 1 new_article + 46 citations = 94`
- page 2: `46 related_work + 0 new_article + 44 citations = 96`
- page 3: `39 related_work + 3 new_article + 41 citations = 87`

Here `related_work` refers to rows whose subjects contain `新的相关研究工作`.

### 4. Cross-page dedupe sanity check

Cross-page overlap checks returned zero in this run:

- `mail_key`: `1-2 = 0`, `1-3 = 0`, `2-3 = 0`
- `sequence_key`: `1-2 = 0`, `1-3 = 0`, `2-3 = 0`

Interpretation:

- no obvious repeated page content was being counted across pages
- the final `277` result does not look inflated by the current dedupe logic

## Root causes found during debugging

### Root cause A. Viewport-only row filtering

Earlier runs regressed to about `135` rows for 3 pages because the indexer only accepted nodes intersecting the current viewport.

Effect:

- per-page counts collapsed to about `45`
- off-viewport rows already present in DOM were ignored

Fix applied:

- accept non-hidden, non-zero-size letter rows even when off-viewport

### Root cause B. Overly narrow Scholar subject filtering

Earlier filtering only reliably matched:

- `新增了 X 次引用`
- `新文章`
- `相关文章`

This missed a major alert subtype:

- `新的相关研究工作`

Effect:

- a large fraction of valid Scholar rows were silently dropped
- a 3-page rerun still stayed at `135` even after fixing viewport handling

Fix applied:

- keep the sender filter for `Google 学术搜索快讯`
- replace the narrow subtype keyword whitelist with a simpler inbox-row gate using `[收件箱]`

### Root cause C. Dedupe had to be stronger than single-title matching

Because title-only dedupe can collapse distinct mails with similar subjects, the scripts were upgraded to use a local sequence key built from:

- center mail
- previous 3 mails
- next 3 mails

This `sequence_key` is now used for cross-scroll dedupe.

## Operational takeaway

If a future 3-page run regresses toward about `135`, check in this order:

1. single-page count with `count_163_scholar_page.ps1 -ScrollSteps 12`
2. whether page-level visible Scholar count is already near the expected range
3. whether subject filtering is excluding a major Scholar subtype again
4. whether dedupe or pagination is actually implicated

## Current status

This 163 local Scholar list indexing workflow should now be treated as:

- validated for the current inbox layout
- suitable as the baseline index step before body extraction
- documented in:
  - `runbooks/163-local-mail-read-runbook-2026-04-22.md`
  - `scripts/windows_local/README.md`
