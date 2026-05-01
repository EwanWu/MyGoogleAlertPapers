# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster_skip_crossref_url_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_crossref_url_only_treatment_150_20260430.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_skip_crossref_url_only.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_crossref_url_only_control_150_20260430.jsonl`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `628`
- source_record_count: `628`
- matched_source_record_count: `503`
- merged_metadata_proposal_count: `367`
- normalized_only_fallback_proposal_count: `68`
- canonical_paper_count: `293`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `20142`
- total_provider_latency_ms: `578656`
- cost_event_count: `1363`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `361`
- processed_runnable_intents: `628` / `628`
- pre_experimental_runnable_provider_intents: `1405`
- experimental_skipped_provider_intents: `777`
- request_savings_vs_processed_intents: `267`
- request_savings_vs_total_planned_intents: `267`
- shared_title_reuse_group_count: `61`
- shared_title_reuse_request_savings: `73`
- shared_title_reuse_request_savings_by_provider: `{'openalex': 37, 'crossref': 36}`
- title_lane_group_count: `214`
- title_lane_request_count: `214`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 154, 'cluster_leader_path': 60}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 154, 'cluster_leader_path': 60}`
- title_lane_group_counts_by_provider: `{'openalex': 170, 'crossref': 44}`
- title_lane_request_counts_by_provider: `{'openalex': 170, 'crossref': 44}`
- title_lane_group_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 14, 'cluster_leader_path': 30}}`
- title_lane_request_counts_by_provider_reason: `{'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 14, 'cluster_leader_path': 30}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 126, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 126, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'crossref': {'mixed_non_doi_identifier': 14}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'crossref': {'mixed_non_doi_identifier': 14}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `{'crossref': ['url_canonical_only']}`
- experimental_skipped_group_count: `126`
- experimental_skipped_group_counts_by_provider: `{'crossref': 126}`
- experimental_skipped_group_counts_by_title_subreason: `{'url_canonical_only': 126}`
- title_lane_post_prelink_residual_group_count: `214`
- title_lane_post_prelink_residual_request_count: `214`

## Provider summary
- arxiv: events=9, total_latency_ms=8635, estimated_cost_usd=0.000000
- crossref: events=241, total_latency_ms=268082, estimated_cost_usd=0.000000
- europepmc: events=5, total_latency_ms=6048, estimated_cost_usd=0.000000
- none: events=735, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=291786, estimated_cost_usd=0.000000
- pubmed: events=5, total_latency_ms=4105, estimated_cost_usd=0.000000
