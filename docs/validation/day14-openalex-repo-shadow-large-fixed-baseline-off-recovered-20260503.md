# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day14_openalex_repo_shadow_large_fixed_baseline_off_recovered_20260503.db`
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
- provider_intent_count: `726`
- source_record_count: `726`
- matched_source_record_count: `487`
- merged_metadata_proposal_count: `357`
- normalized_only_fallback_proposal_count: `25`
- canonical_paper_count: `283`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `8149937`
- total_provider_latency_ms: `8131763`
- cost_event_count: `1451`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `459`
- processed_runnable_intents: `755` / `755`
- pre_experimental_runnable_provider_intents: `1405`
- experimental_skipped_provider_intents: `650`
- request_savings_vs_processed_intents: `296`
- request_savings_vs_total_planned_intents: `296`
- shared_title_reuse_group_count: `61`
- shared_title_reuse_request_savings: `73`
- shared_title_reuse_request_savings_by_provider: `{'openalex': 37, 'crossref': 36}`
- title_lane_group_count: `340`
- title_lane_request_count: `312`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 280, 'cluster_leader_path': 60}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 252, 'cluster_leader_path': 60}`
- title_lane_group_counts_by_provider: `{'openalex': 170, 'crossref': 170}`
- title_lane_request_counts_by_provider: `{'openalex': 170, 'crossref': 142}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 112, 'cluster_leader_path': 30}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 252, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 224, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'crossref': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'crossref': {'url_canonical_only': 98, 'mixed_non_doi_identifier': 14}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `{'url_canonical_only': 5}`
- openalex_title_pick_best_accepted_subreasons: `['url_canonical_only']`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `28`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 28}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 28}`
- post_openalex_unsuppressed_targeted_group_count: `98`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 98}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 98}`
- title_lane_post_prelink_residual_group_count: `340`
- title_lane_post_prelink_residual_request_count: `312`

## Provider summary
- arxiv: events=9, total_latency_ms=19629, estimated_cost_usd=0.000000
- crossref: events=339, total_latency_ms=510533, estimated_cost_usd=0.000000
- europepmc: events=5, total_latency_ms=42668, estimated_cost_usd=0.000000
- none: events=725, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=7551723, estimated_cost_usd=0.000000
- pubmed: events=5, total_latency_ms=7210, estimated_cost_usd=0.000000
