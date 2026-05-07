# Replay validation failure: openalex_batching_ablation_no_semanticscholar

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day4_ablation_no_semanticscholar_120_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_ablation_no_semanticscholar.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich`

## Failure
- status: `failed`
- failed_stage: `enrich`
- error_message: `stage timed out after 599s: python3 -m mygooglealertpapers.cli enrich-candidates --limit 120`

## Partial counts at failure
- replay_candidate_count: `368`
- provider_intent_count: `325`
- source_record_count: `325`
- matched_source_record_count: `219`
- merged_metadata_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- cost_event_count: `325`
- batch_run_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `594485`
- total_provider_latency_ms: `590918`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `245`
- processed_runnable_intents: `325` / `354`
- request_savings_vs_processed_intents: `80`
- request_savings_vs_total_planned_intents: `109`
- shared_title_reuse_group_count: `14`
- shared_title_reuse_request_savings: `14`

## Provider summary
- arxiv: events=2, total_latency_ms=4131, estimated_cost_usd=0.000000
- crossref: events=106, total_latency_ms=253510, estimated_cost_usd=0.000000
- europepmc: events=51, total_latency_ms=102680, estimated_cost_usd=0.000000
- openalex: events=114, total_latency_ms=119272, estimated_cost_usd=0.000000
- pubmed: events=52, total_latency_ms=111325, estimated_cost_usd=0.000000
