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
