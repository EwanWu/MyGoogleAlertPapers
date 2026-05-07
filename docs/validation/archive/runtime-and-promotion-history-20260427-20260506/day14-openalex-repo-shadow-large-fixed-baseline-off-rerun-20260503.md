# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day14_openalex_repo_shadow_large_fixed_baseline_off_rerun_20260503.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `702`
- source_record_count: `702`
- matched_source_record_count: `532`
- merged_metadata_proposal_count: `356`
- normalized_only_fallback_proposal_count: `33`
- canonical_paper_count: `281`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `3467324`
- total_provider_latency_ms: `3459062`
- cost_event_count: `1426`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `434`
- processed_runnable_intents: `755` / `755`
- pre_experimental_runnable_provider_intents: `1405`
- experimental_skipped_provider_intents: `650`
- request_savings_vs_processed_intents: `321`
- request_savings_vs_total_planned_intents: `321`
- shared_title_reuse_group_count: `62`
- shared_title_reuse_request_savings: `74`
- shared_title_reuse_request_savings_by_provider: `{'openalex': 37, 'crossref': 37}`
- title_lane_group_count: `340`
- title_lane_request_count: `287`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 280, 'cluster_leader_path': 60}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 227, 'cluster_leader_path': 60}`
- title_lane_group_counts_by_provider: `{'openalex': 170, 'crossref': 170}`
- title_lane_request_counts_by_provider: `{'openalex': 170, 'crossref': 117}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 87, 'cluster_leader_path': 30}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 252, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 199, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'crossref': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'crossref': {'url_canonical_only': 73, 'mixed_non_doi_identifier': 14}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `{'url_canonical_only': 5}`
- openalex_title_pick_best_accepted_subreasons: `['url_canonical_only']`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `53`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 53}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 53}`
- post_openalex_unsuppressed_targeted_group_count: `73`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 73}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 73}`
- title_lane_post_prelink_residual_group_count: `340`
- title_lane_post_prelink_residual_request_count: `287`

## Provider summary
- arxiv: events=9, total_latency_ms=94304, estimated_cost_usd=0.000000
- crossref: events=315, total_latency_ms=252072, estimated_cost_usd=0.000000
- europepmc: events=5, total_latency_ms=5507, estimated_cost_usd=0.000000
- none: events=724, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=3103673, estimated_cost_usd=0.000000
- pubmed: events=5, total_latency_ms=3506, estimated_cost_usd=0.000000
