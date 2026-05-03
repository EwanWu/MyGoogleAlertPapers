# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day14_openalex_repo_shadow_medium60_baseline_off_20260502.db`
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
- provider_intent_count: `105`
- source_record_count: `105`
- matched_source_record_count: `84`
- merged_metadata_proposal_count: `57`
- normalized_only_fallback_proposal_count: `3`
- canonical_paper_count: `48`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `141783`
- total_provider_latency_ms: `139089`
- cost_event_count: `222`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `74`
- processed_runnable_intents: `122` / `122`
- pre_experimental_runnable_provider_intents: `248`
- experimental_skipped_provider_intents: `126`
- request_savings_vs_processed_intents: `48`
- request_savings_vs_total_planned_intents: `48`
- shared_title_reuse_group_count: `8`
- shared_title_reuse_request_savings: `8`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 4, 'openalex': 4}`
- title_lane_group_count: `72`
- title_lane_request_count: `55`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 64, 'cluster_leader_path': 8}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 47, 'cluster_leader_path': 8}`
- title_lane_group_counts_by_provider: `{'openalex': 36, 'crossref': 36}`
- title_lane_request_counts_by_provider: `{'openalex': 36, 'crossref': 19}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 32, 'cluster_leader_path': 4}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 32, 'cluster_leader_path': 4}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 32, 'cluster_leader_path': 4}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 15, 'cluster_leader_path': 4}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 58, 'mixed_non_doi_identifier': 6}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 41, 'mixed_non_doi_identifier': 6}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 29, 'mixed_non_doi_identifier': 3}, 'crossref': {'url_canonical_only': 29, 'mixed_non_doi_identifier': 3}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 29, 'mixed_non_doi_identifier': 3}, 'crossref': {'url_canonical_only': 12, 'mixed_non_doi_identifier': 3}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `{'url_canonical_only': 5}`
- openalex_title_pick_best_accepted_subreasons: `['url_canonical_only']`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `17`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 17}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 17}`
- post_openalex_unsuppressed_targeted_group_count: `12`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 12}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 12}`
- title_lane_post_prelink_residual_group_count: `72`
- title_lane_post_prelink_residual_request_count: `55`

## Provider summary
- crossref: events=43, total_latency_ms=61183, estimated_cost_usd=0.000000
- europepmc: events=1, total_latency_ms=1366, estimated_cost_usd=0.000000
- none: events=117, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=60, total_latency_ms=75631, estimated_cost_usd=0.000000
- pubmed: events=1, total_latency_ms=909, estimated_cost_usd=0.000000
