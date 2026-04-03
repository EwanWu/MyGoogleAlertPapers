# Package 1 Spec: Enrichment Resumability Foundation

## Purpose
Define the first implementation package for the enrichment reliability hardening plan.

This package does **not** try to solve every enrichment correctness issue at once.
Its purpose is narrower and foundational:
- make enrichment progress explicit at the provider level
- support true checkpoint/resume behavior after interruption
- reduce repeated provider work caused by coarse candidate-level completion logic
- prepare the codebase for stronger cache authority and stricter merge protection in later packages

---

## 1. Problem statement

The current enrichment stage determines whether a candidate still needs work using a candidate-level query:
- if any `source_record` exists for that candidate, the candidate is no longer treated as unenriched

This causes a major resumability defect:
- Crossref may have succeeded
- OpenAlex may not have run yet
- PubMed may have failed or been interrupted
- a rerun can still skip the candidate entirely

As a result, current reruns are coarse and unsafe for long-running or interrupted enrichment batches.

---

## 2. Package-1 goals

### Required goals
1. Track enrichment progress per candidate *and* per provider.
2. Make reruns continue missing provider work instead of skipping partially enriched candidates.
3. Distinguish between these provider outcomes:
   - success with matched record
   - completed with no match
   - failed/error
   - pending/in-progress
4. Preserve compatibility with existing tables and reporting.
5. Keep implementation conservative and auditable.

### Explicit non-goals for Package 1
- no full redesign of merge confidence
- no severe-conflict canonicalization guardrail yet
- no provider batching beyond what already exists unless needed for integration
- no new external providers
- no broad schema migration framework beyond what is needed for this package

---

## 3. Proposed schema addition

## 3.1 New table: `candidate_enrichment_status`

Suggested schema:

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `candidate_id` TEXT NOT NULL
- `provider` TEXT NOT NULL
- `status` TEXT NOT NULL
- `query_type` TEXT
- `query_key` TEXT
- `source_record_id` INTEGER
- `cache_hit` INTEGER DEFAULT 0
- `attempt_count` INTEGER DEFAULT 0
- `last_started_at` TEXT
- `last_finished_at` TEXT
- `latency_ms` INTEGER
- `error_summary` TEXT
- `notes` TEXT
- `created_at` TEXT DEFAULT CURRENT_TIMESTAMP
- `updated_at` TEXT DEFAULT CURRENT_TIMESTAMP

### Recommended status values
- `pending`
- `ok`
- `no_match`
- `error`
- `skipped`

### Uniqueness rule
Add a unique index on:
- `(candidate_id, provider)`

This table represents the current best-known enrichment state for each provider/candidate pair.

---

## 3.2 Semantics of fields

### `candidate_id`
The normalized candidate being enriched.

### `provider`
One of the current providers:
- `pubmed`
- `crossref`
- `openalex`

### `status`
The latest provider-level state.

### `query_type`
Examples:
- `doi`
- `pmid`
- `title`
- `doi_batch`

### `query_key`
Canonical key used for the request intent.
This should later align with the authoritative cache normalization policy.

### `source_record_id`
Optional foreign reference to the inserted `source_record` row when the provider returns a result that is persisted.

### `cache_hit`
Whether the terminal state was resolved from cache instead of fresh external request.

### `attempt_count`
How many provider attempts have been made for this candidate/provider pair.

### `error_summary`
Short sanitized failure reason if status=`error`.

---

## 4. Interaction with existing tables

## 4.1 `source_record`
Remains the source-specific payload table.

`candidate_enrichment_status` does **not** replace `source_record`.
Instead:
- `source_record` stores what the provider returned
- `candidate_enrichment_status` stores whether that provider work is complete, pending, failed, or unresolved

### Rule
A provider can finish with `status=no_match` and still be treated as a valid completed provider state.

Current implementation note:
- for consistency and easier provenance/debugging, the first implementation pass now generally persists a `source_record` row even for `matched=0` / `no_match` outcomes, including the OpenAlex DOI-batch no-match path.
- this is an implementation choice, not a conceptual requirement of the status model.

---

## 4.2 `query_cache`
Package 1 does not fully redesign cache, but it should begin aligning status rows with cache use.

### Minimal Package-1 rule
Whenever cache is used to produce a provider outcome, record:
- `cache_hit=1`
- `status` based on cached result class

This creates the bridge for Package 2 cache hardening.

---

## 4.3 `batch_run`
No replacement needed.
`batch_run` continues to represent batch execution metadata.

Package 1 should continue recording enrichment run timing at the batch level.

---

## 4.4 `cost_event`
No replacement needed.
`cost_event` continues to log per-stage/per-provider activity.

Package 1 should log cost events at provider-level completion just as today, but now with provider-level status transitions driving the work.

---

## 5. Provider work planning model

For each candidate, enrichment should no longer ask “is this candidate enriched?”
It should ask:

> Which provider tasks remain unfinished for this candidate?

## 5.1 Provider worklist construction

For each candidate row from `paper_candidate_normalized`, construct provider intents:

### PubMed intent
Run if:
- `pmid_extracted` exists, or
- title path is allowed under the current heuristic

### Crossref intent
Run if:
- `doi_extracted` exists, or
- title path is allowed

### OpenAlex intent
Run if:
- `doi_extracted` exists, or
- title path is allowed

Each intent should have:
- `provider`
- `query_type`
- `query_key`
- provider-specific input arguments

---

## 5.2 Selection rules for Package 1 rerun behavior

For each candidate/provider intent:

### Run when
- no status row exists
- status row exists with `error` and retry policy allows rerun

### Skip when
- status=`ok`
- status=`no_match`
- status=`skipped`

### Optional later extension
A future `--force` mode may rerun `ok` or `no_match`, but that is not required for Package 1.

---

## 6. Status transition model

## 6.1 Normal provider lifecycle

### Case A: fresh external success with match
1. create/update status row to `pending`
2. increment `attempt_count`
3. record `last_started_at`
4. perform lookup
5. insert `source_record`
6. update status row to:
   - `status=ok`
   - `source_record_id=<id>`
   - `cache_hit=0`
   - `last_finished_at`
   - `latency_ms`

### Case B: fresh external completion with no match
1. set `pending`
2. perform lookup
3. no `source_record` inserted
4. update to:
   - `status=no_match`
   - `cache_hit=0`
   - `last_finished_at`
   - `latency_ms`

### Case C: fresh external failure
1. set `pending`
2. perform lookup
3. on exception or terminal failure, update to:
   - `status=error`
   - `error_summary=<short reason>`
   - `cache_hit=0`
   - `last_finished_at`
   - `latency_ms`

---

## 6.2 Cache-based lifecycle

### Case D: cache hit with matched record
1. create/update status row to `pending`
2. increment `attempt_count`
3. set `last_started_at`
4. load cached payload
5. insert or reuse `source_record` according to Package-1 implementation choice
6. update status to:
   - `status=ok`
   - `cache_hit=1`
   - `last_finished_at`
   - `latency_ms=0`

### Case E: cache hit with no-match payload
1. create/update status row to `pending`
2. load cached no-match payload
3. update status to:
   - `status=no_match`
   - `cache_hit=1`
   - `latency_ms=0`

### Case F: cache hit with cached error payload
Package 1 recommendation:
- do **not** automatically treat cached error as terminal completion forever
- store it as status=`error` with `cache_hit=1`
- allow retry policy to decide whether rerun should happen next time

---

## 7. Retry policy for Package 1

Package 1 should keep retry policy simple and explicit.

### Default retry rule
- rerun provider rows in `error`
- do not rerun `ok` or `no_match`

### No required backoff scheduler yet
Package 1 does not need a full cooldown system.
A simple immediate retry on next enrichment run is acceptable.

### Reason
The goal is correctness of resumability first, not optimal retry economics.

---

## 8. CLI behavior

Package 1 should preserve the existing command shape:
- `mgap enrich-candidates --limit N`

But the semantics should change.

### Old behavior
Select candidate rows lacking any `source_record`.

### New behavior
Select candidate rows that still have at least one provider intent requiring work.

### Practical interpretation of `--limit`
Package 1 should continue to interpret limit primarily at candidate level for user simplicity.
For each selected candidate, provider work may include 1–3 providers depending on status and available identifiers.

---

## 9. Migration and compatibility strategy

## 9.1 Existing databases
Package 1 should be compatible with already populated databases.

### Minimal compatibility rule
When a candidate/provider pair has no status row yet:
- do not assume existing `source_record` means globally complete
- instead, infer bootstrap state conservatively only when needed

## 9.2 Bootstrap options
Two acceptable strategies exist.

### Option A: lazy bootstrap (recommended)
When enrichment examines a candidate/provider pair with no status row:
- if a matching provider `source_record` already exists, initialize status row as `ok`
- otherwise treat as missing and eligible for work

### Option B: one-off migration backfill
Write a helper to backfill status rows from existing `source_record` contents before next enrichment run.

### Recommendation
Use **Option A first** because it is simpler and minimizes migration complexity.
A dedicated backfill command can be added later if needed.

---

## 10. Package-1 implementation outline

## 10.1 Schema work
1. add `candidate_enrichment_status` table
2. add unique index on `(candidate_id, provider)`
3. add repository helpers:
   - get status row
   - upsert pending state
   - finalize ok/no_match/error state
   - infer existing provider completion from `source_record` where needed

## 10.2 Pipeline work
Refactor `pipeline/enrich.py` into these logical steps:
1. list normalized candidates
2. build provider intents per candidate
3. filter intents using status rows and retry rules
4. run provider work one intent at a time
5. update status row and cost events
6. insert `source_record` when applicable

## 10.3 Logging/reporting work
No major new report is required in Package 1, but at minimum logs should make it easy to see:
- how many provider intents were planned
- how many were skipped due to completed status
- how many were retried from error
- how many ended as ok/no_match/error

---

## 11. Validation plan for Package 1

### Primary test
Use a fresh small validation DB on the `issac` mailbox.

### Required checks
1. Interrupt enrichment after partial completion.
2. Rerun enrichment.
3. Confirm only missing or error provider work resumes.
4. Confirm candidates with one completed provider are not incorrectly skipped in a partial state.
5. Confirm `ok`/`no_match` provider states are not repeatedly re-queried.

### Success criteria
- partial-run recovery works at provider level
- reruns no longer depend on “any source_record exists” logic
- repeated enrichment runs produce fewer unnecessary external requests
- logs and DB state make provider progress inspectable

### Initial validation status (2026-04-03)
Validated:
- provider-level status rows are created for planned provider intents on a fresh 10-mail `issac` slice
- completed rerun correctly reports `0 need work`
- `ok` and `no_match` states prevent unnecessary repeat work on rerun
- hard-kill testing preserved database consistency

Not yet fully achieved:
- a hard kill can still roll back the in-flight transaction before provider-level results are durably committed, so the current implementation is structurally resumable but not yet a finest-grained durable checkpoint system

---

## 12. Decision summary
Package 1 is the minimum structural change needed to make enrichment resumable in a principled way.

It should be implemented before:
- broader provider scaling
- severe conflict canonicalization guardrails
- advanced cache redesign

Without this package, enrichment remains operationally fragile for long-running and interrupted batch work.
