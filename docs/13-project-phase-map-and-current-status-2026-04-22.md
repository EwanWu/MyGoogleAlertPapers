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

## Recent hardening phase now absorbed into the mainline view

The 2026-04-26 -> 2026-04-27 Day 2 / Day 3 execution window should be read as a completed **development phase**, not as a separate long-lived document layer.

What that phase added to the current project state:
- safer local `163` JSONL intake with explicit validation / corrupt-line handling / reconciled-artifact preference
- reproducible benchmark/replay baseline entrypoints
- minimal shared provider HTTP runtime for key providers
- enrichment-plan reporting for dedup / batching opportunity measurement
- safe dispatch dedup and context-aware cache semantics in enrich execution
- deterministic recorded-payload replay as the standard judge for narrow runtime-optimization promotion
- default-enabled narrow-scope title payload reuse after semantic replay confirmation

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

## Canonical runtime-promotion evidence added in this phase

The current runtime-default additions are justified by a smaller but decision-grade evidence set:
- `docs/validation/day2-benchmark-baseline-20260426.md`
- `docs/validation/day3-enrichment-plan-snapshot-slice150-20260427.md`
- `docs/validation/day3-crosscheck-merge-dedup-20260427.md`
- `docs/validation/day3-crosscheck-enrich-smoke12-20260427.md`
- `docs/validation/day3-dispatch-report-smoke12-20260427.md`
- `docs/validation/recorded_deterministic_ab_medium60_20260427.md`
- `docs/validation/day5-provider-lane-ablation-120-20260429.md`
- `docs/validation/day5-identifier-plus-title-core-live150-20260429.md`

What these established:
- Day 2 operator-boundary hardening is in place and regression-tested
- Day 3 dispatch/cache/runtime changes did not break the validated merge/dedup path
- narrow-scope title payload reuse was promoted only after deterministic recorded-payload replay showed zero candidate-level semantic drift on the medium60 comparison
- explicit runtime lane gating is now viable: `identifier_fastpath` is a stable live core, and `identifier_fastpath + title_core` has now completed a closer-to-production slice150 live replay cleanly enough to justify promotion as the recommended synchronous default profile
- that promotion is no longer only documentary: the builtin CLI default and baseline helper default have been rebound to the `identifier_fastpath + title_core` profile, so default runs now execute the staged live path rather than the older full-provider synchronous fanout
- explicit per-lane stop conditions are now also viable: a budget-capped `title_core` run stops cleanly, records its stop reason in dispatch stats, and yields a controllable coverage/runtime tradeoff instead of a timeout boundary

## Active document set to read now

1. `docs/13-project-phase-map-and-current-status-2026-04-22.md`
2. `docs/14-mainline-promotion-memo-2026-04-22.md`
3. `docs/11-packageB-decision-memo-2026-04-16.md`
4. `docs/12-packageB-phase-summary-and-archive-guide-2026-04-16.md`
5. `docs/09-packageA-implementation-and-replay-results-2026-04-15.md`
6. `docs/validation/recorded_deterministic_ab_medium60_20260427.md`
7. `docs/validation/day3-enrichment-plan-snapshot-slice150-20260427.md`
8. `docs/validation/day3-crosscheck-merge-dedup-20260427.md`
9. `docs/validation/day3-dispatch-report-smoke12-20260427.md`
10. `docs/validation/trackA-author-blob-fb-decision-20260421c.md`
11. `docs/validation/trackB-unpaywall-decision-memo-20260422.md`
12. `docs/validation/mainline-summary-20260422_mainline.md`

## What is still open

The main unresolved problem is no longer whether staged live lanes are viable. That part is now established. The current unresolved problem is **how to keep the promoted `identifier_fastpath + title_core` default fast enough under wider live bursts, mainly by controlling `crossref` title-lane cost and budget shape**.

The next useful validation is:
- preserve the current promoted mainline/runtime defaults
- use `identifier_fastpath + title_core` as the recommended synchronous live default profile
- keep `biomedical_fallback` and `slow_fallback` outside the synchronous default path until separately budgeted
- tune `title_core` budget shape and prioritize request-reduction inside that lane, especially `crossref` title cost, while keeping judgment on fixed-seed replay

## Immediate next-step direction

The most promising next phase is no longer broad policy exploration. It is **runtime hardening of the promoted synchronous lane default**.

Recommended order:
1. keep `identifier_fastpath` as the guaranteed live base lane
2. keep `identifier_fastpath + title_core` as the promoted synchronous default profile
3. optimize the `title_core` lane, with special focus on `crossref` title cost
4. tune explicit lane budgets / stop conditions as degraded-safe modes before attempting provider concurrency
5. keep every new scheduling optimization behind fixed-seed replay and, when needed, recorded-payload replay
6. avoid changing match standards unless a new correctness problem appears

## What should not be reopened casually

Do not reopen these as default-policy questions unless new evidence appears:
- broad `low_source_title_similarity` blocking
- broad `sparse_metadata_low_source_title_similarity` blocking
- candidate-level Unpaywall as a production enrich provider
- Track A matching-time author-blob filtering
