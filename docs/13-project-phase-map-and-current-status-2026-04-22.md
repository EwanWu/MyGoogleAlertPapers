# Project phase map and current status (updated 2026-04-27)

## Purpose

This is the current top-level entry for the project after Track A, Track B, and the integrated mainline validation.

Read this first if you need the shortest path to:
1. current default strategy
2. what has been decided and frozen
3. what remains open
4. what evidence is canonical

## One-line status

The project is now in:

> **default-flow operational hardening / request-scheduling optimization promotion**

The pipeline is no longer mainly exploring strategy space. The current work is about locking one coherent default path, hardening the operator/runtime boundary around it, and only promoting narrow request-efficiency optimizations after deterministic replay evidence.

## Current default pipeline

`Google Scholar alert emails -> candidate extraction -> normalization -> bibliographic enrich -> merge -> dedup -> post-dedup OA enhancement`

Operationally:
1. `scan-mailbox`
2. `parse-mails`
3. `normalize-candidates`
4. `enrich-candidates`
5. `merge-metadata`
6. `dedup-candidates`
7. `enrich-paper-oa`

Runtime defaults now additionally assume:
- safe dispatch dedup
- context-aware enrichment cache keys
- OpenAlex DOI batching
- title payload reuse enabled by default for `crossref` / `openalex` / `semanticscholar`

## Stable project decisions

### 1. Bibliographic baseline stays on `conditional_sources_v2`
Broader fallback-tightening variants did not survive larger fixed-seed comparison.

### 2. Track A retained patch is narrow and late
The only Track A patch worth keeping is:
- `conditional_sources_v2_author_blob_fallback_only`

Its role is not broad anti-garbage filtering. Its role is to block one narrow bad-shape class only at final `normalized_only` fallback acceptance.

### 3. Track B is now closed
Unpaywall should not be used as a normal candidate-level enrich provider.

Its retained production role is:
- post-dedup OA enhancement over canonical DOI

## What the latest integrated validation established

Using reused source records to eliminate live-provider variability:
- Track A treatment removed the target garbage case only
- no collateral-loss candidates were introduced
- review burden did not worsen
- severe DOI conflict burden did not worsen
- post-dedup OA stage added 156 OA URLs on 263 canonical DOI-carrying papers

Canonical integrated validation artifact:
- `docs/validation/mainline-summary-20260422_mainline.md`

## Active document set to read now

1. `docs/16-day2-day3-hardening-and-title-reuse-promotion-2026-04-27.md`
2. `docs/13-project-phase-map-and-current-status-2026-04-22.md`
3. `docs/14-mainline-promotion-memo-2026-04-22.md`
4. `docs/11-packageB-decision-memo-2026-04-16.md`
5. `docs/12-packageB-phase-summary-and-archive-guide-2026-04-16.md`
6. `docs/09-packageA-implementation-and-replay-results-2026-04-15.md`
7. `docs/validation/trackA-author-blob-fb-decision-20260421c.md`
8. `docs/validation/trackB-unpaywall-decision-memo-20260422.md`
9. `docs/validation/mainline-summary-20260422_mainline.md`

## What is still open

The main unresolved problem is no longer whether narrow Day 3 runtime optimizations should ship. The current unresolved problem is **generalization plus higher-yield scheduling/batching**.

The next useful validation is:
- preserve the current promoted mainline/runtime defaults
- run them on a genuinely fresh slice or a larger fixed slice
- prioritize higher-yield request-reduction opportunities that can still be judged by fixed-seed replay

## What should not be reopened casually

Do not reopen these as default-policy questions unless new evidence appears:
- broad `low_source_title_similarity` blocking
- broad `sparse_metadata_low_source_title_similarity` blocking
- candidate-level Unpaywall as a production enrich provider
- Track A matching-time author-blob filtering
