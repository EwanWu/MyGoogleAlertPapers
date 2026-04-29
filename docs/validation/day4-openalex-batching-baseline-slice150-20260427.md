# Replay validation failure: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day4_openalex_batching_baseline_slice150_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich, merge, dedup`

## Failure
- status: `failed`
- failed_stage: `enrich`
- error_message: `stage timed out after 1799s: python3 -m mygooglealertpapers.cli enrich-candidates --limit 368`

## Partial counts at failure
- replay_candidate_count: `368`
- provider_intent_count: `775`
- source_record_count: `775`
- matched_source_record_count: `492`
- merged_metadata_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- cost_event_count: `775`
- batch_run_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `0`
- total_provider_latency_ms: `1741549`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `n/a`
- processed_runnable_intents: `0` / `n/a`
- request_savings_vs_processed_intents: `n/a`
- request_savings_vs_total_planned_intents: `n/a`
- shared_title_reuse_group_count: `n/a`
- shared_title_reuse_request_savings: `n/a`

## Provider summary
- arxiv: events=2, total_latency_ms=3593, estimated_cost_usd=0.000000
- crossref: events=175, total_latency_ms=384173, estimated_cost_usd=0.000000
- europepmc: events=80, total_latency_ms=139312, estimated_cost_usd=0.000000
- openalex: events=264, total_latency_ms=210356, estimated_cost_usd=0.000000
- pubmed: events=80, total_latency_ms=189587, estimated_cost_usd=0.000000
- semanticscholar: events=174, total_latency_ms=814528, estimated_cost_usd=0.000000
