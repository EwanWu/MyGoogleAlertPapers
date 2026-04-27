# Replay validation report: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/recorded_baseline_live_medium40_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- http_fixture_record: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_medium40_20260427.jsonl`
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
- provider_intent_count: `160`
- source_record_count: `160`
- matched_source_record_count: `100`
- merged_metadata_proposal_count: `40`
- normalized_only_fallback_proposal_count: `4`
- canonical_paper_count: `33`
- merge_review_queue_count: `1`
- severe_doi_conflict_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `453015`
- total_provider_latency_ms: `450450`
- cost_event_count: `240`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `127`
- request_savings_vs_runnable_intents: `33`
- shared_title_reuse_group_count: `0`
- shared_title_reuse_request_savings: `0`

## Provider summary
- crossref: events=40, total_latency_ms=69153, estimated_cost_usd=0.000000
- europepmc: events=20, total_latency_ms=44691, estimated_cost_usd=0.000000
- none: events=80, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=40, total_latency_ms=56608, estimated_cost_usd=0.000000
- pubmed: events=20, total_latency_ms=84845, estimated_cost_usd=0.000000
- semanticscholar: events=40, total_latency_ms=195153, estimated_cost_usd=0.000000
