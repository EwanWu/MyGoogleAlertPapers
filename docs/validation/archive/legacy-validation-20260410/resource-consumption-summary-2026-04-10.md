# Resource consumption summary for conditional-source experiments (2026-04-10)

## Scope
This report summarizes resource consumption across the conditional-source experiment series completed on 2026-04-10.

Included experiment groups:
1. Fresh-30 integration validation
2. Live 100-mail conditional-source validation
3. Same-batch 249-candidate replay validation

## Executive summary
### Main conclusion
The current conditional-source strategy improves output quality and coverage while reducing overall enrichment resource burden in the strict same-batch replay test.

### Most important resource findings
- `arXiv` has extremely favorable cost-benefit: low call volume, high yield.
- `Europe PMC` is useful but materially expensive enough that it should remain narrowed to bridge/fallback usage.
- `PubMed` demotion to fallback substantially reduced provider load without harming overall merged output in the replay setting.
- The strongest same-batch evidence comes from the 249-candidate replay, where total provider-latency burden dropped by about `31.5%` while merged output improved.

## Accounting note
This project does **not** yet implement true monetary billing summaries.
So the current resource accounting should be interpreted in three layers:
1. **System layer**: wall-clock batch durations from `batch_run`
2. **Provider layer**: call counts, matches, average latency, total latency from `source_record`
3. **Bill-like proxy layer**: `cost_event` event counts and `latency_ms` summaries, which approximate infrastructure/API burden but not real USD spend

---

## 1. Fresh-30 integration validation
Source: `docs/validation/conditional-source-integration-2026-04-10.md`

### Version A
- DB: `data/mgap_fresh30_conditional_sources_20260410.db`
- planned provider intents: `379`
- merged proposals: `74`

#### Provider usage
- arxiv: `6` calls, `6` matched, avg `1328.2 ms`
- crossref: `91` calls, `66` matched, avg `1961.4 ms`
- europepmc: `64` calls, `28` matched, avg `1625.7 ms`
- openalex: `91` calls, `52` matched, avg `1078.7 ms`
- pubmed: `36` calls, `23` matched, avg `1976.5 ms`
- semanticscholar: `91` calls, `15` matched, avg `832.6 ms`

### Version B (narrowed Europe PMC)
- DB: `data/mgap_fresh30_conditional_sources_v2_20260410.db`
- planned provider intents: `351`
- merged proposals: `74`

#### Provider usage
- arxiv: `6` calls, `6` matched, avg `1669.2 ms`
- crossref: `91` calls, `66` matched, avg `1988.4 ms`
- europepmc: `36` calls, `10` matched, avg `1689.7 ms`
- openalex: `91` calls, `54` matched, avg `1064.1 ms`
- pubmed: `36` calls, `23` matched, avg `1872.6 ms`
- semanticscholar: `91` calls, `12` matched, avg `818.4 ms`

### Fresh-30 resource interpretation
#### Known
- Narrowing Europe PMC reduced planned intents: `379 -> 351` (`-28`, about `-7.4%`)
- Europe PMC query count dropped: `64 -> 36` (`-28`, about `-43.8%`)
- merged proposals stayed flat at `74`

#### Resource meaning
This is the earliest clear sign that Europe PMC broad DOI-led triggering had poor marginal efficiency.
The narrowed version preserved output while cutting a noticeable amount of provider work.

---

## 2. Live 100-mail conditional-source validation
Source: `docs/validation/package3-conditional-sources-100-validation-2026-04-10.md`

## Comparability warning
This run is operationally useful but **not** strictly comparable to the historical 100-mail baseline, because the live mailbox contents had changed.
So resource numbers here are valid for workload description, but not for strict same-input causal claims.

### Historical baseline
- DB: `data/mgap_pkg3_guardrail_100.db`
- scanned mails: `100`
- detected Scholar mails: `64`
- normalized candidates: `249`
- source records: `996`
- merged proposals: `203`
- canonical papers: `164`

#### System cost
- scan: `92396 ms`
- extract_candidates: `200 ms`
- normalize_candidates: `14 ms`
- enrich_candidates: `2219856 ms`
- merge_metadata: `212 ms`
- dedup_candidates: `13 ms`

#### Provider load
- crossref: `249` calls, `199` matched, total `499883 ms`
- openalex: `249` calls, `167` matched, total `738623 ms`
- pubmed: `249` calls, `104` matched, total `657886 ms`
- semanticscholar: `249` calls, `33` matched, total `304946 ms`
- provider latency proxy total: `2201338 ms`

### New live conditional-source run
- DB: `data/mgap_pkg3_guardrail_100_conditional_20260410.db`
- scanned mails: `100`
- detected Scholar mails: `50`
- normalized candidates: `100`
- merged proposals: `87`
- canonical papers: `79`

#### System cost
- scan: `67604 ms`
- extract_candidates: `137 ms`
- normalize_candidates: `7 ms`
- enrich_candidates: `650876 ms`
- merge_metadata: `41 ms`
- dedup_candidates: `4 ms`

#### Provider load
- arxiv: `2` calls, `2` matched, total `3465 ms`
- crossref: `100` calls, `85` matched, total `223216 ms`
- europepmc: `40` calls, `10` matched, total `89202 ms`
- openalex: `100` calls, `75` matched, total `116340 ms`
- pubmed: `40` calls, `24` matched, total `106954 ms`
- semanticscholar: `100` calls, `21` matched, total `108697 ms`
- provider latency proxy total: `647874 ms`

### Live-100 resource interpretation
#### Known
- arXiv remained low-volume and high-yield.
- Europe PMC contributed useful metadata but imposed non-trivial extra latency.
- OpenAlex latency was much lower in this run than in the historical baseline.

#### Limits
Because input size changed from `249` to `100` normalized candidates, the absolute drop in total cost cannot be attributed only to the strategy.
This run is useful to show that the new strategy is stable under real workload, but not to quantify strict savings.

---

## 3. Same-batch 249-candidate replay validation
Source: `docs/validation/package3-conditional-sources-replay-249-2026-04-10.md`

This is the most trustworthy resource comparison, because it uses the exact same normalized candidate set.

### Baseline
- DB: `data/mgap_pkg3_guardrail_100.db`
- normalized candidates: `249`
- merged proposals: `203`
- canonical papers: `164`
- review queue: `0`

#### System cost
- enrich_candidates: processed `882`, duration `2219856 ms`
- merge_metadata: processed `249`, duration `212 ms`
- dedup_candidates: processed `203`, duration `13 ms`

#### Provider load
- crossref: `249` calls, `199` matched, total `499883 ms`
- openalex: `249` calls, `167` matched, total `738623 ms`
- pubmed: `249` calls, `104` matched, total `657886 ms`
- semanticscholar: `249` calls, `33` matched, total `304946 ms`
- provider latency proxy total: `2201338 ms`

### Replay conditional-source
- DB: `data/mgap_pkg3_guardrail_100_replay_conditional_20260410.db`
- normalized candidates: `249`
- merged proposals: `211`
- canonical papers: `170`
- review queue: `2`

#### System cost
- enrich_candidates: processed `837`, duration `1514821 ms`
- merge_metadata: processed `249`, duration `200 ms`
- dedup_candidates: processed `211`, duration `11 ms`

#### Provider load
- arxiv: `8` calls, `8` matched, total `15347 ms`
- crossref: `249` calls, `197` matched, total `533939 ms`
- europepmc: `98` calls, `28` matched, total `187708 ms`
- openalex: `249` calls, `173` matched, total `281912 ms`
- pubmed: `98` calls, `60` matched, total `232416 ms`
- semanticscholar: `249` calls, `18` matched, total `256693 ms`
- provider latency proxy total: `1508015 ms`

### Replay resource deltas
#### System layer
- enrich processed work: `882 -> 837` (`-45`, about `-5.1%`)
- enrich duration: `2219856 -> 1514821 ms` (`-705035 ms`, about `-31.7%`)

#### Provider layer
- arxiv: `+8` calls, `+15347 ms`
- europepmc: `+98` calls, `+187708 ms`
- crossref: total latency `+34056 ms`
- openalex: total latency `-456711 ms`
- pubmed: total latency `-425470 ms`
- semanticscholar: total latency `-48253 ms`

#### Proxy billing layer
- provider latency proxy total: `2201338 -> 1508015 ms`
- absolute reduction: `693323 ms`
- relative reduction: about `31.5%`

### Replay resource interpretation
This is the key result.
On the same input set, the current strategy consumed **less total external-provider time** while producing **more merged outputs**.

The largest savings came from:
- sharply reducing PubMed usage (`249 -> 98` calls)
- improved OpenAlex runtime in this run
- lower aggregate downstream enrich burden despite adding Europe PMC and arXiv

The largest new costs came from:
- Europe PMC bridge calls
- a small arXiv cost footprint

These new costs were outweighed by the reduced PubMed burden and faster OpenAlex behavior.

---

## Cross-experiment resource findings

## 1. arXiv is a high-efficiency source
Across experiments, arXiv remained:
- low volume
- high match rate
- low total burden relative to utility

### Evidence
- Fresh-30 A: `6/6`
- Fresh-30 B: `6/6`
- Replay-249: `8/8`

### Conclusion
arXiv is resource-efficient and should stay narrow-trigger only.

## 2. Europe PMC is useful but must stay constrained
Across experiments, Europe PMC consistently contributed useful metadata but at a non-trivial cost.

### Evidence
- Fresh-30 narrowing cut Europe PMC queries `64 -> 36` with no loss in merged output
- Replay-249 still required `98` calls and `187708 ms` total provider latency

### Conclusion
Europe PMC should remain a later biomedical bridge/fallback source, not an early broad DOI-led source.

## 3. PubMed demotion delivered the largest clear resource win
PubMed was the clearest heavy source in the old baseline and the clearest place where fallback-only use saved resources.

### Evidence
- Baseline replay-equivalent: `249` PubMed calls, `657886 ms`
- Replay conditional-source: `98` PubMed calls, `232416 ms`
- reduction: `-151` calls, `-425470 ms`

### Conclusion
PubMed fallback demotion is strongly justified from a resource perspective.

## 4. OpenAlex remains a core source, but latency variability exists
OpenAlex was a major source in all runs and showed much better latency in later runs.

### Evidence
- Baseline total latency: `738623 ms`
- Replay total latency: `281912 ms`

### Interpretation
This improvement helps the current strategy look even better, but some portion may reflect provider/runtime variance rather than strategy alone.
Repeated replay would help estimate stability.

## 5. Current billing observability is still incomplete
The project has the right scaffolding (`cost_event`, `estimated_cost_usd`) but actual monetary reporting is not yet implemented.

### Practical consequence
Current resource reporting is strong for:
- time burden
- API burden
- relative comparison

Current resource reporting is weak for:
- real-money cost attribution
- budget forecasting
- spend-per-provider summaries

---

## Bottlenecks
### Historical baseline bottlenecks
1. OpenAlex total latency
2. PubMed total latency
3. Crossref total latency

### Replay bottlenecks after optimization
1. Crossref total latency
2. OpenAlex total latency
3. Semantic Scholar total latency
4. Europe PMC total latency

### Interpretation
After PubMed demotion, the bottleneck stack shifts away from PubMed and becomes more balanced.
Europe PMC enters the cost stack, but not enough to dominate overall burden.

---

## Recommendations
1. Keep `arXiv` as a narrow resolver for arXiv-native candidates.
2. Keep `Europe PMC` only as narrowed biomedical bridge/fallback.
3. Keep `PubMed` as fallback-only for `pmid/pmcid/abstract` and PMID-led cases.
4. Preserve the same-batch replay workflow as the standard method for future resource evaluations.
5. Implement true monetary estimation in `cost_event.estimated_cost_usd` so future summaries can separate:
   - wall-clock burden
   - API burden
   - monetary spend
6. Consider a second replay to test whether OpenAlex latency improvement is stable or incidental.

## Bottom line
The conditional-source experiment series shows a clear resource pattern:
- `arXiv` adds cheap, high-yield value
- `Europe PMC` adds real but bounded cost and should remain constrained
- `PubMed` fallback demotion removes a large amount of unnecessary burden
- on the strict same-batch replay, the new strategy reduces provider-latency burden by about `31.5%` while improving merged and canonical output

From a resource-consumption perspective, the current narrowed conditional-source design is a net improvement over the earlier baseline.
