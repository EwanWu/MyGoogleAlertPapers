# Replay validation report: openalex_batching_identifier_plus_title_core

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day5_identifier_plus_title_core_120_20260429.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core.yaml`
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
- provider_intent_count: `246`
- source_record_count: `246`
- matched_source_record_count: `194`
- merged_metadata_proposal_count: `0`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `455179`
- total_provider_latency_ms: `451544`
- cost_event_count: `246`
- batch_run_count: `1`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `178`
- processed_runnable_intents: `246` / `474`
- request_savings_vs_processed_intents: `68`
- request_savings_vs_total_planned_intents: `296`
- shared_title_reuse_group_count: `14`
- shared_title_reuse_request_savings: `14`

## Provider summary
- arxiv: events=2, total_latency_ms=2178, estimated_cost_usd=0.000000
- crossref: events=120, total_latency_ms=323311, estimated_cost_usd=0.000000
- europepmc: events=2, total_latency_ms=3307, estimated_cost_usd=0.000000
- openalex: events=120, total_latency_ms=120390, estimated_cost_usd=0.000000
- pubmed: events=2, total_latency_ms=2358, estimated_cost_usd=0.000000
