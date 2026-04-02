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
4. Europe PMC / PubMed if relevant

### PMID-first path
Suggested order:
1. PubMed
2. Europe PMC
3. OpenAlex
4. Semantic Scholar

## Title-based path
When no strong identifier is available, use title search.

### Biomedical-leaning candidates
Suggested order:
1. PubMed
2. Europe PMC
3. Semantic Scholar
4. OpenAlex
5. Crossref

### General scholarly candidates
Suggested order:
1. Crossref
2. Semantic Scholar
3. OpenAlex

## Source confidence guidance
- PubMed / Europe PMC: strong candidates for biomedical abstract/metadata
- Crossref: strong for DOI-centered formal publication metadata
- OpenAlex: useful for broad discovery, IDs, and linking, but not sole abstract authority
- Semantic Scholar: useful for graph-style enrichment and search support

## Merge behavior
Do not collapse all source outputs directly into a single truth record.
Instead:
1. retain source_record per provider
2. produce merged_metadata_proposal with explicit priority trace and conflict flags
