# Replay validation report: conditional_sources_v2

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_replay_v2_smoke60_20260416.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2.yaml`
- stages: `enrich`

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
- matched_source_record_count: `133`
- merged_metadata_proposal_count: `0`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `0`
- merge_review_queue_count: `0`
- severe_doi_conflict_count: `0`

## Runtime and accounting
- total_batch_duration_ms: `364025`
- total_provider_latency_ms: `360497`
- cost_event_count: `248`
- batch_run_count: `1`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- crossref: events=60, total_latency_ms=95326, estimated_cost_usd=0.000000
- europepmc: events=34, total_latency_ms=62717, estimated_cost_usd=0.000000
- openalex: events=60, total_latency_ms=79487, estimated_cost_usd=0.000000
- pubmed: events=34, total_latency_ms=72176, estimated_cost_usd=0.000000
- semanticscholar: events=60, total_latency_ms=50791, estimated_cost_usd=0.000000
