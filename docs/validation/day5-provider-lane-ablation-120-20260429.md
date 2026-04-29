# Day 5 provider-lane ablation on slice120 (2026-04-29)

## Goal

Evaluate whether explicit runtime provider lanes can convert the current enrich timeout problem from a monolithic provider-fanout issue into a controllable staged pipeline.

This note compares two new lane-gated profiles against the previously established Day 4 reference point.

## Profiles tested

### 1) `openalex_batching_identifier_fastpath`
Enabled lanes:
- `identifier_fastpath`

Included work:
- DOI batch / DOI lookup (`openalex`, `crossref`)
- PMID lookup (`pubmed`, `europepmc`)
- arXiv identifier lookup

Excluded by lane gate:
- `title_core`
- `biomedical_fallback`
- `slow_fallback`

### 2) `openalex_batching_identifier_plus_title_core`
Enabled lanes:
- `identifier_fastpath`
- `title_core`

Included work:
- all identifier fastpath work above
- `crossref` title lookup
- `openalex` title lookup

Excluded by lane gate:
- `biomedical_fallback`
- `slow_fallback`

## Results

| profile | processed runnable intents | processed fraction | dispatch requests | matched source records | total batch duration | main latency source |
|---|---:|---:|---:|---:|---:|---|
| Day 4 no-`semanticscholar` reference | 325 / 354 | 91.8% | n/a | n/a | projected 10.79 min | mixed live fanout |
| `identifier_fastpath` | 100 / 474 | 21.1% | 46 | 94 | 69.75 s | `crossref` DOI |
| `identifier_plus_title_core` (slice120) | 246 / 474 | 51.9% | 178 | 194 | 455.18 s | `crossref` title + `openalex` title |
| `identifier_plus_title_core_budget60` | 172 / 474 | 36.3% | 106 | 145 | 250.67 s | `crossref` title (budget-capped) |
| `identifier_plus_title_core` (slice150 live) | 308 / 588 | 52.4% | 220 | 251 | 499.50 s | `crossref` title + `openalex` title |

## Direct observations

### `identifier_fastpath`
- Completed comfortably in about **1.16 min**.
- Only **46 dispatch requests** were needed for **100 processed intents**.
- `openalex` DOI batching remained cheap and effective.
- Coverage is too narrow for a standalone default: only **94 matched source records**.
- Mechanistically, this profile is a strong **lane-1 core**, not a full live default.

### `identifier_plus_title_core`
- Completed in about **7.59 min**, i.e. inside the 10-minute class budget that Day 4 was targeting.
- Processed **246 intents**, more than doubling the identifier-only lane while staying far below the previous timeout regime.
- `crossref` dominated latency:
  - `crossref`: **323311 ms** across **120 events**
  - `openalex`: **120390 ms** across **120 events**
- Shared-title reuse did help a bit:
  - `shared_title_reuse_group_count = 14`
  - `shared_title_reuse_request_savings = 14`
- But the main cost is still serialized title traffic, especially `crossref` title lookups.

### `identifier_plus_title_core_budget60`
- Completed in about **4.18 min**.
- Explicitly capped `title_core` at **60 dispatch requests**.
- Final lane stats showed:
  - `lane_dispatch_request_count.title_core = 60`
  - `lane_stop_reasons.title_core = request_budget_exhausted`
  - `lane_skipped_group_count.title_core = 72`
  - `lane_skipped_intents.title_core = 74`
- Coverage fell relative to the uncapped title-core run:
  - processed intents: **172 vs 246**
  - matched source records: **145 vs 194**
- But it reduced wall time materially:
  - **250.67 s vs 455.18 s**
- Mechanistically, this is the first proof that lane budgets are not just a config abstraction — they produce a clean, inspectable live stop boundary.

### Follow-up live validation: `identifier_plus_title_core` on slice150
- A closer-to-production live replay on the full slice150 seed also completed cleanly.
- Key output:
  - processed intents: **308 / 588**
  - dispatch requests: **220**
  - matched source records: **251**
  - canonical papers after merge/dedup: **130**
  - merge review queue: **0**
  - total batch duration: **499.50 s**
- Lane accounting remained coherent:
  - `lane_dispatch_request_count.identifier_fastpath = 62`
  - `lane_dispatch_request_count.title_core = 158`
  - `lane_elapsed_ms.identifier_fastpath = 85712`
  - `lane_elapsed_ms.title_core = 413686`
- Main cost center remained unchanged:
  - `crossref`: **336689 ms** across **150 events**
  - `openalex`: **144986 ms** across **150 events**
- This matters because the slice120 result was not a fragile small-sample artifact; the same lane shape still held on the larger live slice.

## Mechanistic interpretation

The lane split works.

It separates the enrich problem into three operationally different layers:

1. **Lane 1: identifier fastpath**
   - cheap
   - stable
   - high-confidence
   - suitable as guaranteed live core

2. **Lane 2: title core**
   - still viable for live execution on slice120
   - now supports explicit stop conditions, so it can be run either as a fuller synchronous lane or as a budget-capped extension
   - main remaining cost center is `crossref` title latency, not `openalex` DOI batching
   - good candidate for the default synchronous extension after lane 1

3. **Lane 3/4: biomedical fallback + slow fallback**
   - should remain deferred / optional until explicitly budgeted
   - especially `semanticscholar` remains the first slow-lane provider to keep out of the synchronous default path

## Decision

Current evidence supports the following runtime strategy:

- **Do not go back to full-provider synchronous enrich.**
- Treat **`identifier_fastpath` as the guaranteed live base lane**.
- **Promote `identifier_fastpath + title_core` to the recommended synchronous live default profile.**
- Treat **`openalex_batching_identifier_plus_title_core_budget60`** as the stricter fallback profile when wall-time headroom is tight or the operator wants an explicit stop boundary.
- Treat **lane budgets / stop conditions as promoted runtime control**, not just an experimental branch idea.
- Keep `biomedical_fallback` and `slow_fallback` out of the default synchronous path for now.

This is a **yes, but scoped** promotion:
- yes for the operational synchronous live path,
- not a claim that uncapped title-core should automatically handle every larger burst without operator judgment,
- and not a reason to postpone further `crossref` title-lane optimization.

## Next coding target

The next useful optimization target is no longer “provider on/off” in the abstract. It is specifically:

1. reduce `crossref` title-lane wall time inside the promoted synchronous default
2. tune `title_core` budget shape (request count and, if needed, runtime cap) against the promoted default
3. use the budgeted profile as an explicit degraded-safe mode, not as the primary default
4. only then revisit provider-specific concurrency or circuit breakers

## Artifact paths

- `config/policy_profiles/openalex_batching_identifier_fastpath.yaml`
- `config/policy_profiles/openalex_batching_identifier_plus_title_core.yaml`
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_budget60.yaml`
- `docs/validation/day5-identifier-fastpath-120-20260429.json`
- `docs/validation/day5-identifier-plus-title-core-120-20260429.json`
- `docs/validation/day5-identifier-plus-title-core-budget60-120-20260429.json`
- `docs/validation/day5-identifier-plus-title-core-live150-20260429.json`
- `docs/validation/day5-identifier-plus-title-core-live150-20260429.md`
