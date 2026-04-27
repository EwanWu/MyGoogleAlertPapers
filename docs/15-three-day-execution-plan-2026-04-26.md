# Three-day execution plan (2026-04-26)

> Execution outcome note (2026-04-27): this plan has now been executed for the Day 2 / Day 3 hardening window. Read `docs/16-day2-day3-hardening-and-title-reuse-promotion-2026-04-27.md` for the consolidated result and current default interpretation.

## Purpose

This document turns the 2026-04-26 blueprint report into a **short-horizon execution plan** that can be followed directly by a human developer or AI agent.

It is intentionally narrower than the blueprint.

The goal for the next 3 days is **not** to finish the whole architecture. The goal is to:

1. harden correctness and idempotency,
2. make the ingestion artifacts safer,
3. create the minimum benchmarking and runtime structure needed for the next round of enrich optimization.

## Current baseline that must not be casually changed

Keep the current mainline as-is unless fresh replay evidence says otherwise:

- `conditional_sources_v2`
- `author_blob_fallback_only`
- `post-dedup enrich-paper-oa`

Do **not** use this 3-day window to reopen:

- broad fallback-tightening policy exploration,
- candidate-level Unpaywall as a bibliographic provider,
- merge/dedup heuristic expansion without replay,
- Google Scholar search-page scraping,
- UI / export / service-layer expansion.

## What success looks like after 3 days

At the end of these 3 days, the project should have:

1. safer cache semantics for provider failures,
2. harder SQLite-level idempotency and connection discipline,
3. a validated artifact intake boundary for 163 local body JSONL,
4. a reproducible benchmark/replay baseline,
5. the first minimal provider runtime abstraction,
6. a first enrichment-plan skeleton that reveals where dedup/batching opportunities actually are.

---

# Day 1 — Correctness floor: cache semantics + SQLite hardening

## Day 1 objective

Prevent the system from silently poisoning itself.

This day is the highest priority. Speed work should not go ahead until these items are in place.

## Task 1A — Fix provider error cache semantics

### Why

Current risk: transient provider errors may be written into `query_cache` and later behave like authoritative `no_match` results.

This is a P0 correctness bug.

### Primary files

- `src/mygooglealertpapers/db/schema.py`
- `src/mygooglealertpapers/db/repository.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/pipeline/paper_oa.py`
- `src/mygooglealertpapers/enrich/base.py` (only if a status-carrying payload helper is needed)

### Required changes

#### Schema

Extend `query_cache` so cache entries carry state, not just raw JSON.

Minimum fields to add:

- `cache_status`
- `http_status`
- `error_type`
- `expires_at`
- `field_set_hash`

`field_set_hash` can default to `'default'` initially if the planner work is not yet done.

#### Repository semantics

Replace the current "store raw response JSON and assume that is enough" approach with explicit cache-state logic.

Minimum semantics:

- `positive_match` -> cache allowed, longer TTL
- `permanent_no_match` -> cache allowed, shorter TTL
- `transient_error` -> **must not be read as no-match**
- expired entry -> ignore and re-request

#### Pipeline behavior

In `pipeline/enrich.py` and `pipeline/paper_oa.py`:

- cache read path must reject transient error cache rows,
- cache write path must not turn provider exceptions into valid negative evidence,
- OA path should follow the same semantics as bibliographic enrich.

### Tests required

Prefer adding focused tests rather than trying to prove this only by manual run:

- new or expanded tests near:
  - `tests/test_paper_oa_pipeline.py`
  - a new enrich-cache regression test file if needed

Minimum regression case:

1. simulate provider exception,
2. run pipeline once,
3. rerun,
4. verify provider is retried rather than skipped because of cached pseudo-no-match.

### Acceptance criteria

- provider transient error is never treated as stable `no_match`
- rerun after transient error issues a fresh provider request
- no existing tests regress

---

## Task 1B — SQLite connection discipline + uniqueness hardening

### Why

Too much idempotency currently depends on pipeline order rather than database guarantees.

### Primary files

- `src/mygooglealertpapers/db/schema.py`
- `src/mygooglealertpapers/db/repository.py`
- any direct `sqlite3.connect(...)` callers that bypass repository defaults, especially under:
  - `src/mygooglealertpapers/pipeline/*.py`
  - selected helper/report scripts only if they participate in write flows

### Required changes

#### Connection defaults

In the repository connection path, set at minimum:

- `PRAGMA foreign_keys = ON`
- `PRAGMA journal_mode = WAL`
- `PRAGMA busy_timeout = 5000`

If there are write paths bypassing repository connection helpers, either route them through the repository helper or clearly mark them read-only.

#### Unique / partial-unique indexes

Add the most valuable idempotency constraints first.

Priority list:

- mail ingestion uniqueness
- raw snapshot uniqueness
- candidate normalization uniqueness
- merged proposal uniqueness
- candidate-to-paper link uniqueness
- partial unique indexes on canonical DOI / PMID / PMCID where non-null and non-empty

### Tests required

Use the smallest meaningful checks:

- same-ingest rerun should not duplicate rows
- foreign key enforcement should remain on
- current policy/merge tests should still pass

Useful existing files to extend:

- `tests/test_policy_and_merge_fallback.py`
- `tests/test_paper_oa_pipeline.py`

### Acceptance criteria

- repeated runs do not create duplicate canonical identity rows
- DB behavior is stricter even if pipeline order changes or reruns happen
- baseline tests still pass

---

## Day 1 suggested command block

```bash
cd ~/NewCareer/Openclaw/proj/MyGoogleAlertPapers
PYTHONPATH=src python -m pytest tests -q
```

If a narrower fast loop is useful during development, also run the targeted cache/idempotency subset before the full test suite.

## Day 1 stop point

Stop Day 1 only when:

- error-cache semantics are repaired,
- SQLite PRAGMA + core unique indexes are in place,
- tests pass.

---

# Day 2 — 163 artifact intake boundary + reproducible benchmark baseline

## Day 2 objective

Make the validated 163 local path safe to consume repeatedly, and create a stable baseline for later performance work.

## Task 2A — Formalize the 163 artifact intake boundary

### Why

The project has already validated 163 local body fetch as feasible, but artifact reliability remains weaker than the rest of the pipeline.

We now know:

- state counts can drift from artifact counts,
- large JSONL artifacts can contain corrupt lines,
- reconciled artifacts are safer than raw artifacts.

### Primary files

- `src/mygooglealertpapers/pipeline/local_import.py`
- `src/mygooglealertpapers/cli.py`
- optionally a new helper script under `scripts/` if validation/quarantine is easier to maintain there
- possibly small updates to runbooks if the ingest entry changes materially

### Required changes

At minimum, the import path should explicitly support:

- pre-import validation of JSONL structure,
- counting valid vs invalid lines,
- quarantine / skip behavior for corrupt lines,
- explicit use of canonical reconciled artifact as import input when applicable.

This does **not** require solving every future sharding/manifest problem right now.

Short-term target:

- importer can safely consume a large artifact even if a few corrupt lines exist,
- operator can see exactly what was skipped and why.

### Tests / verification required

Use the reconciled-vs-raw lesson directly:

- test a file with valid JSONL + a corrupt line
- confirm importer does not silently miscount or explode the whole run
- confirm skipped/corrupt counts are surfaced clearly

### Acceptance criteria

- corrupt JSONL lines are detected and surfaced
- importer does not silently treat bad lines as valid records
- canonical import input rule is documented and enforceable

---

## Task 2B — Freeze a benchmark/replay baseline

### Why

Future enrich optimization must be measured against a known baseline, not intuition.

### Primary files

- likely new script(s) under `scripts/`
- existing replay/validation entrypoints as needed
- optionally a short validation note under `docs/validation/` if the baseline is formalized enough

### Required output

Create or standardize the command entrypoints for three classes of evaluation:

1. small fixed slice
2. large fixed slice
3. fresh slice (or best currently available fresh-like cached slice)

Each benchmark/replay should at least report:

- candidate count
- provider intent count
- canonical count
- review queue count
- severe DOI conflict count
- provider latency summary
- cache-hit / rerun behavior if applicable

### Acceptance criteria

- there is a reproducible baseline command set
- later optimization PRs can be compared to it without guesswork

---

## Day 2 suggested command block

Use the exact benchmark commands finalized in Task 2B, but end the day with at least:

```bash
cd ~/NewCareer/Openclaw/proj/MyGoogleAlertPapers
PYTHONPATH=src python -m pytest tests -q
```

and one successful artifact-validation/import smoke run.

## Day 2 stop point

Stop Day 2 only when:

- 163 artifact intake is safer and explicit,
- a repeatable benchmark baseline exists,
- tests still pass.

---

# Day 3 — Minimal provider runtime abstraction + enrichment-plan skeleton

## Day 3 objective

Do the smallest amount of runtime restructuring that improves observability and prepares future speed work without forcing a full concurrency rewrite.

## Task 3A — Minimal unified provider HTTP client

### Why

Provider runtime discipline is currently too fragmented.

The first goal is **not** maximum speed. The first goal is consistent behavior:

- timeouts
- retries
- backoff
- headers
- API identity
- 429 / Retry-After handling

### Primary files

- new file: `src/mygooglealertpapers/enrich/http_client.py`
- likely touch:
  - `src/mygooglealertpapers/enrich/crossref.py`
  - `src/mygooglealertpapers/enrich/openalex.py`
  - `src/mygooglealertpapers/enrich/semanticscholar.py`
  - `src/mygooglealertpapers/enrich/pubmed.py`
  - `src/mygooglealertpapers/enrich/europepmc.py`
  - `src/mygooglealertpapers/enrich/arxiv.py`
  - `src/mygooglealertpapers/enrich/unpaywall.py`
- `src/mygooglealertpapers/config.py` if provider identity/config fields need expansion

### Minimum feature set

- common User-Agent injection
- provider-specific API key / email / tool wiring
- timeout handling
- retry on selected statuses
- Retry-After support
- backoff + jitter
- structured request result / error classification

Do **not** force a full async rewrite in this 3-day window.

A conservative synchronous client with clean semantics is enough.

### Acceptance criteria

- at least one or two key providers are migrated cleanly first
- runtime behavior is more consistent and measurable than before
- no quality regression is introduced

---

## Task 3B — Enrichment plan skeleton (plan first, run later)

### Why

Before building provider lanes or aggressive batching, the system needs to expose its real enrichment shape.

### Primary files

- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/cli.py`
- `src/mygooglealertpapers/db/schema.py` only if a minimal persistent plan/intention table is introduced immediately
- optional new script/report helper under `scripts/`

### Required output

Implement the smallest useful version of an enrichment planner.

At minimum, it should be able to answer:

- how many candidate-driven intents exist now,
- how many unique intents would remain after global dedup,
- how many are identifier-driven vs title-search driven,
- which providers dominate total intent volume.

This can begin as a report-producing command before it becomes a persistent multi-stage execution framework.

Examples of acceptable early deliverables:

- `plan-enrichment`
- `report-enrichment-plan`

### Acceptance criteria

- planner can reveal real dedup/batching opportunities
- next-step provider-lane work becomes evidence-driven rather than speculative

---

## Day 3 suggested command block

At minimum:

```bash
cd ~/NewCareer/Openclaw/proj/MyGoogleAlertPapers
PYTHONPATH=src python -m pytest tests -q
```

plus one benchmark/replay comparison using the Day 2 baseline.

## Day 3 stop point

Stop Day 3 only when:

- a minimal provider HTTP abstraction exists,
- an enrichment-plan skeleton or report exists,
- the system is better instrumented for the next optimization wave.

---

# What not to do in this 3-day window

Do **not** spend these 3 days on:

- Gmail watch / history sync implementation
- full provider-lane concurrency runner
- search UI / review UI / export UI
- large merge/dedup policy rewrites
- new broad policy experiments
- service-layer refactoring
- knowledge-base integrations

Those are real future tasks, but they are not the best use of the next 3 days.

---

# Recommended file/module execution map

## Day 1

### Must touch
- `src/mygooglealertpapers/db/schema.py`
- `src/mygooglealertpapers/db/repository.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/pipeline/paper_oa.py`

### Likely tests
- `tests/test_paper_oa_pipeline.py`
- new cache/idempotency regression tests as needed

## Day 2

### Must touch
- `src/mygooglealertpapers/pipeline/local_import.py`
- `src/mygooglealertpapers/cli.py`
- selected script(s) under `scripts/` for validation/benchmark entrypoints

### Likely docs
- one short validation note if benchmark baseline is formalized

## Day 3

### Must touch
- `src/mygooglealertpapers/enrich/http_client.py` (new)
- selected provider modules under `src/mygooglealertpapers/enrich/`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/cli.py`

### Optional schema touch
- only if the planner is persisted immediately rather than reported ephemerally

---

# Minimal daily acceptance checklist

## End of Day 1
- [ ] error cache semantics fixed
- [ ] transient error no longer behaves like no-match
- [ ] SQLite PRAGMAs and core uniqueness constraints hardened
- [ ] tests pass

## End of Day 2
- [ ] 163 artifact validation/quarantine boundary exists
- [ ] canonical import path is explicit and safe
- [ ] benchmark baseline commands are reproducible
- [ ] tests pass

## End of Day 3
- [ ] unified provider HTTP behavior exists in minimal form
- [ ] enrichment-plan skeleton/report exists
- [ ] at least one benchmark comparison confirms no obvious regression
- [ ] tests pass

---

# Recommended execution order for the next session

If an AI agent or human picks this up cold, use this order:

1. `docs/README.md`
2. `docs/13-project-phase-map-and-current-status-2026-04-22.md`
3. `docs/14-mainline-promotion-memo-2026-04-22.md`
4. `docs/15-three-day-execution-plan-2026-04-26.md`
5. `docs/validation/mainline-summary-20260422_mainline.md`
6. `docs/validation/163-local-body-sweep-and-ingest-validation-20260424.md`
7. `docs/validation/163-body-sweep-state-artifact-reconciliation-20260425.md`

Then begin Day 1.
