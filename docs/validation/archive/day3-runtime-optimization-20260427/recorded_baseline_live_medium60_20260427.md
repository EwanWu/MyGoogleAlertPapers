# Replay validation report: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/recorded_baseline_live_medium60_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- http_fixture_record: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_medium60_20260427.jsonl`
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
- provider_intent_count: `248`
- source_record_count: `248`
- matched_source_record_count: `137`
- merged_metadata_proposal_count: `60`
- normalized_only_fallback_proposal_count: `7`
- canonical_paper_count: `51`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `675687`
- total_provider_latency_ms: `673055`
- cost_event_count: `368`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `201`
- request_savings_vs_runnable_intents: `47`
- shared_title_reuse_group_count: `0`
- shared_title_reuse_request_savings: `0`

## Provider summary
- crossref: events=60, total_latency_ms=142433, estimated_cost_usd=0.000000
- europepmc: events=34, total_latency_ms=69323, estimated_cost_usd=0.000000
- none: events=120, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=60, total_latency_ms=78443, estimated_cost_usd=0.000000
- pubmed: events=34, total_latency_ms=87967, estimated_cost_usd=0.000000
- semanticscholar: events=60, total_latency_ms=294889, estimated_cost_usd=0.000000
