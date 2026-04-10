# Package 3 conditional-source validation on 100-mail slice (2026-04-10)

## Objective
Validate the new conditional-source enrichment strategy on a 100-mail real slice, with explicit recording of:
- system-level execution cost
- provider-level latency/coverage cost
- bill-like cost proxies from `cost_event`
- qualitative issues and optimization opportunities

## Important comparability note
A strict same-batch comparison with the earlier 100-mail baseline was requested.
However, the live mailbox contents had changed by the time this run was executed.
Therefore:
- `data/mgap_pkg3_guardrail_100.db` remains the best historical 100-mail baseline
- `data/mgap_pkg3_guardrail_100_conditional_20260410.db` is a valid 100-mail live validation of the new strategy
- but it is **not** a perfectly same-candidate apples-to-apples comparison, because the extracted Scholar subset changed materially

## Baseline reference
### Historical baseline DB
- `data/mgap_pkg3_guardrail_100.db`

### Baseline run summary
- scanned mails: `100`
- detected Scholar mails: `64`
- normalized candidates: `249`
- source records: `996`
- merged proposals: `203`
- canonical papers: `164`
- enrich duration: `2219856 ms` (~37.0 min)

## New conditional-source run
### Database
- `data/mgap_pkg3_guardrail_100_conditional_20260410.db`

### Batch summary
- scanned mails: `100`
- detected Scholar mails: `50`
- normalized candidates: `100`
- merged proposals: `87`
- canonical papers: `79`

## System-level cost
### Baseline batch runs
- scan: `92396 ms`
- extract_candidates: `200 ms`
- normalize_candidates: `14 ms`
- enrich_candidates: `2219856 ms`
- merge_metadata: `212 ms`
- dedup_candidates: `13 ms`

### New run batch runs
- scan: `67604 ms`
- extract_candidates: `137 ms`
- normalize_candidates: `7 ms`
- enrich_candidates: `650876 ms`
- merge_metadata: `41 ms`
- dedup_candidates: `4 ms`

## Provider-level resource usage
### Baseline provider summary
- crossref: `249` calls, `199` matched, avg `2007.6 ms`, total `499883 ms`
- openalex: `249` calls, `167` matched, avg `2966.4 ms`, total `738623 ms`
- pubmed: `249` calls, `104` matched, avg `2642.1 ms`, total `657886 ms`
- semanticscholar: `249` calls, `33` matched, avg `1224.7 ms`, total `304946 ms`

### New provider summary
- arxiv: `2` calls, `2` matched, avg `1732.5 ms`, total `3465 ms`
- crossref: `100` calls, `85` matched, avg `2232.2 ms`, total `223216 ms`
- europepmc: `40` calls, `10` matched, avg `2230.1 ms`, total `89202 ms`
- openalex: `100` calls, `75` matched, avg `1163.4 ms`, total `116340 ms`
- pubmed: `40` calls, `24` matched, avg `2673.9 ms`, total `106954 ms`
- semanticscholar: `100` calls, `21` matched, avg `1087.0 ms`, total `108697 ms`

## Bill-like cost proxy
The project does not yet store direct USD billing per provider API call.
Current bill-like accounting is represented by `cost_event.latency_ms`, provider event counts, and batch duration.

### Baseline total provider latency proxy
- crossref + openalex + pubmed + semanticscholar = `2201338 ms`

### New total provider latency proxy
- arxiv + crossref + europepmc + openalex + pubmed + semanticscholar = `648?`  
Precise sum from provider totals:
- `3465 + 223216 + 89202 + 116340 + 106954 + 108697 = 647874 ms`

This is not a direct money bill, but it is a useful infrastructure-load proxy and correlates with external API time consumption.

## Merge confidence
### Baseline
- `0.9`: `151`
- `0.8`: `36`
- `0.45`: `12`
- `0.65`: `4`

### New run
- `0.9`: `68`
- `0.8`: `14`
- `0.45`: `5`

## Source trace contribution in new run
- `pubmed` abstract: `23`
- `pubmed` pmid: `24`
- `europepmc` title: `10`
- `europepmc` venue: `10`
- `europepmc` doi: `8`
- `europepmc` pmid: `8`
- `arxiv` title: `2`
- `arxiv` venue: `2`
- `arxiv` abstract: `2`

## Interpretation
### Known
- The new live 100-mail run is operationally stable.
- arXiv remained low-volume and high-yield.
- Europe PMC remained useful under narrowed triggering, but still adds noticeable external-call load.
- OpenAlex latency looked much better in the new run than in the historical baseline.
- Because the candidate pool changed substantially, direct absolute output-count comparison is not scientifically clean.

### Inferred
- The conditional-source design is viable and does not destabilize the workflow.
- The current narrowed Europe PMC trigger is reasonable, but still expensive enough that it should stay in fallback/bridge roles.
- arXiv should remain a narrow resolver only.
- For stronger scientific comparison, the next validation should reuse the **same normalized candidate set** rather than rescan the live mailbox.

## Problems / caveats found
1. **Not same-batch comparable**
   - Historical baseline had `249` normalized candidates from `64` Scholar mails.
   - New run had `100` normalized candidates from `50` Scholar mails.
   - So the mailbox changed enough to prevent strict same-batch conclusions.

2. **Billing granularity still weak**
   - Current system records latency but not direct per-provider monetary spend.
   - This limits accounting-quality reporting.

3. **Europe PMC still non-trivial in cost**
   - Even narrowed, it consumed `40` queries and `89202 ms` total latency on this 100-mail slice.

## Recommended next optimization steps
1. Add a reproducible replay mode that re-runs enrichment on the same `paper_candidate_normalized` set without rescanning mailbox.
2. Add provider-level monetary-estimate accounting in `cost_event` using a configurable pricing table.
3. Keep arXiv as-is.
4. Keep Europe PMC narrowed, and consider one more refinement such as triggering only after primary-source miss or unresolved identifier gaps.

## Bottom line
- The conditional-source strategy appears promising and operationally stable.
- arXiv is clearly worth keeping as a narrow source.
- Europe PMC is worth keeping as a later biomedical bridge/fallback source.
- But the requested strict same-batch 100-case comparison was not fully achieved due to live mailbox drift, so the next serious comparison should reuse the exact prior normalized candidate set.
