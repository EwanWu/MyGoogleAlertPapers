# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day11_final_promotion_gate_pkg3_guardrail100_control_20260501.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich, merge, dedup`

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
- merged_metadata_proposal_count: `248`
- normalized_only_fallback_proposal_count: `41`
- canonical_paper_count: `203`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `492404`
- total_provider_latency_ms: `486113`
- cost_event_count: `961`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `289`
- processed_runnable_intents: `510` / `510`
- pre_experimental_runnable_provider_intents: `951`
- experimental_skipped_provider_intents: `441`
- request_savings_vs_processed_intents: `221`
- request_savings_vs_total_planned_intents: `221`
- shared_title_reuse_group_count: `38`
- shared_title_reuse_request_savings: `40`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 20, 'openalex': 20}`
- title_lane_group_count: `230`
- title_lane_request_count: `184`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 192, 'cluster_leader_path': 38}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 146, 'cluster_leader_path': 38}`
- title_lane_group_counts_by_provider: `{'openalex': 115, 'crossref': 115}`
- title_lane_request_counts_by_provider: `{'openalex': 115, 'crossref': 69}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 96, 'cluster_leader_path': 19}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 96, 'cluster_leader_path': 19}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 96, 'cluster_leader_path': 19}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 50, 'cluster_leader_path': 19}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 170, 'mixed_non_doi_identifier': 22}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 124, 'mixed_non_doi_identifier': 22}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 85, 'mixed_non_doi_identifier': 11}, 'crossref': {'url_canonical_only': 85, 'mixed_non_doi_identifier': 11}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 85, 'mixed_non_doi_identifier': 11}, 'crossref': {'url_canonical_only': 39, 'mixed_non_doi_identifier': 11}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `None`
- openalex_title_pick_best_accepted_subreasons: `None`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `46`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 46}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 46}`
- post_openalex_unsuppressed_targeted_group_count: `39`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 39}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 39}`
- title_lane_post_prelink_residual_group_count: `230`
- title_lane_post_prelink_residual_request_count: `184`

## Provider summary
- arxiv: events=8, total_latency_ms=70277, estimated_cost_usd=0.000000
- crossref: events=203, total_latency_ms=234054, estimated_cost_usd=0.000000
- europepmc: events=2, total_latency_ms=4669, estimated_cost_usd=0.000000
- none: events=497, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=249, total_latency_ms=174837, estimated_cost_usd=0.000000
- pubmed: events=2, total_latency_ms=2276, estimated_cost_usd=0.000000
