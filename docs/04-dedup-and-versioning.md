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
