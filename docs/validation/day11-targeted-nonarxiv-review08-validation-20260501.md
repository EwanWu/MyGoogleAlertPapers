# Day11 validation: subgroup-aware non-arXiv residual fallback review (0.80)

## Objective
Implement and validate a **subgroup-aware** merge-only guardrail for the retained arXiv-gated profile.

Target subgroup:
- post-openalex residual
- `title_lane_subreason = url_canonical_only`
- non-arXiv / missing `arxiv_id_extracted`
- normalized-only fallback path only

Rule tested:
- `fallback_review_similarity_threshold_post_openalex_url_only_non_arxiv: 0.8`

Profile:
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_review08.yaml`

## Implementation
Code patch landed in `src/mygooglealertpapers/pipeline/merge.py`:
- recompute same-batch cluster context during merge
- infer a minimal fallback context for normalized-only cases
- expose whether a candidate belongs to the targeted subgroup
- apply the new threshold only inside that subgroup

Added tests in `tests/test_policy_and_merge_fallback.py`:
- targeted non-arXiv residual case is routed to review
- arXiv-native case is not routed by this rule
- clustered url-only leader case is not routed by this rule

Validation gates run:
- `PYTHONPATH=src python3 -m pytest tests/test_policy_and_merge_fallback.py -q`
- `PYTHONPATH=src python3 -m pytest tests/test_post_openalex_residual_audit.py tests/test_fallback_author_blob_identifier_aware.py -q`

## Stable replay design
To avoid provider/runtime noise, validation reused the completed retained-arXiv-gate replay DBs and re-ran **merge + dedup only**.

### large_fixed
Baseline retained arXiv gate:
- canonical: `293`
- review: `0`

Targeted non-arXiv review08:
- canonical: `281`
- review: `12`

Delta:
- canonical: `-12`
- review: `+12`

### fresh30
Baseline retained arXiv gate:
- canonical: `75`
- review: `0`

Targeted non-arXiv review08:
- canonical: `71`
- review: `4`

Delta:
- canonical: `-4`
- review: `+4`

## What changed
Candidate-level delta is clean:
- large_fixed changed cases: `12`
- fresh30 changed cases: `4`
- **all changed rows were `source_title_noise_or_crossref_cleanup`**
- **zero** `likely_openalex_recall_gap` rows were touched
- **zero** `mixed_or_unclear` rows were touched
- clustered duplicate / leader-path spillover seen in the earlier broad probe was excluded
- arXiv-native spillover seen in the earlier broad probe was excluded

So the subgroup-aware patch did what the profile-only probe could not do:

> it isolated the noisy non-arXiv residual fallback subgroup without leaking into the high-confidence recall-gap subgroup.

## Interpretation
This is a successful **targeting** result, not yet an automatic promotion result.

Known:
- the new code path is specific enough to avoid the broad collateral damage from the earlier `fallback_review09` probe
- the affected set is exactly the noisy `source_title_noise_or_crossref_cleanup` subgroup in both slices

Inferred:
- the rule is now operating on the intended residual mechanism rather than globally penalizing normalized-only fallback

Still unresolved:
- promotion policy: the rule still reduces canonical count and increases review burden, even though it appears to do so only for noisy rows
- therefore this is not yet a safe default-promote result under the existing no-semantic-regression gate

## Current recommendation
Do **not** promote this as a default rule yet.

Instead, keep it as a validated experimental hook and choose one of two next moves:
1. **Manual truth audit** of the 16 affected cases to determine whether these canonical losses are actually desirable false-positive removals
2. add a still narrower acceptance path (for example language/author-blob specific guardrails) if the goal is default-safe automation rather than review routing

## Artifacts
- Code:
  - `src/mygooglealertpapers/pipeline/merge.py`
- Tests:
  - `tests/test_policy_and_merge_fallback.py`
- Profile:
  - `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_review08.yaml`
- Reports:
  - `docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-targeted-nonarxiv-review08-20260501.json`
  - `docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-targeted-nonarxiv-review08-20260501.json`
- Audit CSVs:
  - `docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-targeted-nonarxiv-review08-audit-20260501.csv`
  - `docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-targeted-nonarxiv-review08-audit-20260501.csv`
