# Free source expansion scout (2026-04-10)

## Objective
Assess whether the current enrichment stack has room for low-cost / free source expansion, especially for preprints and biomedical metadata not well covered by the current Crossref + OpenAlex + Semantic Scholar + PubMed mix.

## Current implemented enrich sources
- `crossref`
- `openalex`
- `semanticscholar`
- `pubmed`

Planned but not implemented in repo structure:
- `europepmc` (`docs/10-implementation-blueprint.md` mentions it, but no active module exists)

## Quick scout of candidate free sources
### 1. arXiv API
- Endpoint tested: `http://export.arxiv.org/api/query?...`
- Result: reachable, returns Atom XML, title search works.
- Strong use case:
  - arXiv-only preprints
  - machine learning / imaging / computer vision papers
- Likely benefit:
  - strong for `arxiv_id`, title, authors, abstract, versioned preprint metadata
- Limitations:
  - weak outside arXiv-covered fields
  - no PMID/PMCID-style biomedical linking

### 2. bioRxiv / medRxiv API
- Endpoint tested:
  - `https://api.biorxiv.org/details/biorxiv/...`
  - `https://api.biorxiv.org/details/medrxiv/...`
  - monthly range listing endpoints
- Result:
  - APIs are reachable
  - range/list endpoints return JSON successfully
  - direct DOI-style lookup behavior still needs exact endpoint shaping and parser work
- Strong use case:
  - bioRxiv / medRxiv preprints
  - especially for biomedical preprints before journal publication metadata stabilizes
- Limitations:
  - endpoint conventions are less obvious than Crossref/OpenAlex
  - integration likely needs careful URL/DOI normalization and title fallback logic

### 3. Europe PMC API
- Endpoint tested: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?...`
- Result: reachable, JSON search works, returns title / DOI / PMID / journal / publication type / OA flag.
- Strong use case:
  - biomedical journal articles and preprints
  - PMID / PMCID / DOI bridging
  - Europe PMC-specific coverage beyond PubMed, including OA and some preprint records
- Likely benefit:
  - best immediate expansion candidate for current pipeline
- Limitations:
  - still biomed-focused, not a general scholarly source

## Project-local evidence that expansion is worthwhile
From `data/mgap_pkg3_guardrail_100.db`, current normalized candidate URLs include at least:
- arXiv: `8`
- medRxiv: `3`
- bioRxiv: `2`
- ResearchSquare: `2`

This means the current mailbox slice already contains preprint-native records that are not ideal fits for the current enrich stack.

## Known
- arXiv is directly integrable today with a simple XML client.
- Europe PMC is directly integrable today with a simple JSON client.
- bioRxiv / medRxiv are reachable and promising, but need one more round of endpoint-specific probing before implementation.
- Existing project data already contains non-trivial preprint traffic.

## Inferred
- The current stack is stronger for journal articles than for preprint-native candidates.
- The highest-value next free source is probably `Europe PMC`, because it fits the existing biomedical pipeline and can strengthen PMID/PMCID/DOI bridging.
- The second highest-value addition is probably `arXiv`, because the project already extracts `arxiv_id` and sees multiple arXiv candidates in validation slices.
- `bioRxiv` / `medRxiv` are likely worth adding after Europe PMC or as a combined preprint package with better DOI normalization.

## Recommended implementation order
1. `Europe PMC`
2. `arXiv`
3. `bioRxiv` / `medRxiv`
4. optionally `ResearchSquare` only if a stable metadata endpoint is found

## Minimal test result summary
- arXiv title query returned a correct title match.
- Europe PMC title query returned a correct match with DOI and PMID.
- bioRxiv / medRxiv listing APIs returned valid payloads, confirming technical reachability.

## Suggested next move
Implement one small enrichment adapter first:
- either `europepmc.py` for biomedical enhancement
- or `arxiv.py` for preprint enhancement

If choosing by immediate impact on this project, `Europe PMC` should go first.
