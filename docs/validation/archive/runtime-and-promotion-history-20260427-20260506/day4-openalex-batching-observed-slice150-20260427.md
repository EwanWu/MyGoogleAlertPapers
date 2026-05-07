# Replay validation failure: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day4_openalex_batching_observed_slice150_20260427.db`
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
- provider_intent_count: `800`
- source_record_count: `800`
- matched_source_record_count: `518`
- merged_metadata_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- cost_event_count: `800`
- batch_run_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `1779809`
- total_provider_latency_ms: `1768445`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `538`
- processed_runnable_intents: `800` / `1405`
- request_savings_vs_processed_intents: `262`
- request_savings_vs_total_planned_intents: `867`
- shared_title_reuse_group_count: `42`
- shared_title_reuse_request_savings: `48`

## Provider summary
- arxiv: events=2, total_latency_ms=4402, estimated_cost_usd=0.000000
- crossref: events=187, total_latency_ms=406405, estimated_cost_usd=0.000000
- europepmc: events=80, total_latency_ms=132701, estimated_cost_usd=0.000000
- openalex: events=265, total_latency_ms=200930, estimated_cost_usd=0.000000
- pubmed: events=80, total_latency_ms=178273, estimated_cost_usd=0.000000
- semanticscholar: events=186, total_latency_ms=845734, estimated_cost_usd=0.000000
