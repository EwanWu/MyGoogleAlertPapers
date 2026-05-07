# Decision memo: targeted non-arXiv reject71 + review08

## Decision
Advance `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08` as the current best candidate for the non-arXiv post-openalex residual cleanup route.

## Profile
`config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml`

## What it does
Inside the narrow subgroup:
- normalized-only fallback
- `openalex_title_unmatched`
- `url_canonical_only`
- missing `arxiv_id_extracted`

it applies:
- `<= 0.71` → reject
- `(0.71, 0.80]` → review

## Why this is the right current candidate
### 1. The semantic direction is now well supported
From `docs/validation/day11-targeted-nonarxiv-review08-llm-truth-audit-20260501.md`:
- the previously touched unique cases were overwhelmingly false-positive canonicalizations;
- they were mostly thesis/article/book-chapter / cross-language / related-but-not-same-document mismatches.

### 2. The deterministic version scales cleanly
From `docs/validation/day11-targeted-nonarxiv-reject71-review08-large-scale-validation-20260501.md` across `956` candidates / `4` slices:
- canonical papers: `783 -> 757` (`-26`)
- review queue: `7 -> 8` (`+1`)
- normalized-only fallback proposals: `141 -> 116` (`-25`)

### 3. The changed set stays concentrated
Only `10` unique candidates changed across the four slices.
- `9` of those are already inside the day11 audited bad-match set
- the only new unique case, `cand_f241c280253095ad`, is **reviewed rather than rejected**

This is exactly the pattern we wanted.

## What this does *not* yet prove
It does not prove that every remaining `(0.71, 0.80]` case should also be rejected.
That tail is now small enough to audit separately.

## Recommended next action
Use this profile as the working promotion candidate for the route, and if we want one more tightening pass, focus only on the surviving review band rather than reopening the full residual class.

## Bottom line
This route is now substantially more mature than `targeted_nonarxiv_review08` alone:
- it converts most of the audited false-positive subgroup into deterministic cleanup,
- preserves the borderline tail for review,
- and does so without broad spillover.
