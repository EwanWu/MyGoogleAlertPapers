# Replay validation report: mgap_title_payload_reuse_experiment

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/ab_title_reuse_smoke12_metrics_20260427.db`
- policy_profile: `/tmp/mgap_title_payload_reuse_experiment.yaml`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `52`
- source_record_count: `52`
- matched_source_record_count: `32`
- merged_metadata_proposal_count: `12`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `11`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `179758`
- total_provider_latency_ms: `177785`
- cost_event_count: `76`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `46`
- request_savings_vs_runnable_intents: `6`
- shared_title_reuse_group_count: `3`
- shared_title_reuse_request_savings: `3`

## Provider summary
- crossref: events=12, total_latency_ms=22646, estimated_cost_usd=0.000000
- europepmc: events=8, total_latency_ms=13770, estimated_cost_usd=0.000000
- none: events=24, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=12, total_latency_ms=17079, estimated_cost_usd=0.000000
- pubmed: events=8, total_latency_ms=70669, estimated_cost_usd=0.000000
- semanticscholar: events=12, total_latency_ms=53621, estimated_cost_usd=0.000000
