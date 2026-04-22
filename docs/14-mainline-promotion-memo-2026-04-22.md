# Mainline promotion memo (2026-04-22)

## Decision

Promote the following integrated mainline candidate as the current project default:

> `conditional_sources_v2 + author_blob_fallback_only + post-dedup enrich-paper-oa`

## Why this is the right mainline

### Bibliographic core
`conditional_sources_v2` remains the best-supported default bibliographic policy. Larger-slice comparisons already showed that broader fallback-tightening variants reduce canonical yield and increase review burden.

### Narrow retained correctness patch
The retained Track A patch is:
- `conditional_sources_v2_author_blob_fallback_only`

This is acceptable because it fires only at the final weak fallback acceptance step. Under reused-source-record validation, the apparent `canonical -1` was shown to be **targeted garbage removal only**, not collateral loss.

### OA enhancement layer
The retained Track B result is:
- Unpaywall belongs after dedup, not inside the core bibliographic decision path

The OA stage is therefore an additive enhancement, not a provider replacement strategy.

## Promotion evidence

### Track A retained-patch evidence
- `docs/validation/trackA-author-blob-fb-decision-20260421c.md`
- integrated candidate-level check is summarized in `docs/validation/mainline-summary-20260422_mainline.md`

### Track B retained-role evidence
- `docs/validation/trackB-unpaywall-decision-memo-20260422.md`
- `docs/validation/unpaywall-position-batch50-summary-20260422_batch50-corrected.md`

### Integrated mainline evidence
- `docs/validation/mainline-summary-20260422_mainline.md`

## Current standard flow

The standard project flow should now be read as:

1. `normalize-candidates`
2. `enrich-candidates`
3. `merge-metadata`
4. `dedup-candidates`
5. `enrich-paper-oa`

For full end-to-end mailbox processing, prepend:
- `scan-mailbox`
- `parse-mails`

## Operational interpretation

This promotion does **not** mean the project is fully finished. It means:
- the current branch has a coherent default
- local strategy churn should decrease sharply
- future work should prioritize generalization checks and workflow polish over new heuristic branching

## Next recommended validation

The next high-value step is:
- run the promoted mainline on a fresh slice not used to make these decisions
- compare correctness and OA-gain stability
- only revisit policy if fresh-slice behavior materially disagrees with the current integrated validation

## Archival rule from this point

Earlier exploratory memos, branch-local planning notes, and superseded replay artifacts should stay in `docs/archive/` or `docs/validation/archive/`.

The active docs layer should stay small and answer only:
- what is the current default
- why it is the default
- what evidence is canonical
- what should be done next
