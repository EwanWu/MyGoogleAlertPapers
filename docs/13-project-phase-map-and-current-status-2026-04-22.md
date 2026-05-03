# Project phase map and current status (updated 2026-05-02, Phase 2B narrow arXiv-gated default flip)

## Purpose

This is the current top-level entry for the project after Track A, Track B, and the integrated mainline validation.

Read this first if you need the shortest path to:
1. current default strategy
2. what has been decided and frozen
3. what remains open
4. what evidence is canonical

## One-line status

The project is now in:

> **default-flow operational hardening with exact library-first prelink + same-batch clustering active, Phase 2A crossref title suppression promoted, broad Phase 2B top5 rejected, both retained narrow Phase 2B profile-level patches — the arXiv-gated residual top5 exception and the precision-first non-arXiv `reject71 + review08` cleanup route — now bound into the default runtime, the retained deterministic URL-identity DOI recovery lane now bound into the shared default pre-title path, the follow-up narrow truncated-title salvage rule retained in the shared default acceptance layer, and the narrow OpenAlex repository-shadow topk retry retained in the shared default OpenAlex title path**

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
- exact same-batch clustering before residual title work
- safe dispatch dedup
- context-aware enrichment cache keys
- OpenAlex DOI batching
- title payload reuse enabled by default for `crossref` / `openalex` / `semanticscholar`
- post-openalex conditional suppression for `crossref:url_canonical_only`
- broad `top1 -> top5 + best-accepted` remains rejected as a default residual upgrade
- narrow `url_canonical_only + arxiv_id_extracted -> top5 + best-accepted` is now the retained Phase 2B promotion result and has now been flipped into the builtin runtime default as a narrow exception rather than a broad residual-path upgrade
- narrow non-arXiv `targeted_nonarxiv_reject71_review08` is now also promoted into the builtin default as a precision-first residual cleanup rule for the remaining non-arXiv `url_canonical_only` subgroup
- deterministic URL-identity DOI recovery is retained in the shared default pre-title identity path for `non-arXiv + url_canonical_only` candidates when DOI recovery succeeds through the current narrow deterministic rules (`recursive_url_decode`, `nature_article_slug`); this is a default runtime retention, not broad fetch-based DOI scraping
- narrow truncated-title salvage is retained in the shared default acceptance layer for title-core matches when truncation signal + author agreement + venue agreement jointly hold; this is a code-level default retention, not a separate YAML profile flip
- narrow OpenAlex repository-shadow topk retry is retained in the shared default OpenAlex title path: when a top1 result looks like a repository-shadow false lead (title/author aligned but venue-mismatched repository article), do one local `per_page=5` retry and re-pick only if a later result passes the existing accepted-result check; this is a code-level default retention, not a new profile fork

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
- `docs/18-next-phase-runtime-hardening-plan-2026-04-29.md`
- `docs/19-phase2A-post-openalex-conditional-suppression-promotion-memo-2026-04-30.md`
- `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md`
- `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`
- `docs/24-phase2B-narrow-activation-arxiv-gate-promotion-memo-2026-05-01.md`
- `docs/25-phase2B-targeted-nonarxiv-reject71-review08-promotion-posture-memo-2026-05-02.md`
- `docs/26-phase2B-targeted-nonarxiv-reject71-review08-promotion-memo-2026-05-02.md`
- `docs/27-phase2B-truncated-title-salvage-default-retention-memo-2026-05-02.md`
- `docs/29-phase2B-openalex-repository-shadow-topk-retry-default-retention-memo-2026-05-03.md`
- `docs/30-phase2B-url-identity-doi-recovery-default-retention-memo-2026-05-03.md`

What these established:
- Day 2 operator-boundary hardening is in place and regression-tested
- Day 3 dispatch/cache/runtime changes did not break the validated merge/dedup path
- narrow-scope title payload reuse was promoted only after deterministic recorded-payload replay showed zero candidate-level semantic drift on the medium60 comparison
- explicit runtime lane gating is now viable: `identifier_fastpath` is a stable live core, and `identifier_fastpath + title_core` has now completed a closer-to-production slice150 live replay cleanly enough to justify promotion as the recommended synchronous default profile
- that promotion is no longer only documentary: the builtin CLI default and baseline helper default have been rebound to the `identifier_fastpath + title_core` profile, so default runs now execute the staged live path rather than the older full-provider synchronous fanout
- explicit per-lane stop conditions are now also viable: a budget-capped `title_core` run stops cleanly, records its stop reason in dispatch stats, and yields a controllable coverage/runtime tradeoff instead of a timeout boundary
- exact duplicate-query elimination has now crossed from blueprint to implementation for Phase 1: the runtime performs exact library-first prelink before provider dispatch, and live control/treatment evidence shows the operator-visible cost delta is large enough to justify making this the fixed next-stage workstream
- the next layer is now also validated and promoted: exact same-batch candidate clustering on top of prelink reduced dispatch groups `264 -> 216`, dispatch requests `226 -> 178`, and total batch wall time `586361 -> 447053 ms` on the day6 synthetic duplicate stress slice without adding review burden
- this promotion is no longer only documentary: the builtin runtime default and the baseline helper default should now both bind to the same-batch-cluster-enabled synchronous profile rather than the earlier pre-clustering `identifier_plus_title_core` default
- the current Phase 2A strict-rule result is now also decision-grade and has now been bound into the promoted runtime default: blanket `crossref:url_canonical_only` skipping was rejected for semantic regression, while the narrower post-openalex conditional suppression rule passed both fixed-slice and fresh-like semantic gates and is now the retained narrow runtime hardening rule for that subgroup
- Phase 2B has now also closed the next residual question: broad `top1 -> top5 + best-accepted` failed the large-scale efficiency gate on 956 candidates, but retrospective exact subgroup validation showed that all 4 observed final-confidence gains were concentrated in a 26-candidate arXiv-native residual subgroup, so the retained Phase 2B result is a narrow promoted exception rather than a broad default flip
- the remaining non-arXiv residual cleanup route now also has a durable runner and passed exact reproducibility against the prior day11 stable replay; that route has now crossed the final policy bar and is promoted into the builtin default explicitly as a precision-first cleanup rule rather than a neutral runtime tweak
- deterministic URL-identity DOI recovery should now also remain in the current default pre-title identity path because it passed medium60, passed large-fixed, and remained positive when rechecked against the repo-shadow current default; this should be described as pre-title identity hardening rather than broad DOI scraping
- the follow-up truncated-title salvage question is now also closed: the rule should remain in the current default shared acceptance layer because it produces narrow durable title-core rescues without review/conflict regression, and should be described as a precision-preserving acceptance repair rather than a proven live speedup
- the next OpenAlex residual-routing question is now also closed: the narrow repository-shadow topk retry should remain in the current default OpenAlex title path because it passed the medium60 clean gate and beat the clean large-fixed control on both request shape and top-line output without increasing review/conflict burden; this should be described as a precision-preserving local routing repair rather than a broad top5 promotion

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
14. `docs/18-next-phase-runtime-hardening-plan-2026-04-29.md`
15. `docs/19-phase2A-post-openalex-conditional-suppression-promotion-memo-2026-04-30.md`
16. `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md`
17. `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`
18. `docs/24-phase2B-narrow-activation-arxiv-gate-promotion-memo-2026-05-01.md`
19. `docs/25-phase2B-targeted-nonarxiv-reject71-review08-promotion-posture-memo-2026-05-02.md`
20. `docs/26-phase2B-targeted-nonarxiv-reject71-review08-promotion-memo-2026-05-02.md`
21. `docs/27-phase2B-truncated-title-salvage-default-retention-memo-2026-05-02.md`
22. `docs/29-phase2B-openalex-repository-shadow-topk-retry-default-retention-memo-2026-05-03.md`
23. `docs/30-phase2B-url-identity-doi-recovery-default-retention-memo-2026-05-03.md`

## What is still open

The main unresolved problem is no longer whether staged live lanes are viable, nor whether exact library-first prelink is worth implementing, nor whether exact same-batch clustering can matter in practice. All three are now established and have now been promoted into the default runtime layer. The Phase 2B non-arXiv residual default-policy question is now also closed: the project has accepted the precision-first trade of `targeted_nonarxiv_reject71_review08` as a builtin default addition. The review-band follow-up has now also narrowed further after the day15 refresh: the surviving `(0.71, 0.80]` residual-policy tail is no longer a substantial coding target. The next unresolved problem is therefore: **whether a similarly narrow deterministic URL-origin identity expansion beyond the current retained rules is worth adding for the remaining publisher-page residuals, without reopening broad fetch/scrape behavior**.

The next useful validation / rollout step is:
- preserve the current promoted mainline/runtime defaults
- keep exact `library_prelink` enabled as the first-layer short-circuit
- keep exact same-batch clustering enabled as the second-layer short-circuit
- use `identifier_fastpath + title_core` as the synchronous live default base
- keep the retained deterministic URL-identity DOI recovery lane enabled in the default pre-title path
- keep the validated post-openalex conditional suppression rule for `crossref:url_canonical_only`
- retain the promoted Phase 2B arXiv-gated `top5 + best-accepted` exception as the only approved residual top5 expansion
- keep `biomedical_fallback` and `slow_fallback` outside the synchronous default path until separately budgeted
- continue tuning the remaining residual non-arXiv title cost only through the same replay-gated process

## Immediate next-step direction

The most promising next phase is no longer broad policy exploration. It is **runtime hardening of the promoted synchronous lane default plus article-level duplicate suppression above provider fanout**.

Recommended order:
1. keep exact `library_prelink` as the first short-circuit layer
2. keep exact same-batch candidate clustering as the second short-circuit layer
3. keep `identifier_fastpath` as the guaranteed live base lane for unresolved candidates
4. keep the same-batch-cluster-enabled `identifier_fastpath + title_core` profile as the promoted synchronous default profile
5. promote the validated post-openalex conditional suppression rule for `crossref:url_canonical_only`
6. then continue optimizing the residual `title_core` lane, with special focus on the still-unsuppressed `crossref` title cost
7. tune explicit lane budgets / stop conditions as degraded-safe modes before attempting provider concurrency
8. keep every new scheduling optimization behind fixed-seed replay and, when needed, recorded-payload replay
9. avoid changing match standards unless a new correctness problem appears

## What should not be reopened casually

Do not reopen these as default-policy questions unless new evidence appears:
- broad `low_source_title_similarity` blocking
- broad `sparse_metadata_low_source_title_similarity` blocking
- candidate-level Unpaywall as a production enrich provider
- Track A matching-time author-blob filtering
