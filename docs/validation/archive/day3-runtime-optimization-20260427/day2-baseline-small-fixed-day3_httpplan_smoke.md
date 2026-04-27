# Replay validation failure: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day2_baseline_small-fixed_day3_httpplan_smoke.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- stages: `enrich, merge, dedup`

## Failure
- status: `failed`
- failed_stage: `enrich`
- error_message: `command failed with exit code 1: python3 -m mygooglealertpapers.cli enrich-candidates --limit 60`

## Partial counts at failure
- replay_candidate_count: `368`
- provider_intent_count: `0`
- source_record_count: `0`
- matched_source_record_count: `0`
- merged_metadata_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- cost_event_count: `0`
- batch_run_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `0`
- total_provider_latency_ms: `0`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
