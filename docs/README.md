# Documentation map

This repo's docs are now split into a small **active layer** and a larger **archive layer**.

## 1. Active layer

Read these first when you want the current project state, current default flow, and current decision basis.

### Project-wide entry order

1. `docs/13-project-phase-map-and-current-status-2026-04-22.md`
2. `docs/14-mainline-promotion-memo-2026-04-22.md`
3. `docs/11-packageB-decision-memo-2026-04-16.md`
4. `docs/12-packageB-phase-summary-and-archive-guide-2026-04-16.md`
5. `docs/09-packageA-implementation-and-replay-results-2026-04-15.md`
6. `docs/validation/recorded_deterministic_ab_medium60_20260427.md`
7. `docs/validation/trackA-author-blob-fb-decision-20260421c.md`
8. `docs/validation/trackB-unpaywall-decision-memo-20260422.md` — ✅ **COMPLETED 2026-04-22**
9. `docs/validation/mainline-summary-20260422_mainline.md`
10. `docs/validation/day5-provider-lane-ablation-120-20260429.md`
11. `docs/validation/day5-identifier-plus-title-core-live150-20260429.md`
12. `docs/16-duplicate-provider-query-elimination-plan-2026-04-29.md`
13. `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md`
14. `docs/validation/day6-same-batch-cluster-ablation-150-20260429.md`
15. `docs/18-next-phase-runtime-hardening-plan-2026-04-29.md`
16. `docs/19-phase2A-post-openalex-conditional-suppression-promotion-memo-2026-04-30.md`
17. `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md`
18. `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`
19. `docs/24-phase2B-narrow-activation-arxiv-gate-promotion-memo-2026-05-01.md`
20. `docs/25-phase2B-targeted-nonarxiv-reject71-review08-promotion-posture-memo-2026-05-02.md`
21. `docs/26-phase2B-targeted-nonarxiv-reject71-review08-promotion-memo-2026-05-02.md`

### Current active decision layer

- `docs/13-project-phase-map-and-current-status-2026-04-22.md`
- `docs/14-mainline-promotion-memo-2026-04-22.md`
- `docs/11-packageB-decision-memo-2026-04-16.md`
- `docs/12-packageB-phase-summary-and-archive-guide-2026-04-16.md`
- `docs/validation/trackA-author-blob-fb-decision-20260421c.md`
- `docs/validation/trackB-unpaywall-decision-memo-20260422.md`
- `docs/validation/mainline-summary-20260422_mainline.md`
- `docs/validation/day5-provider-lane-ablation-120-20260429.md`
- `docs/validation/day5-identifier-plus-title-core-live150-20260429.md`
- `docs/16-duplicate-provider-query-elimination-plan-2026-04-29.md`
- `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md`
- `docs/validation/day6-same-batch-cluster-ablation-150-20260429.md`
- `docs/18-next-phase-runtime-hardening-plan-2026-04-29.md`
- `docs/19-phase2A-post-openalex-conditional-suppression-promotion-memo-2026-04-30.md`
- `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md`
- `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`
- `docs/24-phase2B-narrow-activation-arxiv-gate-promotion-memo-2026-05-01.md`
- `docs/25-phase2B-targeted-nonarxiv-reject71-review08-promotion-posture-memo-2026-05-02.md`
- `docs/26-phase2B-targeted-nonarxiv-reject71-review08-promotion-memo-2026-05-02.md`

### Current runtime / provider-lane validation

- `docs/validation/day5-provider-lane-ablation-120-20260429.md` — current runtime-lane memo covering lane gating, the first budgeted title-core stop-condition replay, and the live150 follow-up decision
- `docs/validation/day5-identifier-plus-title-core-live150-20260429.md` — closest-to-production slice150 live replay for the promoted synchronous lane profile; confirms clean enrich→merge→dedup completion without reopening slow fallback lanes
- `docs/16-duplicate-provider-query-elimination-plan-2026-04-29.md` — analysis + staged blueprint for suppressing repeated provider queries via exact library prelink, same-batch candidate clustering, and stronger article-identity aliases above the current query-cache layer
- `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md` — implementation archive + live control/treatment evidence showing that exact library-first prelink is now a proven, fixed workstream rather than a speculative idea
- `docs/validation/day6-same-batch-cluster-ablation-150-20260429.md` — first same-batch exact clustering ablation on top of exact prelink; shows ~23.8% wall-time reduction and ~21.2% dispatch-request reduction on a synthetic duplicate stress slice, and now serves as the promotion basis for enabling exact same-batch clustering in the default runtime layer
- `docs/18-next-phase-runtime-hardening-plan-2026-04-29.md` — active Phase 2A runtime-hardening log, including the rejection of blanket `crossref:url_canonical_only` skipping and the two-gate validation path for narrower title-lane suppression rules
- `docs/19-phase2A-post-openalex-conditional-suppression-promotion-memo-2026-04-30.md` — current decision memo recommending promotion of the narrow post-openalex conditional suppression rule for `crossref:url_canonical_only`
- `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md` — large-scale final gate showing that broad `top1 -> top5 + best-accepted` is semantically safe but not efficient enough for default promotion
- `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md` — narrow-rule analysis showing that all observed broad-treatment gains are concentrated in an arXiv-native residual subgroup
- `docs/24-phase2B-narrow-activation-arxiv-gate-promotion-memo-2026-05-01.md` — formal promotion memo recommending only the narrow arXiv-gated `url_canonical_only -> top5 + best-accepted` exception
- `docs/25-phase2B-targeted-nonarxiv-reject71-review08-promotion-posture-memo-2026-05-02.md` — pre-promotion posture memo capturing the last decision gate before defaultization
- `docs/26-phase2B-targeted-nonarxiv-reject71-review08-promotion-memo-2026-05-02.md` — final promotion memo approving the non-arXiv `reject71 + review08` route as a precision-first builtin default addition
- code/runtime note: the builtin CLI default and baseline helper default are now aligned to the same-batch-clustered `identifier_fastpath + title_core` runtime **with promoted post-openalex conditional suppression for `crossref:url_canonical_only`, the promoted narrow arXiv-gated `url_canonical_only -> top5 + best-accepted` exception, and the promoted precision-first non-arXiv `reject71 + review08` cleanup route all enabled by default**

### Current operations / data-acquisition validation

- `docs/validation/163-local-scholar-index-validation-20260423.md` — validated Windows-local 163 unread Google Scholar index flow, including root-cause analysis of the `135`-row regression and the final `277`-row 3-page result
- `docs/validation/163-local-body-sweep-and-ingest-validation-20260424.md` — canonical 2026-04-24 validation memo for the 21-page / 1878-mail body sweep, with time-cost analysis, 20-mail mixed smoke test, full 1878-mail early-ingest verification, and the current diagnosis of deep-page UI navigation overhead
- `runbooks/163-local-mail-modular-pipeline-2026-04-23.md` — defines the new decoupled execution boundary: validate small-batch body ingestion into the existing SQLite pipeline first, then fetch all mail bodies, and only after that run offline enrich / merge / dedup
- `runbooks/163-local-body-ingest-smoketest-2026-04-23.md` — exact CLI, input schema, and smoke-test sequence for importing locally fetched bodies into SQLite before any enrich stage
- `scripts/windows_local/run_163_body_fetch_sample.ps1` + `scripts/windows_local/read_163_scholar_with_manual_pause.py run-body-fetch` — first-cut Windows-local body-fetch path that emits import-local-bodies-compatible JSONL for the 10-20 mail validation stage

## 2. Archive layer

Use archive docs only when you need provenance, debugging history, exact intermediate reasoning, or raw replay artifacts.

- phase archive: `docs/archive/`
- validation archive: `docs/validation/archive/`

### New archive groups created in this cleanup

- `docs/archive/legacy-plans-and-notes-20260409-22/`
- `docs/archive/mainline-transition-20260416-22/`
- `docs/validation/archive/day3-runtime-optimization-20260427/`
- `docs/validation/archive/trackA-20260421/`
- `docs/validation/archive/trackB-20260421-22/`
- `docs/validation/archive/mainline-20260422/`

## Documentation maintenance rule

Keep active docs small and decision-oriented.

Active docs should answer:
- what is the current default
- what is the current implementation state
- what evidence is canonical
- what a new agent or human should read first

Archive docs that are mainly:
- temporary plans
- handoff notes
- superseded branch memos
- smoke-run summaries
- raw control/treatment replay dumps
- intermediate checkpoints already captured elsewhere
