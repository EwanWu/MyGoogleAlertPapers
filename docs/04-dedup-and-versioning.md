# Deduplication and Versioning Strategy

## Deduplication philosophy
- Prefer duplicates over mistaken merges.
- Use identifiers first, then conservative metadata matching.
- Keep uncertain records separate instead of forcing a merge.

## Matching levels

### Level A: strong match
- DOI exact match
- PMID exact match
- PMCID exact match
- trusted external ID exact match

### Level B: high-confidence near match
- normalized title exact match + first author match
- normalized title exact match + close year
- near-exact normalized title + strong author overlap

### Level C: version relation
Used for:
- preprint vs journal publication
- conference vs journal version

These may be linked without collapsing every record detail into one source record.

### Level D: uncertain
- insufficient evidence to merge
- remain in candidate/provisional layer

## Version preference policy
When a main view is needed:
- journal > conference > preprint

## Provenance requirements
Every auto-merge or version link should retain:
- evidence
- confidence
- source trace
- conflict flags where applicable

## External references to borrow ideas from
- Zotero duplicate detection logic
- ASySD conservative citation dedup principles
- BibDedupe bibliographic dedup diagnostics

## Dedup/versioning state update (2026-04-16)

The philosophy above remains correct, but the project has now exercised conservative deduplication in real replay comparisons rather than only as a design proposal.

### Current practical interpretation
- dedup is downstream of `merged_metadata_proposal`, not a substitute for merge correctness
- severe DOI/content conflict handling upstream materially changes what is allowed to enter canonicalization
- `candidate_paper_link` plus review-queue behavior now form part of the operational dedup strategy, not just an eventual refinement

### What recent Package work clarified
- Package A showed that expanding proposal coverage through normalized-only fallback can increase canonical yield without automatically increasing severe conflict burden
- Package B showed that over-tightening fallback before dedup can lower final canonical yield, even when source-match counts rise slightly
- therefore, the dedup system should currently be understood as benefiting more from better upstream proposal coverage than from broad pre-dedup fallback blocking

### Current default interpretation
- keep conservative dedup behavior
- keep uncertain or conflict-heavy cases out of confident canonical promotion
- do not treat broad fallback guardrail escalation as part of the default dedup strategy

### Current recommended reading pair
Use this document together with:

1. `docs/09-packageA-implementation-and-replay-results-2026-04-15.md`
2. `docs/11-packageB-decision-memo-2026-04-16.md`
3. `docs/10-packageB-large-slice150-v2-v4-decision-analysis-2026-04-16.md`
