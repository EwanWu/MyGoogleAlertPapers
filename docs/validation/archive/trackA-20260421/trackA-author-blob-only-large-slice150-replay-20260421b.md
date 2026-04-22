# Replay validation report: conditional_sources_v2_author_blob_only

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_trackA_author_blob_only_large_slice150_replay_author_blob_only_20260421b.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_only.yaml`
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
- matched_source_record_count: `763`
- merged_metadata_proposal_count: `367`
- normalized_only_fallback_proposal_count: `33`
- canonical_paper_count: `291`
- merge_review_queue_count: `4`
- severe_doi_conflict_count: `4`

## Runtime and accounting
- total_batch_duration_ms: `2008641`
- total_provider_latency_ms: `1997842`
- cost_event_count: `2140`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- arxiv: events=9, total_latency_ms=10030, estimated_cost_usd=0.000000
- crossref: events=368, total_latency_ms=730881, estimated_cost_usd=0.000000
- europepmc: events=146, total_latency_ms=237497, estimated_cost_usd=0.000000
- none: events=735, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=368, total_latency_ms=340770, estimated_cost_usd=0.000000
- pubmed: events=146, total_latency_ms=354267, estimated_cost_usd=0.000000
- semanticscholar: events=368, total_latency_ms=324397, estimated_cost_usd=0.000000
