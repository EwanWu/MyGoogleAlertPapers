# Replay validation report: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/ab_baseline_smoke12_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
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
- matched_source_record_count: `29`
- merged_metadata_proposal_count: `12`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `11`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `140805`
- total_provider_latency_ms: `136505`
- cost_event_count: `76`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `46`
- request_savings_vs_runnable_intents: `6`

## Provider summary
- crossref: events=12, total_latency_ms=22428, estimated_cost_usd=0.000000
- europepmc: events=8, total_latency_ms=12473, estimated_cost_usd=0.000000
- none: events=24, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=12, total_latency_ms=22842, estimated_cost_usd=0.000000
- pubmed: events=8, total_latency_ms=18630, estimated_cost_usd=0.000000
- semanticscholar: events=12, total_latency_ms=60132, estimated_cost_usd=0.000000
