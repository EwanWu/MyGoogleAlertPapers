# Phase 2B promotion memo: targeted non-arXiv `reject71 + review08` is now promoted into the builtin default (2026-05-02)

## Decision
Promote:

- `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08`

from **leading validated candidate** to **builtin default behavior for the remaining non-arXiv residual `url_canonical_only` cleanup route**.

## Scope
Inside the narrow subgroup:
- normalized-only fallback
- `openalex_title_unmatched`
- `url_canonical_only`
- missing `arxiv_id_extracted`

apply:
- `<= 0.71` → reject
- `(0.71, 0.80]` → review

This promotion is additive to the already-promoted arXiv-gated residual `top5 + best-accepted` exception.

## Why promotion is now justified
### 1. Semantic direction is strong
The day11 truth audit showed that the touched cases were overwhelmingly desirable false-positive removals rather than obvious true matches that were being harmed.

Primary evidence:
- `docs/validation/day11-targeted-nonarxiv-review08-llm-truth-audit-20260501.md`

### 2. Large-scale effect is concentrated
Across `956` candidates / `4` slices, the deterministic treatment changed only a tiny concentrated set while reducing noisy normalized-only fallback acceptance:
- canonical papers: `783 -> 757`
- review queue: `7 -> 8`
- normalized-only fallback proposals: `141 -> 116`
- changed set: only `10` unique candidates
- `9 / 10` changed candidates were already inside the audited bad-match set
- the only new unique case was routed to review rather than reject

Primary evidence:
- `docs/validation/day11-targeted-nonarxiv-reject71-review08-large-scale-validation-20260501.md`

### 3. Reproducibility is now closed
The day12 runner reproduced the prior day11 stable replay exactly across all four slices:
- canonical papers: `757 -> 757`
- review queue: `8 -> 8`
- merged proposals: `928 -> 928`
- matched source records: `1322 -> 1322`
- normalized-only fallback proposals: `116 -> 116`

Primary evidence:
- `docs/validation/day12-targeted-nonarxiv-reject71-review08-repro-validation-20260502.md`

### 4. Conflict burden did not worsen
`severe_doi_conflict_count` stayed unchanged against the control across all four slices.

## Interpretation
This is **not** a neutral runtime-only upgrade.
It is a deliberate **precision-first default-policy promotion**.

What is being accepted by this promotion is:
- a small reduction in automatic canonical acceptance,
- a very small increase in review burden,
- in exchange for avoiding a subgroup of false-positive canonicalizations that is now strongly evidenced and reproducible.

That trade is now justified enough to be the default.

## Runtime / config consequence
The promoted default should now combine both retained Phase 2B pieces:
1. narrow arXiv-gated residual `top5 + best-accepted`
2. narrow non-arXiv `reject71 + review08`

Canonical combined profile artifact:
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`

## Bottom line
The correct project-level conclusion is now:

> the remaining non-arXiv residual cleanup route has crossed the final policy bar and should be promoted into the builtin default, explicitly as a precision-first default decision rather than as a cost-free runtime tweak.
