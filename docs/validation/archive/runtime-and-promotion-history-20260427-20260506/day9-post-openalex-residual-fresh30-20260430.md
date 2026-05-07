# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_fresh30_20260410.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day9_post_openalex_residual_fresh30_20260430.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_post_openalex_fresh30_control_20260430.jsonl`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `95`
- replay_candidate_count: `95`
- normalized_candidate_count: `95`
- dirty_doi_source_count: `7`
- dirty_doi_output_count: `7`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `181`
- source_record_count: `181`
- matched_source_record_count: `114`
- merged_metadata_proposal_count: `95`
- normalized_only_fallback_proposal_count: `20`
- canonical_paper_count: `75`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `8705`
- total_provider_latency_ms: `197184`
- cost_event_count: `371`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `112`
- processed_runnable_intents: `196` / `196`
- pre_experimental_runnable_provider_intents: `365`
- experimental_skipped_provider_intents: `169`
- request_savings_vs_processed_intents: `84`
- request_savings_vs_total_planned_intents: `84`
- shared_title_reuse_group_count: `22`
- shared_title_reuse_request_savings: `24`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 12, 'openalex': 12}`
- title_lane_group_count: `88`
- title_lane_request_count: `73`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 66, 'cluster_leader_path': 22}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 51, 'cluster_leader_path': 22}`
- title_lane_group_counts_by_provider: `{'openalex': 44, 'crossref': 44}`
- title_lane_request_counts_by_provider: `{'openalex': 44, 'crossref': 29}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 18, 'cluster_leader_path': 11}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 54, 'mixed_non_doi_identifier': 12}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 39, 'mixed_non_doi_identifier': 12}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}, 'crossref': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}, 'crossref': {'url_canonical_only': 12, 'mixed_non_doi_identifier': 6}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `15`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 15}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 15}`
- post_openalex_unsuppressed_targeted_group_count: `12`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 12}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 12}`
- title_lane_post_prelink_residual_group_count: `88`
- title_lane_post_prelink_residual_request_count: `73`

## Provider summary
- arxiv: events=6, total_latency_ms=8350, estimated_cost_usd=0.000000
- crossref: events=80, total_latency_ms=107781, estimated_cost_usd=0.000000
- none: events=190, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=95, total_latency_ms=81053, estimated_cost_usd=0.000000
