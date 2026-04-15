# Package 3 100-mail validation: detailed result and resource-cost analysis

## Date
2026-04-10

## Status
Completed.

This run executed a fresh end-to-end validation on a larger real mailbox slice and reached a clean terminal state:
- database built successfully
- full pipeline completed: `scan -> parse -> normalize -> enrich -> merge -> dedup -> reports -> review export`
- review queue exported successfully
- blocked-for-review candidates: `0`

## Reproducibility

### Run configuration
- project: `~/NewCareer/Openclaw/proj/MyGoogleAlertPapers`
- mailbox account: `issac`
- database: `data/mgap_pkg3_guardrail_100.db`
- review export: `data/exports/mgap_pkg3_guardrail_100_review.jsonl`
- scan limit: `100`

### Commands used
```bash
export IMAP_ACCOUNT=issac
export SQLITE_PATH=data/mgap_pkg3_guardrail_100.db
rm -f "$SQLITE_PATH"
python3 -m mygooglealertpapers.cli init-db
python3 -m mygooglealertpapers.cli scan-mailbox --limit 100 --unseen-only
python3 -m mygooglealertpapers.cli parse-mails --limit 300
python3 -m mygooglealertpapers.cli normalize-candidates --limit 500
python3 -m mygooglealertpapers.cli enrich-candidates --limit 500
python3 -m mygooglealertpapers.cli merge-metadata --limit 500
python3 -m mygooglealertpapers.cli dedup-candidates --limit 500
python3 -m mygooglealertpapers.cli report-batch
python3 -m mygooglealertpapers.cli report-normalization
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
python3 -m mygooglealertpapers.cli export-review-queue --output data/exports/mgap_pkg3_guardrail_100_review.jsonl
```

---

## 1. Pipeline outcome

### Batch summary
- scanned mails: `100`
- detected Google Scholar mails: `64`
- extracted candidates: `249`
- cost events logged: `1861`

### Normalization summary
- normalized candidates: `249 / 249`
- DOI extracted: `114`
- PMID extracted: `2`
- PMCID extracted: `3`
- arXiv extracted: `8`

### Enrichment summary
- provider intents / source records: `996`
- matched source records: `503`
- overall source-match rate: `50.5%`

Provider-level matched coverage:
- Crossref: `199 / 249 = 79.9%`
- OpenAlex: `167 / 249 = 67.1%`
- PubMed: `104 / 249 = 41.8%`
- Semantic Scholar: `33 / 249 = 13.3%`

### Merge summary
- merged proposals: `203`
- proposals with conflicts: `52`
- low-confidence proposals: `16`
- canonical-blocked proposals: `0`
- grade A: `36`
- grade B: `4`
- grade C: `12`

### Dedup summary
- paper candidates: `249`
- canonical papers: `164`
- candidate-paper links: `203`
- blocked-for-review candidates: `0`
- compression ratio: `164 / 249 = 0.659`
- accepted-link yield: `203 / 249 = 81.5%`
- canonical yield: `164 / 249 = 65.9%`

### Review queue summary
- blocked candidates: `0`
- exported review rows: `0`
- review export file size: `0 B`

---

## 2. Resource-cost analysis

## 2.1 Wall-clock runtime by stage

### Batch runtime summary
- `scan`: `92,396 ms` = `92.4 s`
- `extract_candidates`: `200 ms`
- `normalize_candidates`: `14 ms`
- `enrich_candidates`: `2,219,856 ms` = `36.998 min`
- `merge_metadata`: `212 ms`
- `dedup_candidates`: `13 ms`

### End-to-end runtime
- total pipeline runtime: `2,312,691 ms`
- total wall time: `38.54 min`

### Runtime share
- enrichment: `95.99%`
- scan: `4.00%`
- extract + normalize + merge + dedup combined: `<0.02%`

### Throughput-style views
- end-to-end time per scanned mail: `23.13 s/mail`
- end-to-end time per candidate: `9.29 s/candidate`
- enrichment time per candidate: `8.92 s/candidate`
- average provider-intent latency: `2.21 s/intent`

### Main operational conclusion
The system is now correctness-stable on this slice, but runtime is still overwhelmingly controlled by enrichment IO rather than merge/dedup logic.

---

## 2.2 Provider-side latency and hit profile

### Provider average latencies
- Crossref: `2007.6 ms`
- OpenAlex: `2966.4 ms`
- PubMed: `2642.1 ms`
- Semantic Scholar: `1224.7 ms`

### Provider max observed per-candidate latency
- Crossref max: `6220 ms`
- OpenAlex max: `22796 ms`
- PubMed max: `11552 ms`
- Semantic Scholar max: `7491 ms`

### Cache-hit rates in `candidate_enrichment_status`
- Crossref: `42 / 249 = 16.9%`
- OpenAlex: `19 / 249 = 7.6%`
- PubMed: `42 / 249 = 16.9%`
- Semantic Scholar: `42 / 249 = 16.9%`

### Status distribution
- Crossref: `199 ok`, `50 no_match`
- OpenAlex: `167 ok`, `82 no_match`
- PubMed: `104 ok`, `145 no_match`
- Semantic Scholar: `33 ok`, `216 no_match`

### Query-type effectiveness
- Crossref DOI query: `95 / 114 = 83.3%`
- Crossref title query: `104 / 135 = 77.0%`
- OpenAlex DOI batch: `95 / 114 = 83.3%`
- OpenAlex title query: `72 / 135 = 53.3%`
- PubMed PMID query: `2 / 2 = 100%`
- PubMed title query: `102 / 247 = 41.3%`
- Semantic Scholar DOI query: `23 / 114 = 20.2%`
- Semantic Scholar title query: `10 / 135 = 7.4%`

### Interpretation
1. DOI-based lookup remains much more reliable than title fallback.
2. Crossref and OpenAlex are still the two most important providers for high-yield enrichment.
3. PubMed title query has limited match quality and should remain under conservative trust rules.
4. Semantic Scholar currently adds relatively little recall for this workload while still consuming request budget and latency.

---

## 2.3 Storage and artifact footprint

- SQLite DB size: `37 MB`
- query cache rows: `828`
- cache rows per candidate: `3.33`
- review export size: `0 B`

### Table counts
- `raw_mail_snapshot`: `100`
- `mail_ingestion_record`: `100`
- `paper_candidate`: `249`
- `paper_candidate_normalized`: `249`
- `candidate_enrichment_status`: `996`
- `source_record`: `996`
- `merged_metadata_proposal`: `203`
- `candidate_paper_link`: `203`
- `canonical_paper`: `164`
- `merge_review_queue`: `0`
- `cost_event`: `1861`
- `batch_run`: `6`

---

## 2.4 Monetary / token accounting

Recorded in `cost_event` for this run:
- `request_count`: `0`
- `tokens_total`: `0`
- `estimated_cost_usd`: `0`

### Important note
This does **not** mean the run used zero external resources.
It means the current instrumentation is primarily capturing:
- event counts
- latency
- stage coverage

It is **not yet** recording provider request counts or billable cost in a meaningful way for this pipeline.
So the practical resource-cost view for now should be interpreted as:
- wall-clock time
- provider event count
- cache usage
- DB / artifact footprint
rather than actual API billing.

---

## 3. Correctness interpretation

## Known
- The full 100-mail slice completed successfully.
- `blocked-for-review = 0`.
- `canonical-blocked proposals = 0`.
- The pipeline did not stall under the conservative merge guardrail.
- The review queue did not re-expand on the larger slice.

## Inferred
- The main systematic error class, PubMed title-fallback DOI noise, is now largely controlled.
- Current guardrail + suppression rules generalize beyond the earlier 30-mail and 60-mail validation slices.
- Additional merge-rule expansion is no longer the highest-value next step.

## Still not proven by this run alone
- every accepted canonical assignment is correct
- every DOI resolution is optimal
- provider trust weighting is fully settled for all future distributions

---

## 4. Comparison with earlier validated slices

### Final validated state across slices
- 30-mail final state: `blocked=1`, `canonical=44`, `links=50`
- 60-mail final state: `blocked=0`, `canonical=101`, `links=114`
- 100-mail fresh run: `blocked=0`, `canonical=164`, `links=203`

### What matters
- the 60-mail slice already cleared the review queue after the refined suppression rule
- the 100-mail fresh full-pipeline run also cleared the review queue
- this is a materially stronger signal than only rerunning merge/dedup on old DBs

---

## 5. Bottom-line judgment

The larger-slice validation is complete and successful.

The main result is not just that the system still runs.
It is that the current conservative Package 3 policy now appears to be:
- operationally stable on a larger live slice
- strong enough to prevent review-queue explosions
- selective enough to avoid obvious overblocking on this run

The dominant remaining engineering constraint is now **enrichment cost/latency**, not merge correctness.

---

## 6. Recommended next step

The best next move is **accepted-merge audit sampling**, not more rule expansion.

Recommended audit set:
- 10 accepted cases with conflicts
- 10 accepted cases where PubMed contributed evidence
- 10 accepted cases where final DOI came from a single provider path

Goal:
check whether there is any residual class of silently wrong canonical assignments that no longer enters the review queue.
