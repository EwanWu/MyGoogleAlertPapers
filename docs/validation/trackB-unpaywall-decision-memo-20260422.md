# Track B Unpaywall Decision Memo — corrected placement conclusion (20260422)

**Run tag:** `20260422_batch50`  
**Date:** 2026-04-22  
**Status:** ✅ decision closed

## Executive decision

Unpaywall should **not** be used as a candidate-level provider to try to replace or shrink the main bibliographic enrich stack.

It should be implemented as a **post-dedup OA enhancement step**.

Recommended production position: **`post_dedup`**.

## Why this changed

The first position summary had two methodological problems:

1. `unpaywall_only` fell back to builtin default merge rules and disabled `normalized_only_fallback`, so the first candidate-level downstream delta was confounded.
2. The first placement comparison only had candidate-level DOI cache coverage, so post-merge and post-dedup latency/coverage were undercounted.

The corrected analysis fixed both issues and is the only trusted basis for the final decision.

Canonical artifact:
- `docs/validation/unpaywall-position-batch50-summary-20260422_batch50-corrected.json`
- `docs/validation/unpaywall-position-batch50-summary-20260422_batch50-corrected.md`

## Batch and constraint

Because live IMAP selection failed with:

`EXAMINE Unsafe Login. Please contact kefu@188.com for help`

this experiment used the **oldest 50 locally cached Google Scholar mails** from the slice150 seed DB instead of newly fetched ~2-month-old mailbox data.

Batch facts:
- 50 mails
- span: `18-Mar-2026` → `02-Apr-2026`
- 188 candidates
- 88 DOI-positive normalized candidates
- paid LLM usage: **none**

## Current enrich baseline cost

Baseline (`conditional_sources_v2`) on this batch:
- total provider latency: **983,056 ms**
- canonical papers: **165**
- review queue: **2**

Main latency contributors:
- Crossref: `373,498 ms`
- OpenAlex: `173,804 ms`
- PubMed: `157,990 ms`
- Semantic Scholar: `150,632 ms`
- Europe PMC: `124,326 ms`

## Corrected candidate-level Unpaywall delta

When Unpaywall was added at candidate level under the corrected merge rules:
- canonical delta: **0**
- review delta: **0**
- normalized-only-fallback delta: **0**
- actual remote DOI requests: **76**
- cache hits: **12**
- added latency: **85,343 ms**
- added latency vs baseline enrich latency: **+8.68%**

Interpretation:
- candidate-level Unpaywall is **safe** at `SOURCE_PRIORITY=0`
- but it is **not a time-saving replacement** for existing providers
- and it only touches the subset of DOI-bearing items already visible at candidate stage

## Placement comparison

| placement | unique DOI | OA URL DOI | matched fill rate | estimated latency ms |
|---|---:|---:|---:|---:|
| candidate_level | 76 | 30 | 0.4225 | 85,343 |
| post_merge | 151 | 88 | 0.6069 | 161,336 |
| post_dedup | 150 | 87 | 0.6042 | 160,288 |

## Final interpretation

### What Unpaywall is good for
- OA status
- OA URL discovery
- post-hoc OA coverage enhancement for canonical papers with DOI

### What Unpaywall is not good for
- replacing Crossref / OpenAlex / Semantic Scholar / PubMed as bibliographic providers
- reducing current enrich latency
- improving canonical merge correctness in a material way

## Final recommendation

### 1. Keep Unpaywall out of the core bibliographic decision path
Do not treat it as a normal enrich provider for production runs.

### 2. Run it after dedup
Add a dedicated **post-dedup OA enrichment step** over `canonical_paper.canonical_doi`.

### 3. Keep the role narrow
Unpaywall remains:
- DOI-only
- OA-only
- non-authoritative for title/authors/year/venue/DOI selection

### 4. Prefer `post_dedup` over `post_merge`
`post_merge` and `post_dedup` have nearly identical coverage, but `post_dedup` is cleaner semantically because it enriches the final canonical paper set rather than an intermediate proposal set.

## Code direction adopted from this memo

Production path:
1. `normalize-candidates`
2. `enrich-candidates`
3. `merge-metadata`
4. `dedup-candidates`
5. `enrich-paper-oa`

This separates OA enhancement from bibliographic merge logic.

## Historical note

The earlier candidate-level integration remains useful as an experimental comparison arm, but it is no longer the recommended production implementation.
