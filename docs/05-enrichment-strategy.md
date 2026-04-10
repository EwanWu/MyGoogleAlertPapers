# Metadata Enrichment Strategy

## Objective
Use low-cost, explainable API cascades to enrich paper candidates before deduplication and canonicalization.

## Identifier-first policy
If a candidate contains a strong identifier, prefer direct identifier lookups.

### DOI-first path
Suggested order:
1. Crossref
2. OpenAlex
3. Semantic Scholar
4. PubMed only as fallback when PMID/PMCID confirmation or missing biomedical fields are needed

### PMID-first path
Suggested order:
1. PubMed
2. Europe PMC
3. OpenAlex
4. Semantic Scholar

PubMed remains primary for PMID-led resolution.

## Title-based path
When no strong identifier is available, use title search.

### Biomedical-leaning candidates
Suggested order:
1. Crossref if DOI is available
2. OpenAlex
3. Semantic Scholar
4. PubMed as fallback for title-only biomedical candidates, or when PMID / abstract / PMCID is still missing
5. Europe PMC if added later

### General scholarly candidates
Suggested order:
1. Crossref
2. Semantic Scholar
3. OpenAlex

## Source confidence guidance
- PubMed / Europe PMC: strong biomedical fallback sources, especially for PMID, PMCID, and some abstracts, but should not be the default authority for DOI-led record establishment
- Crossref: strong for DOI-centered formal publication metadata
- OpenAlex: useful for broad discovery, IDs, linking, and often useful abstract coverage, but not sole abstract authority
- Semantic Scholar: useful for graph-style enrichment and search support

## Field-level merge policy
- Preferred record establishment should rely first on Crossref and OpenAlex when they agree on title, venue, DOI, and year.
- PubMed should be treated as fallback-only for `title`, `venue`, and `doi` during merge selection.
- PubMed remains eligible to supply `abstract`, `pmid`, and `pmcid`, and can still act as a last-resort source when no non-PubMed record exists.

## Validation status
Fresh-30 validation on `2026-04-10` showed that demoting PubMed to fallback reduced provider intents from `380` to `341` while keeping merged proposals at `73` and canonical papers at `56` in the tested slice.

## Merge behavior
Do not collapse all source outputs directly into a single truth record.
Instead:
1. retain source_record per provider
2. produce merged_metadata_proposal with explicit priority trace and conflict flags
