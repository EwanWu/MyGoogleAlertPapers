# Experiment reflection and cost notes

## Cost/timing summary

Cost stats
- stage summary:
  - dedup_candidates: events=235, total_latency_ms=0, avg_latency_ms=0.0
  - enrich_candidates: events=732, total_latency_ms=1818158, avg_latency_ms=2483.8
  - extract_candidates: events=66, total_latency_ms=0, avg_latency_ms=0.0
  - merge_metadata: events=244, total_latency_ms=0, avg_latency_ms=0.0
  - normalize_candidates: events=244, total_latency_ms=0, avg_latency_ms=0.0
  - scan: events=100, total_latency_ms=0, avg_latency_ms=0.0
- provider summary:
  - crossref: events=244, total_latency_ms=560165, avg_latency_ms=2295.8
  - none: events=889, total_latency_ms=0, avg_latency_ms=0.0
  - openalex: events=244, total_latency_ms=500625, avg_latency_ms=2051.7
  - pubmed: events=244, total_latency_ms=757368, avg_latency_ms=3104.0


## Observed operational bottlenecks

- The dominant runtime bottleneck was enrichment, especially serial multi-provider external lookups.
- IMAP scanning, parsing, normalization, merge, and dedup were comparatively lightweight.
- A monolithic 100-email enrichment run was impractical; batched execution was materially more stable.
- Crossref/OpenAlex provided high coverage, but each additional provider multiplied runtime.

## Reflections from this experiment

- The low-/non-LLM architecture is viable for this pipeline; the main constraints are external provider latency and metadata disagreement, not lack of semantic modeling.
- Google Scholar alert emails are a workable high-trust ingress layer for paper discovery.
- Conflict exposure at the merge layer is a feature, not a bug, at this stage; it reveals where provider fallbacks are too aggressive or fields need stronger normalization.
- Conservative deduplication is behaving as intended, but it is currently limited by normalization quality and enrichment noise.
- Runtime accounting should have been made first-class earlier; future runs should keep explicit batch-level timing in addition to event-level latency.

## Known issues to address next

- Over-aggressive title fallback in provider enrichment can create false merge conflicts.
- DOI cleanup still needs stronger post-processing for URL suffix artifacts.
- PMCID/PMID backfill from provider records should be strengthened.
- Merge confidence should evolve beyond the current conflict-count heuristic.
- Dedup can be expanded only after the above issues are reduced, otherwise false merges become more likely.

## Recommendations for next iteration

- Tighten provider title-search acceptance rules before broadening dedup logic.
- Add batch-run timing records (start/end/duration/count) as a separate table or structured log.
- Re-run a smaller controlled validation slice after provider matching fixes, then only refresh the 100-email report if metrics improve materially.