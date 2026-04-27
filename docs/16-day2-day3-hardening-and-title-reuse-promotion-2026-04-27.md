# Day 2/Day 3 hardening and title-reuse promotion summary (2026-04-27)

## Purpose

This is the new top-level summary for the 2026-04-26 -> 2026-04-27 execution window.

It replaces the need to reconstruct the current state from many stepwise Day 2 / Day 3 notes.

Read this first if you need:
1. what changed in the implementation,
2. what is now the current default runtime behavior,
3. what evidence is canonical,
4. what should happen next.

## One-line status

The project is now in:

> **default-flow operational hardening with request-scheduling optimizations promoted into the mainline**

The core policy default is still:

> `conditional_sources_v2 + author_blob_fallback_only + post-dedup enrich-paper-oa`

But the runtime layer is no longer the same as the 2026-04-22 state. It now includes stricter intake, benchmark/replay baselines, safer enrichment dispatch/cache semantics, and default-enabled narrow-scope title payload reuse.

## What this phase delivered

### 1. Day 2 correctness / operator boundary work is complete

- `163` local body JSONL intake now has an explicit validation boundary.
- corrupt-line handling, valid/invalid counting, and canonical `_reconciled.jsonl` preference are implemented.
- benchmark/replay baseline generation is standardized through `benchmark-baseline`.

### 2. Day 3 enrichment runtime work is complete in first production form

- a minimal shared provider HTTP client now exists for `crossref`, `openalex`, and `semanticscholar`
- enrichment planning/reporting now quantifies:
  - total provider intents
  - dedup-only request count
  - recommended request count
  - batching opportunities
  - execution recommendations
- enrich execution now includes:
  - safe dispatch dedup
  - context-aware cache keys via `field_set_hash`
  - dispatch/accounting summaries written into `batch_run.notes`

### 3. Title payload reuse has now cleared promotion

Current promoted behavior:
- for duplicated **title** queries on `crossref`, `openalex`, and `semanticscholar`
- share only the provider fetch/payload
- keep per-candidate build / match / cache decisions separate

This is a request-scheduling optimization, not a match-standard relaxation.

## Current default interpretation

### Policy default
- `conditional_sources_v2_author_blob_fallback_only`

### Runtime default additions now assumed
- OpenAlex DOI batching remains enabled
- safe dispatch dedup remains enabled
- context-aware cache keys remain enabled
- **title payload reuse is now enabled by default** for:
  - `crossref`
  - `openalex`
  - `semanticscholar`

## Why title payload reuse is now promoted

### Mechanism constraint
The promoted version is intentionally narrow:
- shared fetch only
- no shared accept/match decision
- no relaxed merge/dedup rule
- no widened provider scope

### Canonical evidence

#### Live A/B conclusion
Live smoke A/B showed that request reuse was real and visible, but provider jitter made `matched_source_record_count` unsuitable as the final judge.

Support memo:
- `docs/validation/archive/day3-runtime-optimization-20260427/day3-title-payload-reuse-ab-summary-20260427.md`

#### Deterministic conclusion
The promotion decision is based on recorded-payload replay, not live jitter.

Canonical decision artifact:
- `docs/validation/recorded_deterministic_ab_medium60_20260427.md`

Key result on the larger deterministic sample (`limit=60`):
- `matched_source_record_count = 137` vs `137`
- `merged_metadata_proposal_count = 60` vs `60`
- `normalized_only_fallback_proposal_count = 7` vs `7`
- `canonical_paper_count = 51` vs `51`
- `merge_review_queue_count = 2` vs `2`
- candidate-level semantic changed count = `0`

Observed experiment-only savings on that same fixture:
- `shared_title_reuse_group_count = 12`
- `shared_title_reuse_intent_count = 24`
- `shared_title_reuse_request_count = 12`
- `shared_title_reuse_request_savings = 12`

Interpretation:
- the optimization is doing real work
- the optimization did not change enrich/merge/dedup semantics on the fixed recorded sample

## Canonical evidence set for this phase

Read in this order:

1. `docs/16-day2-day3-hardening-and-title-reuse-promotion-2026-04-27.md`
2. `docs/validation/day2-benchmark-baseline-20260426.md`
3. `docs/validation/day3-enrichment-plan-snapshot-slice150-20260427.md`
4. `docs/validation/day3-crosscheck-merge-dedup-20260427.md`
5. `docs/validation/day3-crosscheck-enrich-smoke12-20260427.md`
6. `docs/validation/day3-dispatch-report-smoke12-20260427.md`
7. `docs/validation/recorded_deterministic_ab_medium60_20260427.md`

## Implementation commits already landed in this phase

- `03db1fa` — `feat: harden local import and add benchmark baseline`
- `e0e4311` — `feat: add provider http client and enrichment plan report`
- `005f8a1` — `feat: add enrichment plan recommendations and crosschecks`
- `0b2caf7` — `feat: add safe dispatch dedup for enrichment`
- `3f4c6bd` — `feat: add context-aware enrichment cache keys`
- `650b3af` — `feat: add HTTP fixture record/replay and title payload reuse optimization`

## What changed in the documentation layer

This phase produced too many stepwise notes to keep all of them in the active layer.

So the documentation rule is now:
- keep only the decision-grade summaries in active `docs/validation/`
- move raw control/treatment dumps and intermediate A/B artifacts into archive
- keep this document as the active phase summary

## Remaining next step

The project should now shift from “should we enable this optimization?” to:

1. keep replay-based regression discipline for future runtime optimizations
2. spend the next round on higher-yield batching/scheduling opportunities that still preserve semantic comparisons
3. avoid reopening broad matching heuristics without fixed-seed replay evidence
