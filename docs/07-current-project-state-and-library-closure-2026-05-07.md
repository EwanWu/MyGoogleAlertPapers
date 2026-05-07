# Current project state and library closure (2026-05-07)

## Purpose

This is the current top-level state document for the project after the 2026-05-07 documentation cleanup.

Read this first if you need the present posture rather than the full historical decision trail.

## Project posture

The project is no longer in broad bulk-build mode.

Current posture:

> **Mainline library build is complete enough for the current cycle; residual tail is formally closed; reopening requires an explicit scope change.**

That means:

- no routine `chunk08+` continuation;
- no default reopening of parked residual items;
- no further tail rescue unless policy changes explicitly.

## Current confirmed library state

- `canonical_papers = 14638`
- `candidate_paper_links = 64478`
- `review_queue_total = 12`
- `unlinked_total = 50`
- after manual standard-entry insertion, the remaining working residual was reduced to `42`

## What was finalized in this cycle

### 1. Regular mainline closure

The regular fast-pass / chunk-style mainline was effective through the productive middle phase, but by the tail it was exhausted.

Operational conclusion:

- the mainline build path has already delivered its useful gain;
- additional regular chunk continuation is not justified;
- `chunk08+` should not be resumed under the current policy.

### 2. Residual-tail disposition

The remaining tail was split into two final dispositions:

#### A. Archived but not ingested

For the **13 thesis/dissertation-like PDFs already downloaded locally**:

- keep the PDFs as external archived assets;
- do **not** create canonical library records for them in this cycle;
- remove them from the active residual queue.

#### B. Discarded from active queue

For the other **29** leftovers:

- stop further salvage / merge / rescue work;
- keep historical evidence for auditability;
- treat them as intentionally closed under the current scope.

Important interpretation:

- “discard / 扔掉” here means **workflow discard**;
- it does **not** mean deleting PDFs, exports, or historical notes.

## What remains active now

What remains active is no longer large-scale build execution, but:

- maintaining the project’s stable documentation layer;
- preserving reproducible evidence;
- reopening only when a new scope is chosen.

Examples of valid future scope changes:

- thesis/dissertation ingestion becomes in-scope;
- multilingual expansion becomes in-scope;
- a special-topic salvage pass is explicitly requested.

## Canonical supporting documents

- documentation map and archive guide: `docs/08-documentation-map-and-archive-guide-2026-05-07.md`
- active validation map: `docs/validation/README.md`
- archive index: `docs/archive/README.md`
- validation archive index: `docs/validation/archive/README.md`

## Historical source trail for this closure

The detailed intermediate memos used to reach this final state were retained under:

- `docs/archive/closure-intermediates-20260507/`

In particular:

- `30-current-library-build-status-and-tail-issues-2026-05-07.md`
- `31-residual-tail-priority-worklist-2026-05-07.md`
- `32-final-residual-disposition-rule-2026-05-07.md`
- `33-library-build-sync-brief-2026-05-07.md`
