# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day13_large_fixed_url_identity_doi_20260502.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml`
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
- provider_intent_count: `681`
- source_record_count: `681`
- matched_source_record_count: `543`
- merged_metadata_proposal_count: `358`
- normalized_only_fallback_proposal_count: `29`
- canonical_paper_count: `283`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `665839`
- total_provider_latency_ms: `654373`
- cost_event_count: `1407`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `407`
- processed_runnable_intents: `755` / `755`
- pre_experimental_runnable_provider_intents: `1393`
- experimental_skipped_provider_intents: `638`
- request_savings_vs_processed_intents: `348`
- request_savings_vs_total_planned_intents: `348`
- shared_title_reuse_group_count: `57`
- shared_title_reuse_request_savings: `67`
- shared_title_reuse_request_savings_by_provider: `{'openalex': 34, 'crossref': 33}`
- title_lane_group_count: `326`
- title_lane_request_count: `253`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 270, 'cluster_leader_path': 56}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 197, 'cluster_leader_path': 56}`
- title_lane_group_counts_by_provider: `{'openalex': 163, 'crossref': 163}`
- title_lane_request_counts_by_provider: `{'openalex': 163, 'crossref': 90}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 135, 'cluster_leader_path': 28}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 135, 'cluster_leader_path': 28}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 135, 'cluster_leader_path': 28}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 62, 'cluster_leader_path': 28}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 242, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 169, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 121, 'mixed_non_doi_identifier': 14}, 'crossref': {'url_canonical_only': 121, 'mixed_non_doi_identifier': 14}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 121, 'mixed_non_doi_identifier': 14}, 'crossref': {'url_canonical_only': 48, 'mixed_non_doi_identifier': 14}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `{'url_canonical_only': 5}`
- openalex_title_pick_best_accepted_subreasons: `['url_canonical_only']`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `73`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 73}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 73}`
- post_openalex_unsuppressed_targeted_group_count: `48`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 48}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 48}`
- title_lane_post_prelink_residual_group_count: `326`
- title_lane_post_prelink_residual_request_count: `253`

## Provider summary
- arxiv: events=9, total_latency_ms=14956, estimated_cost_usd=0.000000
- crossref: events=294, total_latency_ms=325586, estimated_cost_usd=0.000000
- europepmc: events=5, total_latency_ms=8585, estimated_cost_usd=0.000000
- none: events=726, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=297769, estimated_cost_usd=0.000000
- pubmed: events=5, total_latency_ms=7477, estimated_cost_usd=0.000000
