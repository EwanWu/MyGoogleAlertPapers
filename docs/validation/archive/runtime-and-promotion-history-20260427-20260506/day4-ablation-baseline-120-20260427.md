# Replay validation failure: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day4_ablation_baseline_120_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich`

## Failure
- status: `failed`
- failed_stage: `enrich`
- error_message: `stage timed out after 599s: python3 -m mygooglealertpapers.cli enrich-candidates --limit 120`

## Partial counts at failure
- replay_candidate_count: `368`
- provider_intent_count: `250`
- source_record_count: `250`
- matched_source_record_count: `169`
- merged_metadata_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- cost_event_count: `250`
- batch_run_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `550369`
- total_provider_latency_ms: `545934`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `168`
- processed_runnable_intents: `250` / `474`
- request_savings_vs_processed_intents: `82`
- request_savings_vs_total_planned_intents: `306`
- shared_title_reuse_group_count: `18`
- shared_title_reuse_request_savings: `18`

## Provider summary
- crossref: events=56, total_latency_ms=129540, estimated_cost_usd=0.000000
- europepmc: events=28, total_latency_ms=49779, estimated_cost_usd=0.000000
- openalex: events=83, total_latency_ms=67144, estimated_cost_usd=0.000000
- pubmed: events=28, total_latency_ms=67053, estimated_cost_usd=0.000000
- semanticscholar: events=55, total_latency_ms=232418, estimated_cost_usd=0.000000
