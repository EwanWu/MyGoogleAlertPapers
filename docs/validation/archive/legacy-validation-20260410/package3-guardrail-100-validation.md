# Package 3 guardrail validation on 100-mail slice

## Date
2026-04-10

## Run config
- mailbox account: `issac`
- scan limit: `100`
- database: `data/mgap_pkg3_guardrail_100.db`
- review export: `data/exports/mgap_pkg3_guardrail_100_review.jsonl`

## Batch summary
- total scanned mails: `100`
- detected Scholar mails: `64`
- extracted candidates: `249`
- cost events logged: `1861`

## Normalization summary
- normalized candidates: `249/249`
- DOI extracted: `114`
- PMID extracted: `2`
- PMCID extracted: `3`
- arXiv extracted: `8`

## Enrichment summary
- source records: `996`
- matched source records: `503`
- provider breakdown:
  - crossref: `199/249`
  - openalex: `167/249`
  - pubmed: `104/249`
  - semanticscholar: `33/249`

## Merge summary
- merged proposals: `203`
- proposals with conflicts: `52`
- low-confidence proposals: `16`
- canonical-blocked proposals: `0`
- grade_A: `36`
- grade_B: `4`
- grade_C: `12`

## Dedup summary
- paper candidates: `249`
- canonical papers: `164`
- candidate-paper links: `203`
- blocked-for-review candidates: `0`
- compression ratio: `164/249 = 0.659`
- dedup rule counts:
  - new_canonical: `164`
  - doi_exact: `39`

## Review queue summary
- blocked candidates: `0`
- exported review rows: `0`

## Cost / latency summary
- enrich_candidates duration: `2219856 ms` (~37.0 min)
- avg per-provider enrichment latency: `2210.2 ms`
- provider average latencies:
  - crossref: `2007.6 ms`
  - openalex: `2966.4 ms`
  - pubmed: `2642.1 ms`
  - semanticscholar: `1224.7 ms`

## Interpretation
This larger real slice supports the same conclusion as the 30-mail and 60-mail validations:
- conservative merge guardrails do not stall the pipeline
- PubMed title-fallback DOI noise is no longer creating review-queue explosions
- the current Package 3 rules are stable enough to clear a 100-mail slice with zero blocked review cases

## Caveat
This run validates queue-clearing and operational stability on a larger live slice.
It does not by itself prove every canonical assignment is perfect, so future work should still include targeted audit sampling on accepted merges.
