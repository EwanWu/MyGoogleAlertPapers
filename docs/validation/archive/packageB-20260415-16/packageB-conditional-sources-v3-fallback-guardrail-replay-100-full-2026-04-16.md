# Replay validation report: conditional_sources_v3_fallback_guardrail

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_full_20260416.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v3_fallback_guardrail.yaml`
- stages: `enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `249`
- replay_candidate_count: `249`
- normalized_candidate_count: `249`
- dirty_doi_source_count: `9`
- dirty_doi_output_count: `9`
- dirty_doi_repaired_count: `0`

## Replay output summary
- provider_intent_count: `951`
- source_record_count: `951`
- matched_source_record_count: `512`
- merged_metadata_proposal_count: `248`
- normalized_only_fallback_proposal_count: `36`
- canonical_paper_count: `195`
- merge_review_queue_count: `10`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `1141992`
- total_provider_latency_ms: `1135337`
- cost_event_count: `1448`
- batch_run_count: `3`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- arxiv: events=8, total_latency_ms=25249, estimated_cost_usd=0.000000
- crossref: events=249, total_latency_ms=305134, estimated_cost_usd=0.000000
- europepmc: events=98, total_latency_ms=188334, estimated_cost_usd=0.000000
- none: events=497, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=249, total_latency_ms=240674, estimated_cost_usd=0.000000
- pubmed: events=98, total_latency_ms=201051, estimated_cost_usd=0.000000
- semanticscholar: events=249, total_latency_ms=174895, estimated_cost_usd=0.000000
