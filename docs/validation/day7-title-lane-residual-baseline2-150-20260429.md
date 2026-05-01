# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day7_title_lane_residual_baseline2_150_20260429.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `None`
- stages: `enrich`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `308`
- source_record_count: `308`
- matched_source_record_count: `251`
- merged_metadata_proposal_count: `0`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `640248`
- total_provider_latency_ms: `628756`
- cost_event_count: `308`
- batch_run_count: `1`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `220`
- processed_runnable_intents: `308` / `588`
- request_savings_vs_processed_intents: `88`
- request_savings_vs_total_planned_intents: `368`
- shared_title_reuse_group_count: `16`
- shared_title_reuse_request_savings: `16`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 8, 'openalex': 8}`
- title_lane_group_count: `158`
- title_lane_request_count: `158`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 144, 'cluster_leader_path': 14}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 144, 'cluster_leader_path': 14}`
- title_lane_group_counts_by_provider: `{'crossref': 79, 'openalex': 79}`
- title_lane_request_counts_by_provider: `{'crossref': 79, 'openalex': 79}`
- title_lane_group_counts_by_provider_reason: `{'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 72, 'cluster_leader_path': 7}, 'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 72, 'cluster_leader_path': 7}}`
- title_lane_request_counts_by_provider_reason: `{'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 72, 'cluster_leader_path': 7}, 'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 72, 'cluster_leader_path': 7}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 130, 'mixed_non_doi_identifier': 14}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 130, 'mixed_non_doi_identifier': 14}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'crossref': {'url_canonical_only': 65, 'mixed_non_doi_identifier': 7}, 'openalex': {'url_canonical_only': 65, 'mixed_non_doi_identifier': 7}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'crossref': {'url_canonical_only': 65, 'mixed_non_doi_identifier': 7}, 'openalex': {'url_canonical_only': 65, 'mixed_non_doi_identifier': 7}}`
- title_lane_cache_hit_group_count: `0`
- title_lane_post_prelink_residual_group_count: `158`
- title_lane_post_prelink_residual_request_count: `158`

## Provider summary
- arxiv: events=2, total_latency_ms=2395, estimated_cost_usd=0.000000
- crossref: events=150, total_latency_ms=379639, estimated_cost_usd=0.000000
- europepmc: events=3, total_latency_ms=5545, estimated_cost_usd=0.000000
- openalex: events=150, total_latency_ms=233941, estimated_cost_usd=0.000000
- pubmed: events=3, total_latency_ms=7236, estimated_cost_usd=0.000000
