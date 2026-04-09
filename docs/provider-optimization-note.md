# Provider Optimization Note

## Purpose
Consolidate provider-specific optimization constraints and opportunities using official documentation as the primary source, then translate them into implementation priorities for this project.

## OpenAlex
### Official signals reviewed
- Official rate limits/authentication page indicates API-key/pricing/usage-limit framing in current documentation.
- Official docs also indicate API usage limits such as 100,000 requests/day in overview-style materials.
- Official filter-entity-lists docs indicate multi-ID/OR filtering support and recommend retrieving full result sets with `per-page=100`.
- Search results and doc ecosystem show some old/new wording overlap; therefore, optimization should be based on the current authentication/rate-limit documentation rather than older "polite pool" assumptions.

### Practical conclusions
- Do **not** assume older polite-pool behavior is the main optimization path.
- Prefer current documented authentication/rate-limit behavior as authoritative.
- High-value optimization: **batch DOI lookup** using OR filter syntax for works.
- Additional future optimization: align requests with currently documented authentication/rate-limit requirements once project credentials/policy are confirmed.

### Recommended implementation order
1. OpenAlex DOI batching for identifier-first enrichment.
2. Re-check latest auth/rate-limit details before adding any account/key-specific optimization.
3. Leave title-search optimization secondary to identifier-first batching.

## Crossref
### Official signals reviewed
- Current official access/authentication documentation still emphasizes `mailto` and rate-limit behavior.
- Crossref documentation/blog/community posts continue to describe `mailto` as the correct way to improve request handling and contactability.

### Practical conclusions
- `mailto` remains a valid and low-risk optimization to add.
- Caching and reducing duplicate title fallback remain important alongside `mailto`.
- Crossref title fallback should remain guarded by stricter acceptance logic.

### Recommended implementation order
1. Add `mailto` support.
2. Keep cache + acceptance tightening.
3. Consider later request-shaping improvements only after validating impact.

## NCBI / PubMed E-utilities
### Official signals reviewed
- Official docs and E-utilities guidance emphasize API keys for higher request rates.
- Official docs recommend using History server / batch retrieval for larger workloads.
- Official docs recommend batched retrieval patterns instead of one-request-per-record loops.

### Practical conclusions
- Current single-record style is acceptable for small validation slices but not ideal for larger-scale runs.
- Medium-term optimization should move toward batch-oriented retrieval and stronger use of identifiers.
- NCBI API key becomes important if throughput needs to rise beyond low-rate serial use.

### Recommended implementation order
1. Keep current small-scale mode for validation slices.
2. Defer PubMed batching until after OpenAlex batching and Crossref `mailto` are in place.
3. When scaling, move to History-server/batch-oriented requests and API-key-aware rate usage.

## Cross-provider strategy implications
### What to optimize first
1. Cache and duplicate-request elimination.
2. Crossref `mailto`.
3. OpenAlex DOI batching.
4. Later: PubMed batching / History server.

### What not to assume
- Do not assume all older documentation patterns are still current for OpenAlex.
- Do not optimize title fallback before identifier-first paths and acceptance gates are stable.
- Do not prioritize concurrency ahead of request reduction, caching, and batching.

## Immediate next coding targets
1. Add Crossref `mailto` support in requests.
2. Implement OpenAlex DOI batching in enrichment pipeline.
3. Re-run a small controlled slice to measure first-run latency reduction.
