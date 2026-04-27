# Day 3 title payload reuse A/B summary (2026-04-27)

## Experiment setup

- Baseline: `conditional_sources_v2_author_blob_fallback_only`

- Experiment: same profile + `title_payload_reuse_enabled=true` for `crossref`, `openalex`, `semanticscholar`

- Principle: share provider title payload fetch only; keep per-candidate build/match and per-candidate cache writes


## Final-output stability table

| run | matched_source_record_count | canonical_paper_count | merge_review_queue_count | dispatch_request_count | request_savings_vs_runnable_intents | total_provider_latency_ms |
|---|---:|---:|---:|---:|---:|---:|
| baseline_smoke12 | 29 | 11 | 0 | 46 | 6 | 136505 |
| experiment_smoke12 | 37 | 11 | 0 | 46 | 6 | 115177 |
| baseline_smoke12_repeat2 | 28 | 11 | 0 | 46 | 6 | 163665 |
| experiment_smoke12_repeat2 | 34 | 11 | 0 | 46 | 6 | 185243 |
| baseline_smoke18 | 45 | 17 | 0 | 67 | 9 | 185785 |
| experiment_smoke18 | 46 | 17 | 0 | 67 | 9 | 172834 |

## Direct title-reuse observability (new instrumentation)

| run | shared_title_reuse_group_count | shared_title_reuse_intent_count | shared_title_reuse_request_count | shared_title_reuse_request_savings | canonical_paper_count | merge_review_queue_count |
|---|---:|---:|---:|---:|---:|---:|
| baseline_smoke12_metrics | 0 | 0 | 0 | 0 | 11 | 0 |
| experiment_smoke12_metrics | 3 | 6 | 3 | 3 | 11 | 0 |

## Observations

- `canonical_paper_count` and `merge_review_queue_count` stayed unchanged in all completed A/B pairs (`11/0` for smoke12, `17/0` for smoke18).
- `matched_source_record_count` tends to move upward in the experiment runs, but baseline repeats also drift (`29 -> 28 -> 30`), so live-provider noise is real.
- One tighter-timeout repeat failed in `enrich`, confirming that provider latency jitter can confound live A/B evaluation if timeout budget is too narrow.
- New direct instrumentation shows the experiment is actually being exercised: on the latest smoke12 run it reused title payloads for `3` groups covering `6` intents, saving an estimated `3` provider title requests relative to per-intent fetching.
- Those `3` saved title fetches did **not** change final merge/dedup outputs on the tested smoke12 slice (`canonical=11`, `review=0`).

## Interim conclusion

- Mechanistically, the experiment is doing real work now; it is not just a no-op flag.
- Empirically, I still do **not** see evidence of final-output regression on the tested slices.
- But because `matched_source_record_count` shifts under both experiment and baseline repeats, I would keep this behind the feature flag for now and avoid promoting it to default behavior until we have either larger-budget replays or more deterministic recorded-payload comparisons.
