# Europe PMC vs arXiv source expansion comparison (2026-04-10)

## Objective
Compare two candidate free enrichment sources, `Europe PMC` and `arXiv`, on both coverage and resource cost, especially latency, using the current project design and existing validation data.

## Test setup
- code path: minimal probe adapters only, not yet fully integrated into pipeline ordering
- script: `scripts/compare_source_expansion.py`
- source DB: `data/mgap_pkg3_guardrail_100.db`
- sample size: first `100` rows from `paper_candidate_normalized`

## Raw results
### Europe PMC
- tested: `100`
- matched: `48`
- match rate: `0.48`
- average latency: `2095.1 ms`
- median latency: `1867.0 ms`
- matched records with DOI: `46`
- matched records with PMID: `46`
- matched records with abstract: `0` in this probe mode

### arXiv
- tested: `100`
- matched: `2`
- match rate: `0.02`
- average latency: `2033.5 ms`
- median latency: `1562.5 ms`
- matched records with DOI: `0`
- matched records with PMID: `0`
- matched records with abstract: `2`

## Interpretation
### Known
- Europe PMC delivered a much higher hit rate than arXiv on the current 100-candidate slice.
- Europe PMC and arXiv had similar single-query latency order of magnitude, both around ~2 seconds per probe.
- arXiv only helped when a strong arXiv-native signal existed, especially extracted `arxiv_id`.
- Project-local validation data already contains preprint-native candidates:
  - arXiv: `8`
  - medRxiv: `3`
  - bioRxiv: `2`
  - ResearchSquare: `2`

### Inferred
- Europe PMC is viable as a biomedical enrichment source, but probably too expensive to add as a default query for every candidate.
- arXiv should not be a general title-search source in the main cascade, because its match rate is too low relative to cost on mixed scholarly mail.
- arXiv is still worthwhile as a targeted source when `arxiv_id_extracted` is present or the canonical URL is clearly arXiv.

## Resource-cost implications
If a source costs about ~2 seconds per query:
- adding it to all 95 fresh30 candidates would add roughly ~3 minutes of wall-clock time in a purely serial model
- adding it only to a narrow targeted subset is much cheaper and more defensible

For this workflow, source usefulness must be judged by **coverage gained per extra second** rather than raw availability.

## Recommended priority
### 1. Europe PMC: high-value, conditional source
Recommended role:
- biomedical fallback / bridge source
- strongest use cases:
  - DOI/PMID/PMCID reconciliation
  - title-only biomedical candidates after stronger general sources fail
  - PubMed-adjacent metadata strengthening

Recommended query policy:
- do **not** run by default for every candidate
- run when any of these hold:
  - candidate appears biomedical
  - candidate has PMID/PMCID signal
  - Crossref/OpenAlex fail or disagree
  - missing DOI/PMID after primary enrichment

### 2. arXiv: targeted source only
Recommended role:
- arXiv-native preprint resolver
- strongest use cases:
  - `arxiv_id_extracted` present
  - URL host is `arxiv.org`
  - title-only fallback only for AI/imaging candidates if an arXiv hint exists

Recommended query policy:
- run for arXiv-native candidates only
- do not place in general title-search cascade

## Suggested source allocation by information segment
### Core bibliographic establishment
Prefer:
1. Crossref
2. OpenAlex
3. Europe PMC only when biomedical conditions trigger
4. PubMed only for PMID-led or biomedical fallback cases

### Biomedical identifiers and OA bridging
Prefer:
1. Europe PMC
2. PubMed
3. OpenAlex

### Preprint-native metadata
Prefer:
1. arXiv for arXiv-native candidates
2. bioRxiv / medRxiv later, after dedicated adapter work
3. OpenAlex as broad backup

## Recommended next implementation order
1. integrate `Europe PMC` as a conditional fallback source
2. integrate `arXiv` as an arXiv-native targeted resolver
3. only then consider `bioRxiv / medRxiv`

## Bottom-line recommendation
Do not treat Europe PMC and arXiv symmetrically.
- `Europe PMC` deserves earlier integration because it has meaningful coverage on the current biomedical-heavy workflow.
- `arXiv` should be integrated too, but only behind strong arXiv-specific triggers.
