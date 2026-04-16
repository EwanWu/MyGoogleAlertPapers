# Replay validation report: conditional_sources_v4_fallback_guardrail_salvage

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_full_20260416.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100_replay_conditional_sources_v4_fallback_guardrail_salvage_20260416.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v4_fallback_guardrail_salvage.yaml`
- stages: `merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `249`
- replay_candidate_count: `249`
- normalized_candidate_count: `249`
- dirty_doi_source_count: `9`
- dirty_doi_output_count: `9`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `951`
- source_record_count: `951`
- matched_source_record_count: `512`
- merged_metadata_proposal_count: `248`
- normalized_only_fallback_proposal_count: `36`
- canonical_paper_count: `196`
- merge_review_queue_count: `9`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `160`
- total_provider_latency_ms: `0`
- cost_event_count: `497`
- batch_run_count: `2`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- none: events=497, total_latency_ms=0, estimated_cost_usd=0.000000
