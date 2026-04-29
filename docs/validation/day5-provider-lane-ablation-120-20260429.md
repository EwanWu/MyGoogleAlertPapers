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
| `identifier_plus_title_core` | 246 / 474 | 51.9% | 178 | 194 | 455.18 s | `crossref` title + `openalex` title |

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
   - main remaining cost center is `crossref` title latency, not `openalex` DOI batching
   - good candidate for the default synchronous extension after lane 1

3. **Lane 3/4: biomedical fallback + slow fallback**
   - should remain deferred / optional until explicitly budgeted
   - especially `semanticscholar` remains the first slow-lane provider to keep out of the synchronous default path

## Decision

Current evidence supports the following runtime strategy:

- **Do not go back to full-provider synchronous enrich.**
- Treat **`identifier_fastpath` as the guaranteed live base lane**.
- Treat **`identifier_fastpath + title_core` as the main candidate for the next live default experiment**.
- Keep `biomedical_fallback` and `slow_fallback` out of the default synchronous path for now.

## Next coding target

The next useful optimization target is no longer “provider on/off” in the abstract. It is specifically:

1. make lane execution first-class in reports and docs
2. add explicit per-lane budgets / stop conditions
3. reduce `crossref` title-lane wall time
4. only then revisit provider-specific concurrency or circuit breakers

## Artifact paths

- `config/policy_profiles/openalex_batching_identifier_fastpath.yaml`
- `config/policy_profiles/openalex_batching_identifier_plus_title_core.yaml`
- `docs/validation/day5-identifier-fastpath-120-20260429.json`
- `docs/validation/day5-identifier-plus-title-core-120-20260429.json`
