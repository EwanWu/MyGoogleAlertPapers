# Replay validation report: openalex_batching_identifier_plus_title_core

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day6_same_batch_cluster_prep_control_20260429.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day6_same_batch_cluster_control_20260429.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `150`
- normalized_candidate_count: `150`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `306`
- source_record_count: `306`
- matched_source_record_count: `223`
- merged_metadata_proposal_count: `149`
- normalized_only_fallback_proposal_count: `14`
- canonical_paper_count: `106`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `586361`
- total_provider_latency_ms: `581879`
- cost_event_count: `605`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `226`
- processed_runnable_intents: `306` / `616`
- request_savings_vs_processed_intents: `80`
- request_savings_vs_total_planned_intents: `390`
- shared_title_reuse_group_count: `22`
- shared_title_reuse_request_savings: `26`

## Provider summary
- arxiv: events=2, total_latency_ms=2396, estimated_cost_usd=0.000000
- crossref: events=150, total_latency_ms=384613, estimated_cost_usd=0.000000
- europepmc: events=2, total_latency_ms=4337, estimated_cost_usd=0.000000
- none: events=299, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=150, total_latency_ms=186742, estimated_cost_usd=0.000000
- pubmed: events=2, total_latency_ms=3791, estimated_cost_usd=0.000000
