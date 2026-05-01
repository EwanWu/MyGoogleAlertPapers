# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_issac_100.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day11_final_promotion_gate_issac100_treatment_20260501.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `244`
- replay_candidate_count: `244`
- normalized_candidate_count: `244`
- dirty_doi_source_count: `7`
- dirty_doi_output_count: `7`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `421`
- source_record_count: `421`
- matched_source_record_count: `342`
- merged_metadata_proposal_count: `243`
- normalized_only_fallback_proposal_count: `28`
- canonical_paper_count: `213`
- merge_review_queue_count: `3`
- severe_doi_conflict_count: `3`

## Runtime and accounting
- total_batch_duration_ms: `504960`
- total_provider_latency_ms: `498095`
- cost_event_count: `908`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `278`
- processed_runnable_intents: `503` / `503`
- pre_experimental_runnable_provider_intents: `941`
- experimental_skipped_provider_intents: `438`
- request_savings_vs_processed_intents: `225`
- request_savings_vs_total_planned_intents: `225`
- shared_title_reuse_group_count: `24`
- shared_title_reuse_request_savings: `24`
- shared_title_reuse_request_savings_by_provider: `{'openalex': 12, 'crossref': 12}`
- title_lane_group_count: `256`
- title_lane_request_count: `174`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 236, 'cluster_leader_path': 20}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 154, 'cluster_leader_path': 20}`
- title_lane_group_counts_by_provider: `{'openalex': 128, 'crossref': 128}`
- title_lane_request_counts_by_provider: `{'openalex': 128, 'crossref': 46}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 118, 'cluster_leader_path': 10}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 118, 'cluster_leader_path': 10}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 118, 'cluster_leader_path': 10}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 36, 'cluster_leader_path': 10}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 214, 'mixed_non_doi_identifier': 22}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 132, 'mixed_non_doi_identifier': 22}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 107, 'mixed_non_doi_identifier': 11}, 'crossref': {'url_canonical_only': 107, 'mixed_non_doi_identifier': 11}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 107, 'mixed_non_doi_identifier': 11}, 'crossref': {'url_canonical_only': 25, 'mixed_non_doi_identifier': 11}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- openalex_title_per_page_by_subreason: `{'url_canonical_only': 5}`
- openalex_title_pick_best_accepted_subreasons: `['url_canonical_only']`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- post_openalex_suppressed_group_count: `82`
- post_openalex_suppressed_group_counts_by_provider: `{'crossref': 82}`
- post_openalex_suppressed_group_counts_by_title_subreason: `{'url_canonical_only': 82}`
- post_openalex_unsuppressed_targeted_group_count: `25`
- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{'openalex_title_unmatched': 25}`
- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{'url_canonical_only': 25}`
- title_lane_post_prelink_residual_group_count: `256`
- title_lane_post_prelink_residual_request_count: `174`

## Provider summary
- arxiv: events=3, total_latency_ms=3501, estimated_cost_usd=0.000000
- crossref: events=162, total_latency_ms=210265, estimated_cost_usd=0.000000
- europepmc: events=6, total_latency_ms=9956, estimated_cost_usd=0.000000
- none: events=487, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=244, total_latency_ms=267182, estimated_cost_usd=0.000000
- pubmed: events=6, total_latency_ms=7191, estimated_cost_usd=0.000000
