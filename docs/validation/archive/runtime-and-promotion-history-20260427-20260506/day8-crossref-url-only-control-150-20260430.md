# Replay validation report: openalex_batching_identifier_plus_title_core_same_batch_cluster

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_crossref_url_only_control_150_20260430.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- http_fixture_record: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_crossref_url_only_control_150_20260430.jsonl`
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
- provider_intent_count: `755`
- source_record_count: `755`
- matched_source_record_count: `608`
- merged_metadata_proposal_count: `367`
- normalized_only_fallback_proposal_count: `38`
- canonical_paper_count: `292`
- merge_review_queue_count: `1`
- severe_doi_conflict_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `938226`
- total_provider_latency_ms: `928175`
- cost_event_count: `1490`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `487`
- processed_runnable_intents: `755` / `755`
- pre_experimental_runnable_provider_intents: `1405`
- experimental_skipped_provider_intents: `650`
- request_savings_vs_processed_intents: `268`
- request_savings_vs_total_planned_intents: `268`
- shared_title_reuse_group_count: `62`
- shared_title_reuse_request_savings: `74`
- shared_title_reuse_request_savings_by_provider: `{'crossref': 37, 'openalex': 37}`
- title_lane_group_count: `340`
- title_lane_request_count: `340`
- title_lane_group_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 280, 'cluster_leader_path': 60}`
- title_lane_request_counts_by_reason: `{'identifier_present_but_not_sufficient_for_provider_path': 280, 'cluster_leader_path': 60}`
- title_lane_group_counts_by_provider: `{'crossref': 170, 'openalex': 170}`
- title_lane_request_counts_by_provider: `{'crossref': 170, 'openalex': 170}`
- title_lane_group_counts_by_provider_reason: `{'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}}`
- title_lane_request_counts_by_provider_reason: `{'crossref': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}, 'openalex': {'identifier_present_but_not_sufficient_for_provider_path': 140, 'cluster_leader_path': 30}}`
- title_lane_identifier_gap_group_counts_by_subreason: `{'url_canonical_only': 252, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_request_counts_by_subreason: `{'url_canonical_only': 252, 'mixed_non_doi_identifier': 28}`
- title_lane_identifier_gap_group_counts_by_provider_subreason: `{'crossref': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}}`
- title_lane_identifier_gap_request_counts_by_provider_subreason: `{'crossref': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}, 'openalex': {'url_canonical_only': 126, 'mixed_non_doi_identifier': 14}}`
- title_lane_cache_hit_group_count: `0`
- experimental_title_skip_subreasons_by_provider: `None`
- experimental_skipped_group_count: `0`
- experimental_skipped_group_counts_by_provider: `{}`
- experimental_skipped_group_counts_by_title_subreason: `{}`
- title_lane_post_prelink_residual_group_count: `340`
- title_lane_post_prelink_residual_request_count: `340`

## Provider summary
- arxiv: events=9, total_latency_ms=12422, estimated_cost_usd=0.000000
- crossref: events=368, total_latency_ms=610951, estimated_cost_usd=0.000000
- europepmc: events=5, total_latency_ms=8754, estimated_cost_usd=0.000000
- none: events=735, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=291786, estimated_cost_usd=0.000000
- pubmed: events=5, total_latency_ms=4262, estimated_cost_usd=0.000000
