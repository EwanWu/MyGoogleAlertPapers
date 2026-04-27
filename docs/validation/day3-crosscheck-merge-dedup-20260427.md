# Replay validation report: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day3_crosscheck_merge_dedup_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- stages: `merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `0`
- source_record_count: `0`
- matched_source_record_count: `0`
- merged_metadata_proposal_count: `60`
- normalized_only_fallback_proposal_count: `60`
- canonical_paper_count: `52`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `17`
- total_provider_latency_ms: `0`
- cost_event_count: `120`
- batch_run_count: `2`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- none: events=120, total_latency_ms=0, estimated_cost_usd=0.000000
