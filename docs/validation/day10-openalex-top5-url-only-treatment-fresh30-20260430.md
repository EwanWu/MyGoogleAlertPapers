# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_fresh30_20260410.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day10_openalex_top5_url_only_treatment_fresh30_20260430.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day10_openalex_top5_url_only_control_fresh30_20260430.jsonl`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `95`
- replay_candidate_count: `95`
- normalized_candidate_count: `95`
- dirty_doi_source_count: `7`
- dirty_doi_output_count: `7`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `177`
- source_record_count: `177`
- matched_source_record_count: `117`
- merged_metadata_proposal_count: `95`
- normalized_only_fallback_proposal_count: `20`
- canonical_paper_count: `75`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `7469`
- total_provider_latency_ms: `213336`
- cost_event_count: `367`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `108`
- processed_runnable_intents: `196` / `196`
- pre_experimental_runnable_provider_intents: `365`
- experimental_skipped_provider_intents: `169`
- request_savings_vs_processed_intents: `88`
- request_savings_vs_total_planned_intents: `88`
- shared_title_reuse_group_count: `22`
- shared_title_reuse_request_savings: `24`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 12, 'openalex': 12}`
- title_lane_group_count: `88`
- title_lane_request_count: `69`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 66, 'cluster_leader_path': 22}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 47, 'cluster_leader_path': 22}`
- title_lane_group_counts_by_provider: `{'openalex': 44, 'crossref': 44}`
- title_lane_request_counts_by_provider: `{'openalex': 44, 'crossref': 25}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 14, 'cluster_leader_path': 11}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 54, 'mixed_non_doi_identifier': 12}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 35, 'mixed_non_doi_identifier': 12}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}, 'crossref': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}, 'crossref': {'url_canonical_only': 8, 'mixed_non_doi_identifier': 6}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `{'url_canonical_only': 5}`
- openalex_title_pick_best_accepted_subreasons: `['url_canonical_only']`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `19`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 19}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 19}`
- post_openalex_unsuppressed_targeted_group_count: `8`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 8}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 8}`
- title_lane_post_prelink_residual_group_count: `88`
- title_lane_post_prelink_residual_request_count: `69`

## Provider summary
- arxiv: events=6, total_latency_ms=6851, estimated_cost_usd=0.000000
- crossref: events=76, total_latency_ms=111112, estimated_cost_usd=0.000000
- none: events=190, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=95, total_latency_ms=95373, estimated_cost_usd=0.000000
