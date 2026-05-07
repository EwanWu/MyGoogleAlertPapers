# Day 4 ablation comparison (limit=120, enrich-only, 2026-04-27)

## What happened
Both ablation runs completed their 600s enrich-only replay window and emitted timeout-safe partial reports:

- baseline: `docs/validation/day4-ablation-baseline-120-20260427.json`
- no-semanticscholar: `docs/validation/day4-ablation-no-semanticscholar-120-20260427.json`

Both runs still timed out at 599s, so this is a **throughput diagnosis**, not a final semantic-quality verdict.

## Core comparison

| metric | baseline | no-semanticscholar | interpretation |
| --- | ---: | ---: | --- |
| total_batch_duration_ms | 550,369 | 594,485 | both hit the same timeout budget class |
| total_provider_latency_ms | 545,934 | 590,918 | wall-clock remains dominated by live provider time |
| matched_source_record_count | 169 | 219 | no-semanticscholar processed much further before timeout |
| processed_runnable_intents | 250 / 474 | 325 / 354 | completion fraction jumps from 52.7% to 91.8% |
| dispatch_request_count | 168 | 245 | removing semanticscholar reduces plan size less than it improves completion fraction |
| processed_per_min | 27.25 | 32.80 | throughput improves by about 20.4% |
| projected_full_runtime | 17.39 min | 10.79 min | semanticscholar removal nearly pulls the run into the 10 min timeout envelope |

## Provider bottleneck diagnosis

### baseline provider latencies
- semanticscholar: `55 events`, `232,418 ms`, avg `4,225.8 ms/event`
- crossref: `56 events`, `129,540 ms`, avg `2,313.2 ms/event`
- openalex: `83 events`, `67,144 ms`, avg `809.0 ms/event`
- pubmed: `28 events`, `67,053 ms`, avg `2,394.8 ms/event`
- europepmc: `28 events`, `49,779 ms`, avg `1,777.8 ms/event`

### no-semanticscholar provider latencies
- crossref: `106 events`, `253,510 ms`, avg `2,391.6 ms/event`
- openalex: `114 events`, `119,272 ms`, avg `1,046.2 ms/event`
- pubmed: `52 events`, `111,325 ms`, avg `2,140.9 ms/event`
- europepmc: `51 events`, `102,680 ms`, avg `2,013.3 ms/event`
- arxiv: `2 events`, `4,131 ms`, avg `2,065.5 ms/event`

## Interpretation
1. **Semantic Scholar is a real primary bottleneck.** In baseline it is the single slowest provider by a wide margin, both in total latency and per-event latency.
2. **Removing Semantic Scholar materially improves the throughput SLA.** The run moves from `52.7%` completion to `91.8%` completion within roughly the same timeout class.
3. **But Semantic Scholar is not the only bottleneck.** Even without it, projected full runtime is still about `10.79 min`, slightly above the current 10 min timeout. So after demoting/removing Semantic Scholar from the default live lane, the next bottlenecks become Crossref + PubMed/EuropePMC-class title lookups.
4. **OpenAlex is not the limiting factor here.** Its per-event latency remains much lower than the slow providers, and the batching signal remains intact.

## Operational conclusion
For live large-slice enrich, the current default chain should not treat Semantic Scholar as a first-line synchronous provider.

### Recommended next move
1. **Demote Semantic Scholar to fallback/async lane** for live throughput-sensitive enrich.
2. Re-run the same `limit=120` enrich-only experiment with:
   - `no-semanticscholar` as the new comparison baseline
   - a second ablation targeting `crossref` or `biomedical title fallback` to isolate the next bottleneck.
3. Keep timeout-safe dispatch accounting enabled; it was essential for making this diagnosis.
