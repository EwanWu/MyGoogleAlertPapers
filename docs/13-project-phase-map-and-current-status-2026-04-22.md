# Project phase map and current status (updated 2026-04-29, same-batch clustering follow-up)

## Purpose

This is the current top-level entry for the project after Track A, Track B, and the integrated mainline validation.

Read this first if you need the shortest path to:
1. current default strategy
2. what has been decided and frozen
3. what remains open
4. what evidence is canonical

## One-line status

The project is now in:

> **default-flow operational hardening / request-scheduling optimization promotion with exact library-first prelink now active**

The pipeline is no longer mainly exploring strategy space. The current work is about locking one coherent default path, hardening the operator/runtime boundary around it, and only promoting narrow request-efficiency optimizations after deterministic replay evidence. As of 2026-04-29, this now includes an active exact library-first prelink layer above provider dispatch rather than treating duplicate-query elimination as a future-only idea.

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
- exact library-first prelink before provider fanout
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
- `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md`
- `docs/validation/day6-same-batch-cluster-ablation-150-20260429.md`

What these established:
- Day 2 operator-boundary hardening is in place and regression-tested
- Day 3 dispatch/cache/runtime changes did not break the validated merge/dedup path
- narrow-scope title payload reuse was promoted only after deterministic recorded-payload replay showed zero candidate-level semantic drift on the medium60 comparison
- explicit runtime lane gating is now viable: `identifier_fastpath` is a stable live core, and `identifier_fastpath + title_core` has now completed a closer-to-production slice150 live replay cleanly enough to justify promotion as the recommended synchronous default profile
- that promotion is no longer only documentary: the builtin CLI default and baseline helper default have been rebound to the `identifier_fastpath + title_core` profile, so default runs now execute the staged live path rather than the older full-provider synchronous fanout
- explicit per-lane stop conditions are now also viable: a budget-capped `title_core` run stops cleanly, records its stop reason in dispatch stats, and yields a controllable coverage/runtime tradeoff instead of a timeout boundary
- exact duplicate-query elimination has now crossed from blueprint to implementation for Phase 1: the runtime performs exact library-first prelink before provider dispatch, and live control/treatment evidence shows the operator-visible cost delta is large enough to justify making this the fixed next-stage workstream
- the next layer is now also validated: exact same-batch candidate clustering on top of prelink reduced dispatch groups `264 -> 216`, dispatch requests `226 -> 178`, and total batch wall time `586361 -> 447053 ms` on the day6 synthetic duplicate stress slice without adding review burden

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
13. `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md`

## What is still open

The main unresolved problem is no longer whether staged live lanes are viable, nor whether exact library-first prelink is worth implementing, nor whether exact same-batch clustering can matter in practice. All three are now established. The current unresolved problem is **how to combine exact prelink, same-batch clustering, and lane-level runtime control so the promoted `identifier_fastpath + title_core` default stays fast under wider live bursts, mainly by shrinking residual `crossref` title-lane cost**.

The next useful validation is:
- preserve the current promoted mainline/runtime defaults
- keep exact `library_prelink` enabled as the new first-layer short-circuit
- use `identifier_fastpath + title_core` as the recommended synchronous live default profile for unresolved candidates
- keep `biomedical_fallback` and `slow_fallback` outside the synchronous default path until separately budgeted
- implement same-batch candidate clustering as the next duplicate-suppression layer after exact prelink
- continue tuning `title_core` budget shape and residual `crossref` title cost while keeping judgment on fixed-seed replay

## Immediate next-step direction

The most promising next phase is no longer broad policy exploration. It is **runtime hardening of the promoted synchronous lane default plus article-level duplicate suppression above provider fanout**.

Recommended order:
1. keep exact `library_prelink` as the first short-circuit layer
2. keep exact same-batch candidate clustering as the second short-circuit layer
3. keep `identifier_fastpath` as the guaranteed live base lane for unresolved candidates
4. keep `identifier_fastpath + title_core` as the promoted synchronous default profile
5. optimize the residual `title_core` lane, with special focus on `crossref` title cost
6. tune explicit lane budgets / stop conditions as degraded-safe modes before attempting provider concurrency
7. keep every new scheduling optimization behind fixed-seed replay and, when needed, recorded-payload replay
8. avoid changing match standards unless a new correctness problem appears

## What should not be reopened casually

Do not reopen these as default-policy questions unless new evidence appears:
- broad `low_source_title_similarity` blocking
- broad `sparse_metadata_low_source_title_similarity` blocking
- candidate-level Unpaywall as a production enrich provider
- Track A matching-time author-blob filtering
