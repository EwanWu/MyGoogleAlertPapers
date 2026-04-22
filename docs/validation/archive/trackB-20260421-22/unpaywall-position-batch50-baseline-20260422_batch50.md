# Replay validation report: conditional_sources_v2

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_unpaywall_position_seed_20260422_batch50.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_unpaywall_position_baseline_v2_20260422_batch50.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2.yaml`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `188`
- replay_candidate_count: `188`
- normalized_candidate_count: `188`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `720`
- source_record_count: `720`
- matched_source_record_count: `416`
- merged_metadata_proposal_count: `188`
- normalized_only_fallback_proposal_count: `18`
- canonical_paper_count: `165`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `989318`
- total_provider_latency_ms: `983056`
- cost_event_count: `1096`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- arxiv: events=2, total_latency_ms=2806, estimated_cost_usd=0.000000
- crossref: events=188, total_latency_ms=373498, estimated_cost_usd=0.000000
- europepmc: events=77, total_latency_ms=124326, estimated_cost_usd=0.000000
- none: events=376, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=188, total_latency_ms=173804, estimated_cost_usd=0.000000
- pubmed: events=77, total_latency_ms=157990, estimated_cost_usd=0.000000
- semanticscholar: events=188, total_latency_ms=150632, estimated_cost_usd=0.000000
