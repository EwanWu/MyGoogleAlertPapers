# Conditional Europe PMC + arXiv integration validation (2026-04-10)

## Objective
Validate the condition-trigger strategy after formal integration into `pipeline/enrich.py`, then validate a narrower Europe PMC trigger.

## Strategy version A
### Europe PMC
Triggered when candidate appeared biomedical and one of the following was true:
- PMID exists
- DOI exists
- title-only fallback path in biomedical-looking candidate

### arXiv
Triggered only when candidate was arXiv-native:
- `arxiv_id_extracted` exists
- or strong arXiv hint in title path

## Strategy version B (narrowed)
### Europe PMC
Triggered only when:
- PMID exists
- or title-only biomedical fallback path is used

DOI-led biomedical candidates no longer trigger Europe PMC directly.

### arXiv
Unchanged, still arXiv-native only.

## Validation run
- mailbox account: `issac`
- scan limit: `30`

## Version A results
- database: `data/mgap_fresh30_conditional_sources_20260410.db`
- planned provider intents: `379`
- provider stats:
  - arxiv: `6` records, `6` matched, avg latency `1328.2 ms`
  - crossref: `91` records, `66` matched, avg latency `1961.4 ms`
  - europepmc: `64` records, `28` matched, avg latency `1625.7 ms`
  - openalex: `91` records, `52` matched, avg latency `1078.7 ms`
  - pubmed: `36` records, `23` matched, avg latency `1976.5 ms`
  - semanticscholar: `91` records, `15` matched, avg latency `832.6 ms`
- merged proposals: `74`
- trace contribution:
  - arxiv title/venue/abstract: `6/6/6`
  - europepmc title/venue/doi/pmid: `28/28/25/25`

## Version B results
- database: `data/mgap_fresh30_conditional_sources_v2_20260410.db`
- planned provider intents: `351`
- provider stats:
  - arxiv: `6` records, `6` matched, avg latency `1669.2 ms`
  - crossref: `91` records, `66` matched, avg latency `1988.4 ms`
  - europepmc: `36` records, `10` matched, avg latency `1689.7 ms`
  - openalex: `91` records, `54` matched, avg latency `1064.1 ms`
  - pubmed: `36` records, `23` matched, avg latency `1872.6 ms`
  - semanticscholar: `91` records, `12` matched, avg latency `818.4 ms`
- merged proposals: `74`
- confidence distribution:
  - `0.9`: `54`
  - `0.8`: `16`
  - `0.65`: `2`
  - `0.45`: `1`
  - `0.25`: `1`
- trace contribution:
  - arxiv title/venue/abstract: `6/6/6`
  - europepmc title/venue/doi/pmid: `10/10/8/8`

## Interpretation
### Known
- Narrowing Europe PMC reduced planned intents from `379` to `351`.
- Europe PMC queries dropped from `64` to `36`.
- Merged proposal count remained `74` after narrowing.
- arXiv stayed clean and high-yield under narrow triggering.
- Version B improved the merge confidence distribution relative to version A.

### Inferred
- Europe PMC should stay as a later biomedical bridge/fallback, not an early DOI-led biomedical source.
- arXiv should remain a narrow resolver only for arXiv-native candidates.
- The narrowed Europe PMC trigger gives a better cost/benefit tradeoff for this workflow.

## Recommended policy
1. Keep `Crossref + OpenAlex + Semantic Scholar` as the main path.
2. Keep `PubMed` for PMID-led and biomedical title fallback.
3. Keep `Europe PMC` only for PMID-led and title-only biomedical fallback / bridge scenarios.
4. Keep `arXiv` only for arXiv-native candidates.
