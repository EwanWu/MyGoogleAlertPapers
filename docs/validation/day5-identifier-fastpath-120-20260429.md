# Replay validation report: openalex_batching_identifier_fastpath

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day5_identifier_fastpath_120_20260429.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_fastpath.yaml`
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
- provider_intent_count: `100`
- source_record_count: `100`
- matched_source_record_count: `94`
- merged_metadata_proposal_count: `0`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `69752`
- total_provider_latency_ms: `66503`
- cost_event_count: `100`
- batch_run_count: `1`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `46`
- processed_runnable_intents: `100` / `474`
- request_savings_vs_processed_intents: `54`
- request_savings_vs_total_planned_intents: `428`
- shared_title_reuse_group_count: `0`
- shared_title_reuse_request_savings: `0`

## Provider summary
- arxiv: events=2, total_latency_ms=3681, estimated_cost_usd=0.000000
- crossref: events=47, total_latency_ms=54708, estimated_cost_usd=0.000000
- europepmc: events=2, total_latency_ms=4536, estimated_cost_usd=0.000000
- openalex: events=47, total_latency_ms=0, estimated_cost_usd=0.000000
- pubmed: events=2, total_latency_ms=3578, estimated_cost_usd=0.000000
