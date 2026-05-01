# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_fresh30_20260410.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_post_openalex_fresh30_control_20260430.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- http_fixture_record: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_post_openalex_fresh30_control_20260430.jsonl`
- http_fixture_replay: `None`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `95`
- replay_candidate_count: `95`
- normalized_candidate_count: `95`
- dirty_doi_source_count: `7`
- dirty_doi_output_count: `7`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `196`
- source_record_count: `196`
- matched_source_record_count: `129`
- merged_metadata_proposal_count: `95`
- normalized_only_fallback_proposal_count: `20`
- canonical_paper_count: `75`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `236563`
- total_provider_latency_ms: `233096`
- cost_event_count: `386`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `127`
- processed_runnable_intents: `196` / `196`
- pre_experimental_runnable_provider_intents: `365`
- experimental_skipped_provider_intents: `169`
- request_savings_vs_processed_intents: `69`
- request_savings_vs_total_planned_intents: `69`
- shared_title_reuse_group_count: `22`
- shared_title_reuse_request_savings: `24`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 12, 'openalex': 12}`
- title_lane_group_count: `88`
- title_lane_request_count: `88`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 66, 'cluster_leader_path': 22}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 66, 'cluster_leader_path': 22}`
- title_lane_group_counts_by_provider: `{'crossref': 44, 'openalex': 44}`
- title_lane_request_counts_by_provider: `{'crossref': 44, 'openalex': 44}`
- title_lane_group_counts_by_provider_reason: `{'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}, 'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}}`
- title_lane_request_counts_by_provider_reason: `{'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}, 'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 33, 'cluster_leader_path': 11}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 54, 'mixed_non_doi_identifier': 12}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 54, 'mixed_non_doi_identifier': 12}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'crossref': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}, 'openalex': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'crossref': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}, 'openalex': {'url_canonical_only': 27, 'mixed_non_doi_identifier': 6}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- title_lane_post_prelink_residual_group_count: `88`
- title_lane_post_prelink_residual_request_count: `88`

## Provider summary
- arxiv: events=6, total_latency_ms=7448, estimated_cost_usd=0.000000
- crossref: events=95, total_latency_ms=144595, estimated_cost_usd=0.000000
- none: events=190, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=95, total_latency_ms=81053, estimated_cost_usd=0.000000
