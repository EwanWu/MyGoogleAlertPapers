# Phase 2B default-retention memo: deterministic URL-identity DOI recovery (2026-05-03)

## Short answer
**Yes — keep it in the current default runtime.**

This is not a broad fetch-based DOI scraping feature.
It is a **narrow deterministic pre-title identity recovery lane**.

Current implemented rules are still intentionally small:
- `recursive_url_decode`
- `nature_article_slug`

The decision is therefore:
> should the current mainline default runtime keep deterministic URL-identity DOI recovery enabled before title fanout for non-arXiv `url_canonical_only` cases?

My answer is **yes**.

---

## What is being retained
When a candidate has:
- no extracted DOI
- no arXiv ID
- a `url_canonical`

then before title-path provider fanout, the runtime may try:
- deterministic DOI recovery from recursively decoded URL content
- deterministic DOI recovery from known publisher-local URL shape (`nature.com/articles/<slug>`)

If recovery succeeds, the candidate is upgraded from title-path routing into DOI-path routing.

This is intentionally narrower than:
- generic landing-page fetch and scrape
- broad publisher heuristics
- fuzzy URL inference
- generic residual top5 / acceptance relaxation

---

## Where the default actually binds
Primary code path:
- `src/mygooglealertpapers/normalize/identifiers.py`
- `src/mygooglealertpapers/pipeline/enrich.py`

Runtime binding:
- builtin default in `src/mygooglealertpapers/config.py`
- canonical combined profile:
  `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`

So “固化” here means:
- keep the narrow DOI-recovery lane enabled in the mainline default runtime
- do not widen it into fetch-based scraping
- do not reopen generic URL heuristics without new replay evidence

---

## Evidence base

### 1. The patch already passed medium60 on day13
Artifact:
- `docs/validation/day13-url-identity-doi-recovery-experiment-20260502.md`

Headline result on medium60:
- `planned_provider_intents 248 -> 242`
- `dispatch_request_count 75 -> 73`
- `title_lane_request_count 56 -> 51`
- `matched_source_record_count 83 -> 87`
- `canonical_paper_count 48 -> 49`
- `merge_review_queue_count 2 -> 2`

Interpretation:
- runtime got cheaper
- one real canonical gain appeared
- review burden did not increase

### 2. The patch also passed large-fixed before the repo-shadow integration
Artifact:
- `docs/validation/day13-large-fixed-url-identity-doi-validation-20260502.md`

Headline result on large-fixed:
- `matched_source_record_count 537 -> 543`
- `merged_metadata_proposal_count 357 -> 358`
- `canonical_paper_count 282 -> 283`
- `merge_review_queue_count 2 -> 2`
- `dispatch_request_count 413 -> 407`
- `title_lane_request_count 266 -> 253`
- `total_batch_duration_ms 707047 -> 665839`

Interpretation:
- this was already a clean positive on the real larger gate
- the gain profile was exactly what we want from a micro-lane: fewer title-path requests plus a small semantic win

### 3. The patch still helps after repo-shadow topk retry became part of the current default code path
New combined medium60 validation run:
- base: `docs/validation/day14-openalex-repo-shadow-medium60-20260502.json`
- treatment: `docs/validation/day15-current-default-plus-urlid-medium60-20260503.json`

Combined result relative to the current repo-shadow default:
- `planned_provider_intents 248 -> 242`
- `dispatch_request_count 73 -> 71`
- `title_lane_group_count 72 -> 66`
- `title_lane_request_count 54 -> 49`
- `matched_source_record_count 84 -> 88`
- `merged_metadata_proposal_count 57 -> 58`
- `canonical_paper_count 48 -> 49`
- `merge_review_queue_count 2 -> 2`
- `severe_doi_conflict_count 2 -> 2`
- `total_batch_duration_ms 142957 -> 112468`
- `total_provider_latency_ms 139941 -> 109335`

Interpretation:
- the gain survives coexistence with the later repo-shadow repair
- this is important because it means URL-identity DOI recovery was not made obsolete by the later OpenAlex routing fix

### 4. The refreshed current-default residual tail still supports this direction
Artifact:
- `docs/validation/day15-current-default-review-band-decomposition-and-next-target-20260503.md`

Relevant observation:
- current residuals remain heavily URL-anchored publisher pages
- the surviving review band is now too small to justify a first-pass collapse rule

Interpretation:
- pre-title identity recovery is still a more meaningful lever than immediate review-threshold tuning

---

## What this decision does **not** mean

### It does not justify broad HTML fetch / scraping
The retained claim is about **deterministic URL identity recovery**.
Not about fetching arbitrary landing pages and scraping DOI metadata at scale.

### It does not justify generic publisher-local rule explosion
The current rules are still very small.
Future additions should require the same bar:
- deterministic
- easy to audit
- replay-gated
- narrow blast radius

### It does not replace the repository-shadow retry
These are different repairs:
- URL-identity DOI recovery is a **pre-title identity upgrade**
- repository-shadow topk retry is an **OpenAlex-local routing rescue after a bad top1**

They are complementary, not substitutes.

---

## Operational consequence
### Recommended default posture
- enable `url_identity_doi_recovery_enabled: true` in the current builtin default runtime
- bind the same in the canonical combined default profile
- keep the current rule surface intentionally narrow

### Why this is the correct “固化” action
Because the patch is:
1. deterministic
2. already validated on medium60
3. already validated on large-fixed
4. still positive after coexistence with repo-shadow default behavior
5. non-regressive on review/conflict burden
6. a route-cleanup + small semantic gain layer, not a risky policy widening

---

## Final posture
### Known
- deterministic URL-identity DOI recovery improves routing on medium60
- it also passed large-fixed before repo-shadow retention
- it remains positive when re-checked against the repo-shadow current default on medium60
- review/conflict burden did not increase

### Inferred
- this patch should remain enabled in the current default runtime
- the right framing is pre-title identity hardening, not scraping or broad residual widening

### Speculative
- further domain-specific expansion may still be worthwhile, but only if new rules are equally deterministic and replay-clean
- do not assume the next expansion should be `sciencedirect` or `mdpi` until URL-shape determinism is demonstrated

---

## Bottom line
The correct project-level conclusion is now:

> **Deterministic URL-identity DOI recovery should be retained in the current builtin default runtime.**
> It is a narrow identity-upgrade layer that reduces title-path work, survives coexistence with the repo-shadow OpenAlex repair, and provides a small but real semantic gain without increasing review burden.
