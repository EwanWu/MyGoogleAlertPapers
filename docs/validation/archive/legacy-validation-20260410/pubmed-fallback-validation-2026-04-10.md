# PubMed fallback validation note (2026-04-10)

## Objective
Validate whether `PubMed` can be demoted from a default record-establishment source to a fallback-only source, mainly used for missing biomedical fields.

## Code changes tested
- enrich-stage demotion commit: `040607c`
- merge-stage field-level fallback rule:
  - PubMed is fallback-only for `title`, `venue`, and `doi`
  - PubMed remains eligible for `abstract`, `pmid`, and `pmcid`

## Validation runs
### Baseline fresh30
- database: `data/mgap_fresh30_20260410.db`
- provider intents: `380`
- merged proposals: `73`
- canonical papers: `56`

### Enrich demotion only
- database: `data/mgap_fresh30_pubmedfallback2_20260410.db`
- provider intents: `341`
- merged proposals: `73`

### Enrich demotion + merge field-level fallback
- database: `data/mgap_fresh30_pubmedmergefallback_20260410.db`
- provider stats:
  - crossref: `70/95` matched
  - openalex: `58/95` matched
  - pubmed: `30/56` matched
  - semanticscholar: `8/95` matched
- merged proposals: `73`
- merge confidence:
  - `0.9`: `60`
  - `0.8`: `11`
  - `0.65`: `2`
- PubMed trace usage in merged proposal:
  - abstract: `23`
  - pmid: `30`
  - title: `3`
  - venue: `3`
  - doi: `3`

## Interpretation
### Known
- Demoting PubMed in enrich reduced provider intents from `380` to `341` on the fresh30 slice.
- Merged proposal count remained `73` after both enrich demotion and merge fallback restriction.
- PubMed still contributed useful `abstract` and `pmid` fields after demotion.
- PubMed influence on `title`, `venue`, and `doi` dropped sharply in merge output.

### Inferred
- Crossref + OpenAlex are sufficient as the main record-establishment path for most DOI-led candidates in this slice.
- PubMed is better treated as a biomedical fallback source than as a default authority for title/venue/DOI establishment.

### Residual risk
- A small number of records remain PubMed-only or PubMed-dominant.
- The fresh30 slice supports the fallback strategy, but larger validation should still be run before treating this as fully settled policy.

## Recommended policy
1. Keep PubMed primary for PMID-led resolution.
2. For DOI-led or DOI-resolved candidates, prefer Crossref and OpenAlex for record establishment.
3. Use PubMed mainly to backfill `abstract`, `pmid`, and `pmcid`.
4. Allow PubMed-only metadata to survive only when no stronger non-PubMed source exists.
