# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day12_pkg3_guardrail100_targeted_nonarxiv_reject71_review08_20260502.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `249`
- replay_candidate_count: `249`
- normalized_candidate_count: `249`
- dirty_doi_source_count: `9`
- dirty_doi_output_count: `9`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `464`
- source_record_count: `464`
- matched_source_record_count: `339`
- merged_metadata_proposal_count: `240`
- normalized_only_fallback_proposal_count: `33`
- canonical_paper_count: `195`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `142`
- total_provider_latency_ms: `0`
- cost_event_count: `489`
- batch_run_count: `2`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `n/a`
- processed_runnable_intents: `0` / `n/a`
- pre_experimental_runnable_provider_intents: `n/a`
- experimental_skipped_provider_intents: `n/a`
- request_savings_vs_processed_intents: `n/a`
- request_savings_vs_total_planned_intents: `n/a`
- shared_title_reuse_group_count: `n/a`
- shared_title_reuse_request_savings: `n/a`
- shared_title_reuse_request_savings_by_provider: `n/a`
- title_lane_group_count: `n/a`
- title_lane_request_count: `n/a`
- title_lane_group_counts_by_reason: `n/a`
- title_lane_request_counts_by_reason: `n/a`
- title_lane_group_counts_by_provider: `n/a`
- title_lane_request_counts_by_provider: `n/a`
- title_lane_group_counts_by_provider_reason: `n/a`
- title_lane_request_counts_by_provider_reason: `n/a`
- title_lane_identifier_gap_group_counts_by_subreason: `n/a`
- title_lane_identifier_gap_request_counts_by_subreason: `n/a`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `n/a`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `n/a`
- title_lane_cache_hit_group_count: `n/a`
- experimental_title_skip_subreasons_by_provider: `n/a`
- openalex_title_per_page_by_subreason: `n/a`
- openalex_title_pick_best_accepted_subreasons: `n/a`
- experimental_skipped_group_count: `n/a`
- experimental_skipped_group_counts_by_provider: `n/a`
- experimental_skipped_group_counts_by_title_subreason: `n/a`
- post_openalex_suppressed_group_count: `n/a`
- post_openalex_suppressed_group_counts_by_provider: `n/a`
- post_openalex_suppressed_group_counts_by_title_subreason: `n/a`
- post_openalex_unsuppressed_targeted_group_count: `n/a`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `n/a`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `n/a`
- title_lane_post_prelink_residual_group_count: `n/a`
- title_lane_post_prelink_residual_request_count: `n/a`

## Provider summary
- none: events=489, total_latency_ms=0, estimated_cost_usd=0.000000
