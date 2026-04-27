# Replay validation failure: conditional_sources_v2_author_blob_fallback_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/ab_baseline_smoke12_repeat_20260427.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- stages: `enrich, merge, dedup`

## Failure
- status: `failed`
- failed_stage: `enrich`
- error_message: `stage timed out after 179s: python3 -m mygooglealertpapers.cli enrich-candidates --limit 12`

## Partial counts at failure
- replay_candidate_count: `368`
- provider_intent_count: `25`
- source_record_count: `25`
- matched_source_record_count: `14`
- merged_metadata_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- cost_event_count: `25`
- batch_run_count: `1`

## Runtime and accounting
- total_batch_duration_ms: `0`
- total_provider_latency_ms: `100113`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`
- dispatch_request_count: `n/a`
- request_savings_vs_runnable_intents: `n/a`

## Provider summary
- crossref: events=6, total_latency_ms=10788, estimated_cost_usd=0.000000
- europepmc: events=4, total_latency_ms=6189, estimated_cost_usd=0.000000
- openalex: events=6, total_latency_ms=6555, estimated_cost_usd=0.000000
- pubmed: events=4, total_latency_ms=48733, estimated_cost_usd=0.000000
- semanticscholar: events=5, total_latency_ms=27848, estimated_cost_usd=0.000000
