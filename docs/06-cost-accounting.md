# Cost Accounting Plan

## Goal
Estimate whether scaling from ~100 validation emails to ~8000 emails is practical in token, API, and time terms.

## Track more than token usage
### LLM usage
- prompt tokens
- completion tokens
- total tokens
- estimated cost

### External API usage
- provider name
- request count
- hit/miss
- retry count
- latency
- rate-limit events

### Local processing
- parse time
- normalization time
- enrichment time
- dedup time
- total wall time

## Required reporting levels
### Per email
- candidate count
- provider calls
- token usage
- wall time

### Per candidate
- number of successful enrichments
- number of failed enrichments
- whether LLM fallback was triggered

### Per batch
- average per-email cost
- average per-unique-paper cost
- variance
- long-tail outliers

## Scale-up estimates
Report at least three scenarios:
- optimistic
- neutral
- conservative

Each should estimate:
- total provider calls
- total token usage
- total runtime
- likely bottlenecks

## Cost/accounting state update (2026-04-16)

This plan remains directionally correct, but the project's real accounting state is now more specific:

### What is already observable
- batch-level wall time
- provider-level latency aggregates
- provider event counts through `cost_event`
- stage duration summaries in replay reports
- explicit reporting when no paid LLM path was used

### What is now important to report explicitly as an observability gap
- true provider billing is still not equivalent to the current event log
- paid LLM token/cost accounting should not be implied when the path was not exercised
- when monetary fields are unavailable or placeholder-only, reports should say so directly instead of silently omitting the gap

### Current accounting rule from recent Package A / B work
- if no paid LLM path was exercised, write that explicitly
- keep both technical-resource metrics and economic-resource metrics when available
- when economic-resource metrics are incomplete, surface the missing instrumentation as part of the report

### Current evidence-backed example
In the formal larger-slice Package B replay, the correct statement was:

- `No paid LLM call path was exercised in this replay run.`

This is now the model for future reporting: explicit positive accounting when present, explicit non-use statement when absent.

### Next accounting priority
The next meaningful accounting improvement is not more prose, but better instrumentation for:
- monetary provider cost where available
- request-count correctness by provider/stage
- clearer separation between event logging and true billable resource reporting
