# Replay validation report: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/ab_baseline_smoke18_20260427.db`
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
- provider_intent_count: `76`
- source_record_count: `76`
- matched_source_record_count: `45`
- merged_metadata_proposal_count: `18`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `17`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `187390`
- total_provider_latency_ms: `185785`
- cost_event_count: `112`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `67`
- request_savings_vs_runnable_intents: `9`

## Provider summary
- crossref: events=18, total_latency_ms=31109, estimated_cost_usd=0.000000
- europepmc: events=11, total_latency_ms=16449, estimated_cost_usd=0.000000
- none: events=36, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=18, total_latency_ms=21389, estimated_cost_usd=0.000000
- pubmed: events=11, total_latency_ms=24976, estimated_cost_usd=0.000000
- semanticscholar: events=18, total_latency_ms=91862, estimated_cost_usd=0.000000
