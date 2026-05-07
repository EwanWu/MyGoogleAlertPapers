# Day11 probe: non-arXiv residual fallback_review_similarity_threshold=0.9

## Goal
Test whether a **merge-only**, one-factor guardrail can clean up the small non-arXiv `url_canonical_only` residual subgroup without touching the retained arXiv-gated runtime behavior.

Profile used:
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_fallback_review09.yaml`

Design:
- Keep the retained arXiv-gated runtime rules unchanged
- Reuse the already-materialized source records from the completed retained-arXiv-gate replay DBs
- Re-run **merge + dedup only**
- Add exactly one merge rule:
  - `fallback_review_similarity_threshold: 0.9`

## Why 0.9 looked plausible before replay
Candidate-level residual audit from the retained arXiv-gated run showed:
- combined residual rows: `153`
- normalized-only residual rows: `27`
- among those 27 rows, threshold sweep on `crossref_title_similarity` suggested:
  - `<=0.80` hits `17/27` and all are `source_title_noise_or_crossref_cleanup`
  - `<=0.90` hits `24/27` and still hits **0** `likely_openalex_recall_gap`

This made `0.9` look like a promising narrow cleanup threshold **if** the affected population stayed inside the residual subgroup.

## Replay results

### large_fixed
Baseline retained arXiv gate:
- canonical_paper_count: `293`
- merge_review_queue_count: `0`

fallback_review09 probe:
- canonical_paper_count: `270`
- merge_review_queue_count: `27`

Delta:
- canonical: `-23`
- review: `+27`

### fresh30
Baseline retained arXiv gate:
- canonical_paper_count: `75`
- merge_review_queue_count: `0`

fallback_review09 probe:
- canonical_paper_count: `69`
- merge_review_queue_count: `7`

Delta:
- canonical: `-6`
- review: `+7`

## What the probe actually hit
All new review cases were triggered by:
- `fallback_guardrail:low_source_title_similarity`

Residual-audit overlap:
- large_fixed: only `19/27` review cases were inside the targeted post-openalex residual audit slice
- fresh30: only `5/7` review cases were inside the targeted residual audit slice

So this profile-level threshold **leaked outside** the intended residual subgroup.

### Off-target examples
The extra review cases included candidates not in the residual audit slice, for example:
- repeated JAMA Cardiology URL cases around `HeartSync-LBBP`
- repeated ScienceDirect URL cases around `BIO-CONDUCT`
- arXiv URL cases such as `DINOv3 with Test-Time Calibration...`

These were all normalized-only fallback cases with no extracted DOI/PMID/PMCID, but they were **not** the specific `post-openalex residual url_canonical_only` subgroup we intended to target.

## Interpretation
This is the key result:

> A plain merge-level `fallback_review_similarity_threshold=0.9` is **too broad**.

It does recover the intuition that many noisy normalized-only residuals are low-similarity garbage-like cases, but it cannot safely isolate them at profile level because the merge guardrail has no notion of:
- whether the candidate came from the `post-openalex residual` path
- whether the subgroup was specifically `url_canonical_only`
- whether the case is non-arXiv versus arXiv/duplicate spillover

## Decision
**Do not promote or continue with the profile-only `fallback_review09` approach.**

It is useful only as a diagnostic probe.

## Recommended next step
Move from a profile-only guardrail to a **code-targeted micro-patch** that carries subgroup awareness into merge/fallback handling.

Minimum requirements for the next patch:
1. Trigger only on the intended subgroup, not all normalized-only fallback cases
2. Preserve the retained arXiv-gated runtime behavior
3. Avoid touching the high-confidence Crossref DOI rescue subgroup
4. Gate on explicit subgroup metadata such as:
   - post-openalex residual status
   - `title_lane_subreason = url_canonical_only`
   - non-arXiv / missing arXiv id

## Artifacts
- Profile:
  - `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_fallback_review09.yaml`
- Replay outputs:
  - `docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-fallback-review09-20260501.json`
  - `docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-fallback-review09-20260501.json`
- Audit CSVs:
  - `docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-fallback-review09-audit-20260501.csv`
  - `docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-fallback-review09-audit-20260501.csv`
