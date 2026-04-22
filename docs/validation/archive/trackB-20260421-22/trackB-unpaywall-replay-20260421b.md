# Replay validation report: conditional_sources_v2_unpaywall

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_trackB_treat_20260421b.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_unpaywall.yaml`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `368`
- replay_candidate_count: `368`
- normalized_candidate_count: `368`
- dirty_doi_source_count: `0`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `1566`
- source_record_count: `1566`
- matched_source_record_count: `724`
- merged_metadata_proposal_count: `368`
- normalized_only_fallback_proposal_count: `45`
- canonical_paper_count: `290`
- merge_review_queue_count: `7`
- severe_doi_conflict_count: `7`

## Runtime and accounting
- total_batch_duration_ms: `2538035`
- total_provider_latency_ms: `2522665`
- cost_event_count: `2366`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- arxiv: events=9, total_latency_ms=46435, estimated_cost_usd=0.000000
- crossref: events=368, total_latency_ms=798285, estimated_cost_usd=0.000000
- europepmc: events=146, total_latency_ms=285002, estimated_cost_usd=0.000000
- none: events=736, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=432, total_latency_ms=307220, estimated_cost_usd=0.000000
- pubmed: events=146, total_latency_ms=399057, estimated_cost_usd=0.000000
- semanticscholar: events=368, total_latency_ms=455033, estimated_cost_usd=0.000000
- unpaywall: events=161, total_latency_ms=231633, estimated_cost_usd=0.000000
