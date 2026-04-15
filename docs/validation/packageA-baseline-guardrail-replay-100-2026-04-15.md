# Replay validation report: baseline_guardrail

## Run context
- source_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100.db`
- output_db: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkg3_guardrail_100_replay_baseline_guardrail_20260415.db`
- policy_profile: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/baseline_guardrail.yaml`
- stages: `normalize, enrich, merge, dedup`

## Candidate and normalization summary
- source_candidate_count: `249`
- replay_candidate_count: `249`
- normalized_candidate_count: `249`
- dirty_doi_source_count: `9`
- dirty_doi_output_count: `0`
- dirty_doi_repaired_count: `9`

## Replay output summary
- provider_intent_count: `951`
- source_record_count: `951`
- matched_source_record_count: `503`
- merged_metadata_proposal_count: `219`
- normalized_only_fallback_proposal_count: `0`
- canonical_paper_count: `176`
- merge_review_queue_count: `2`
- severe_doi_conflict_count: `2`

## Runtime and accounting
- total_batch_duration_ms: `1550315`
- total_provider_latency_ms: `1538256`
- cost_event_count: `1668`
- batch_run_count: `4`
- paid_llm_usage_present: `False`
- paid_llm_note: `No paid LLM call path was exercised in this replay run.`

## Provider summary
- arxiv: events=8, total_latency_ms=17764, estimated_cost_usd=0.000000
- crossref: events=249, total_latency_ms=492248, estimated_cost_usd=0.000000
- europepmc: events=98, total_latency_ms=196993, estimated_cost_usd=0.000000
- none: events=717, total_latency_ms=0, estimated_cost_usd=0.000000
- openalex: events=249, total_latency_ms=326970, estimated_cost_usd=0.000000
- pubmed: events=98, total_latency_ms=241926, estimated_cost_usd=0.000000
- semanticscholar: events=249, total_latency_ms=262355, estimated_cost_usd=0.000000
