# Integrated mainline validation summary (20260422_mainline)

## Profiles
- control: `conditional_sources_v2`
- treatment: `conditional_sources_v2_author_blob_fallback_only + post_dedup_unpaywall`

## Baseline enrich cost (donor v2 source-record run)
- provider latency total: `2197341` ms
- paid LLM usage: `False`

## Track A merge/dedup delta under reused source records
| metric | control | treatment | delta |
|---|---:|---:|---:|
| canonical_paper_count | 292 | 291 | -1 |
| merge_review_queue_count | 4 | 4 | 0 |
| severe_doi_conflict_count | 4 | 4 | 0 |
| normalized_only_fallback_proposal_count | 35 | 34 | -1 |

## Garbage-case check
- candidate: `cand_400e144162689110`
- control present in merged proposal: `True`
- treatment present in merged proposal: `False`
- blocked in treatment: `True`
- only-control candidate diff: `['cand_400e144162689110']`
- only-treatment candidate diff: `[]`
- collateral loss candidates: `[]`
- targeted removal only: `True`

## Post-dedup OA stage
- canonical DOI count: `263`
- paper_open_access rows: `263`
- is_oa=true rows: `156`
- best_oa_url filled rows: `156`
- OA stage latency: `322042` ms
- OA stage cost events: `263`
- OA cache hits: `0`

## Bottom line
- Track A targeted garbage removal only: `True`
- Review burden not worse: `True`
- Severe DOI conflict not worse: `True`
- OA URLs added by integrated candidate: `156`
