# Phase 2B default retention memo: narrow truncated-title salvage should remain in the current default code path (2026-05-02)

## Decision
Keep the narrow **truncated-title salvage** rule in the current default mainline runtime.

This is a **retain-in-default** decision, not a new profile promotion.

The rule lives in the shared acceptance layer:
- `src/mygooglealertpapers/enrich/base.py`
- function: `accept_result(...)`

So the operational question is not:
- “should we switch the builtin default to a new YAML profile?”

It is:
- “should the current default mainline continue to keep this narrow acceptance rule enabled?”

Answer:
- **yes**

---

## Scope of the rule
The salvage branch only activates when all of the following hold:
- normal title acceptance did not already pass
- `title_similarity >= 0.84`
- the source title looks truncated (`. .`, `…`, or trailing `...`)
- `first_author_matches(...) is True`
- `venue_hint_matches(...) is True`
- no year conflict

This is deliberately narrower than a generic similarity-threshold relaxation.

---

## Current default context
Current promoted mainline default remains the combined Phase 2B profile:
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`

Bound at:
- builtin runtime default in `src/mygooglealertpapers/config.py`
- baseline helper default in `src/mygooglealertpapers/benchmark_baseline.py`

Important runtime context:
- default enabled lanes remain:
  - `identifier_fastpath`
  - `title_core`
- broader fallback lanes are still not part of the default path

So retaining this patch in the current default means:
- preserving a narrow title-core acceptance repair
- not reopening broad fallback behavior

---

## Evidence for retention
### 1. Targeted test coverage exists
`tests/test_title_normalization.py` now covers:
- truncation detection
- positive salvage case
- negative case when author / venue support is missing

Result:
```bash
pytest -q tests/test_title_normalization.py
```
passed.

### 2. Medium60 showed the intended narrow effect
Relative to the retained URL-identity DOI recovery baseline:
- `matched_source_record_count 87 -> 88`
- `dispatch_request_count 73 -> 72`

Representative rescued case:
- `cand_89794a7e8282a9b7`

Interpretation:
- the rule does not appear broad or noisy on the representative live slice
- it behaves like a true residual-tail salvage

### 3. Large-fixed confirmed that the effect was not a one-off
Primary artifact:
- `docs/validation/day13-large-fixed-truncated-title-salvage-rerun-validation-20260502.md`

Durable large-fixed deltas vs `day13_large_fixed_url_identity_doi_20260502`:
- `matched_source_record_count 543 -> 547` `(+4)`
- `dispatch_request_count 407 -> 403` `(-4)`
- `title_lane_request_count 253 -> 249` `(-4)`
- `merge_review_queue_count 2 -> 2`
- `severe_doi_conflict_count 2 -> 2`

Four stable rescued cases:
- `cand_20f8d5e121253c15`
- `cand_89794a7e8282a9b7`
- `cand_ba178f768ff6ab00`
- `cand_ebc2f5c1d2ce68ca`

These are the main retention argument.

---

## What this decision should and should not claim
### What it **should** claim
This patch is justified as a:
- **precision-preserving residual-tail acceptance repair**
- **semantic / routing improvement**

### What it should **not** claim
It should **not** be described as a stable runtime-speed improvement.

The completed live rerun showed:
- `total_batch_duration_ms 665839 -> 724093`
- `total_provider_latency_ms 654373 -> 712795`

even though request counts improved.

Interpretation:
- network/provider drift dominated observed latency on the rerun
- runtime gain is therefore not the correct promotion rationale

---

## Important caution
One extra `canonical +1` signal from the rerun should not be treated as core evidence for this patch.

Reason:
- `cand_8994637b2b637b39` appears to reflect live provider drift rather than the truncation-salvage mechanism itself

Therefore, the durable retention evidence should stay focused on:
- `matched_source_record +4`
- `dispatch_request_count -4`
- `title_lane_request_count -4`
- no review/conflict regression

---

## Policy interpretation
This retention is justified because the rule satisfies all of the following:
1. **mechanistically narrow**
2. **validated on both medium60 and large-fixed**
3. **no observed review/conflict regression**
4. **improves the exact residual title-core path the project is currently hardening**

This is materially different from:
- broadening non-arXiv top5 expansion
- lowering generic similarity thresholds
- relaxing venue checks globally
- reopening broad fallback acceptance

Those broader moves were either rejected already or remain unsupported.

---

## Bottom line
The correct Phase 2B project-level wording is:

> after promotion of URL-identity DOI recovery and the current combined Phase 2B default profile, the narrow truncated-title salvage rule should be retained in the shared default acceptance layer. It produces a small but durable set of semantically correct OpenAlex rescues, reduces residual Crossref title workload, and does not increase review or DOI-conflict burden. The rule should be justified as a precision-preserving acceptance repair, not as a proven live runtime-speed optimization.
