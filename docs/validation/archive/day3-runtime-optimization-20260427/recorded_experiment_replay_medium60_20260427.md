# Replay validation report: title_payload_reuse_experiment_profile_20260427

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/recorded_experiment_replay_medium60_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/title_payload_reuse_experiment_profile_20260427.yaml`
- http_fixture_record: `None`
- http_fixture_replay: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_medium60_20260427.jsonl`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `248`
- source_record_count: `248`
- matched_source_record_count: `137`
- merged_metadata_proposal_count: `60`
- normalized_only_fallback_proposal_count: `7`
- canonical_paper_count: `51`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `153606`
- total_provider_latency_ms: `668982`
- cost_event_count: `368`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `201`
- request_savings_vs_runnable_intents: `47`
- shared_title_reuse_group_count: `12`
- shared_title_reuse_request_savings: `12`

## Provider summary
- crossref: events=60, total_latency_ms=142433, estimated_cost_usd=0.000000
- europepmc: events=34, total_latency_ms=67994, estimated_cost_usd=0.000000
- none: events=120, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=60, total_latency_ms=78443, estimated_cost_usd=0.000000
- pubmed: events=34, total_latency_ms=85223, estimated_cost_usd=0.000000
- semanticscholar: events=60, total_latency_ms=294889, estimated_cost_usd=0.000000
