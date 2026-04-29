# Enrichment plan snapshot (data/mgap_pkgB_large_slice150_seed_20260416_slice150.db)

- candidate_count: 368
- provider_intent_count: 1405
- unique_intent_count: 1149
- duplicate_intent_count: 256
- identifier_driven_intents: 502
- title_search_intents: 903
- identifier_driven_unique_intents: 398
- title_search_unique_intents: 751
- dedup_only_request_count: 1149
- recommended_request_count: 1025
- request_savings_vs_naive: 380
- request_savings_vs_dedup_only: 124

## Provider breakdown

| provider | total_intents | unique_intents | duplicate_intents |
| --- | ---: | ---: | ---: |
| crossref | 368 | 298 | 70 |
| openalex | 368 | 298 | 70 |
| semanticscholar | 368 | 298 | 70 |
| europepmc | 146 | 123 | 23 |
| pubmed | 146 | 123 | 23 |
| arxiv | 9 | 9 | 0 |

## Query-type breakdown

| provider | query_type | total_intents | unique_intents |
| --- | --- | ---: | ---: |
| crossref | title | 207 | 171 |
| openalex | title | 207 | 171 |
| semanticscholar | title | 207 | 171 |
| crossref | doi | 161 | 127 |
| openalex | doi | 161 | 127 |
| semanticscholar | doi | 161 | 127 |
| europepmc | title | 141 | 119 |
| pubmed | title | 141 | 119 |
| arxiv | arxiv_id | 9 | 9 |
| europepmc | pmid | 5 | 4 |
| pubmed | pmid | 5 | 4 |

## Execution recommendations

| provider | query_type | mode | total_intents | unique_intents | recommended_request_count | savings_vs_naive | savings_vs_dedup_only |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| openalex | doi | batch_after_dedup | 161 | 127 | 3 | 158 | 124 |
| crossref | title | dedup_only | 207 | 171 | 171 | 36 | 0 |
| openalex | title | dedup_only | 207 | 171 | 171 | 36 | 0 |
| semanticscholar | title | dedup_only | 207 | 171 | 171 | 36 | 0 |
| crossref | doi | dedup_only | 161 | 127 | 127 | 34 | 0 |
| semanticscholar | doi | dedup_only | 161 | 127 | 127 | 34 | 0 |
| europepmc | title | dedup_only | 141 | 119 | 119 | 22 | 0 |
| pubmed | title | dedup_only | 141 | 119 | 119 | 22 | 0 |
| europepmc | pmid | dedup_only | 5 | 4 | 4 | 1 | 0 |
| pubmed | pmid | dedup_only | 5 | 4 | 4 | 1 | 0 |
| arxiv | arxiv_id | dedup_only | 9 | 9 | 9 | 0 | 0 |

## Top duplicate query groups

| provider | query_type | query_key | candidate_count | extra_intents |
| --- | --- | --- | ---: | ---: |
| crossref | doi | 10.1148/radiol.251586 | 4 | 3 |
| openalex | doi | 10.1148/radiol.251586 | 4 | 3 |
| semanticscholar | doi | 10.1148/radiol.251586 | 4 | 3 |
| crossref | doi | 10.1007/s00330-026-12469-9 | 3 | 2 |
| crossref | doi | 10.1093/ejhf/xuag062 | 3 | 2 |
| crossref | doi | 10.1093/eurheartj/ehag182 | 3 | 2 |
| crossref | doi | 10.1152/ajpheart.00043.2026 | 3 | 2 |
| crossref | doi | 10.1152/ajpheart.00668.2025 | 3 | 2 |
| crossref | title | FDG PET-CT uncovers cardiac sarcoidosis when CMR is inconclusive: the impact of multimodal imaging | 3 | 2 |
| crossref | title | Left Bundle Branch Area Stylet-Driven Lead: Performance, Safety and Quality of Life at 12 Months Post Implant (The BIO-CONDUCT IDE Study) | 3 | 2 |
