# Replay validation report: conditional_sources_v2

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_replay_v2_20260416_slice150.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2.yaml`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `1405`
- source_record_count: `1405`
- matched_source_record_count: `777`
- merged_metadata_proposal_count: `368`
- normalized_only_fallback_proposal_count: `36`
- canonical_paper_count: `293`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `1953366`
- total_provider_latency_ms: `1940163`
- cost_event_count: `2141`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- arxiv: events=9, total_latency_ms=55043, estimated_cost_usd=0.000000
- crossref: events=368, total_latency_ms=578028, estimated_cost_usd=0.000000
- europepmc: events=146, total_latency_ms=259525, estimated_cost_usd=0.000000
- none: events=736, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=413587, estimated_cost_usd=0.000000
- pubmed: events=146, total_latency_ms=319527, estimated_cost_usd=0.000000
- semanticscholar: events=368, total_latency_ms=314453, estimated_cost_usd=0.000000
