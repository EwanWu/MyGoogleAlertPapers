# Phase 2A promotion memo: post-openalex conditional suppression for `crossref:url_canonical_only` (2026-04-30)

## Decision

**Promote** the following narrow runtime rule into the default synchronous runtime path:

- for title-lane subgroup `crossref:url_canonical_only`
- do **not** blanket pre-skip the subgroup
- instead, run `openalex` first and suppress the corresponding `crossref` title request **only after** `openalex` has already produced a DOI-bearing title recovery for that subgroup

This rule is currently implemented by the profile:

- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml`

Rollout status on 2026-04-30:
- builtin default runtime profile updated
- baseline helper default profile updated

## Why this memo exists

Phase 2A was explicitly constrained by an anti-overfitting rule:

- every stricter runtime rule must be tested as a **one-factor ablation**
- request savings are not enough
- promotion requires **no semantic regression** on both:
  1. fixed slice150
  2. at least one fresh-like / recent slice

This memo records that the first strict rule failed, the narrower follow-up rule passed, and the project now has decision-grade evidence for promotion.

## Rejected alternative: blanket skip `crossref:url_canonical_only`

The first strict rule tested was a blanket pre-dispatch skip of `crossref:url_canonical_only`.

Result on fixed slice150:
- clear runtime win
- but **clear semantic regression**
- specifically, **30 crossref-only DOI rescue cases** were lost
- `normalized_only` fallback proposals inflated **38 -> 68**

Therefore the blanket skip rule is **rejected** and should not be reopened as a default candidate without new evidence.

Canonical rejection note:
- `docs/validation/day8-crossref-url-only-ablation-fixed150-20260430.md`

## Promoted candidate under evaluation: post-openalex conditional suppression

The narrower follow-up rule changes only the suppression timing:
- keep `crossref:url_canonical_only` available by default
- allow `openalex` to run first for the targeted subgroup
- suppress `crossref` only when `openalex` has already recovered a DOI-bearing title match

Mechanistically, this targets the subgroup that looked safely redundant in the decomposition while preserving the `crossref-only` DOI rescue cases that broke the blanket skip rule.

## Evidence summary

### 1. Fixed slice150

Validation note:
- `docs/validation/day8-crossref-url-only-post-openalex-ablation-fixed150-20260430.md`

Key results vs control:
- post-openalex suppressed **76 groups / 77 intents**
- dispatch requests **487 -> 411**
- title-lane requests **340 -> 264**
- crossref events **368 -> 291**
- crossref latency **610,951 -> 391,016 ms**
- total provider latency **928,175 -> 743,555 ms**
- canonical papers **292 -> 293**
- merge review queue **1 -> 0**
- severe DOI conflicts **1 -> 0**
- normalized-only fallback **38 -> 38**
- candidate-level diff: **0 DOI loss / 0 confidence collapse / 1 review resolved**

Interpretation:
- the rule preserved semantics on the fixed slice
- it retained the only meaningful precision gain case
- it removed a large fraction of the redundant crossref title work

### 2. Fresh-like cached slice

Validation note:
- `docs/validation/day8-post-openalex-fresh30-ablation-20260430.md`

Source slice:
- `data/mgap_fresh30_20260410.db`

Key results vs control:
- post-openalex suppressed **15 groups / 15 intents**
- dispatch requests **127 -> 112**
- title-lane requests **88 -> 73**
- crossref events **95 -> 80**
- crossref latency **144,595 -> 107,781 ms**
- total provider latency **233,096 -> 195,002 ms**
- canonical papers **75 -> 75**
- merge review queue **0 -> 0**
- severe DOI conflicts **0 -> 0**
- normalized-only fallback **20 -> 20**
- candidate-level diff: **0 DOI loss / 0 confidence collapse / 0 canonical changes / 0 new review**

Interpretation:
- the same mechanism generalizes beyond the fixed slice
- the fresh-like slice reproduces the key safety property: `crossref` support disappears only when `openalex` is already sufficient

## Promotion-gate verdict

Against the explicit Phase 2A gate, the rule now passes:

1. **runtime win on fixed + fresh-like slices** — yes
2. **`canonical_paper_count` does not drop** — yes
3. **`merge_review_queue_count` does not rise** — yes
4. **`severe_doi_conflict_count` does not rise** — yes
5. **changed outcomes are explainable as safe suppression rather than recall loss** — yes

## Caveat

The second gate used the repo's **best currently documented fresh-like cached slice** (`2026-04-10`), not a later truly recent ingest slice.

This is a real caveat, but under the current project rules it is **not** a blocker:
- the slice is explicitly fresh-like and was already part of the repo's baseline-comparison vocabulary
- there is currently no better recent cached slice documented in the repo

So the correct interpretation is:
- promotion is justified now
- a later newer ingest slice would be useful as **extra confirmation**, not as a prerequisite to avoid calling the current evidence sufficient

## Recommended rollout scope

Promote only the narrow rule that has actually been validated:

- provider: `crossref`
- title subgroup: `url_canonical_only`
- condition: only after successful DOI-bearing `openalex` title recovery

Do **not** expand promotion to:
- broader `crossref` title suppression
- other title subreasons
- pre-dispatch blanket skipping
- provider-order changes outside this validated subgroup without separate replay evidence

## Recommended immediate follow-up after promotion

1. keep the new observability fields in runtime/reporting output
2. monitor:
   - `post_openalex_suppressed_*`
   - `normalized_only_fallback_proposal_count`
   - review/conflict burden
3. if a newer recent ingest slice becomes available, run one confirmatory replay pair
4. do not reopen the rejected blanket-skip rule unless a materially different mechanism is proposed

## Artifacts

- Phase plan / decision log:
  - `docs/18-next-phase-runtime-hardening-plan-2026-04-29.md`
- Blanket-skip rejection:
  - `docs/validation/day8-crossref-url-only-ablation-fixed150-20260430.md`
- Fixed-slice success note:
  - `docs/validation/day8-crossref-url-only-post-openalex-ablation-fixed150-20260430.md`
- Fresh-like success note:
  - `docs/validation/day8-post-openalex-fresh30-ablation-20260430.md`
- Fixed-slice JSON report:
  - `docs/validation/day8-post-openalex-skip-crossref-url-only-fixed150-20260430.json`
- Fresh-like control/treatment JSON reports:
  - `docs/validation/day8-post-openalex-fresh30-control-20260430.json`
  - `docs/validation/day8-post-openalex-fresh30-treatment-20260430.json`
