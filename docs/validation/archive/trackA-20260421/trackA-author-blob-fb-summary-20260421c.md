# Track A author_blob_fallback_only replay summary

## Run tag
20260421c

## Profiles
- control: `conditional_sources_v2`
- treatment: `conditional_sources_v2_author_blob_fallback_only`

## Key metrics

| Metric | v2 (control) | author_blob_fb (treatment) | delta |
|---|---|---|---|
| matched_source_record_count | 781 | 750 | -31 |
| merged_metadata_proposal_count | 368 | 367 | -1 |
| normalized_only_fallback_proposal_count | 35 | 35 | 0 |
| canonical_paper_count | 292 | 292 | 0 |
| merge_review_queue_count | 4 | 3 | -1 |
| severe_doi_conflict_count | 4 | 3 | -1 |

## Interpretation guide

- canonical_paper_count: primary correctness metric, negative delta means treatment lost canonical papers
- matched_source_record_count: provider match stability, but only comparable under reused source-record design
- normalized_only_fallback_proposal_count: fallback usage change
- merge_review_queue_count: human review burden, should stay flat or decrease
- severe_doi_conflict_count: conflict burden, should stay flat or decrease

## Full raw results

### v2 (control)
```json
{
  "status": "ok",
  "failed_stage": null,
  "error_message": null,
  "source_db": "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db",
  "output_db": "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_trackA_author_blob_fb_v2_20260421c.db",
  "policy_profile": "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2.yaml",
  "policy_profile_name": "conditional_sources_v2",
  "stages": [
    "enrich",
    "merge",
    "dedup"
  ],
  "source_candidate_count": 368,
  "replay_candidate_count": 368,
  "normalized_candidate_count": 368,
  "dirty_doi_source_count": 0,
  "dirty_doi_output_count": 0,
  "dirty_doi_repaired_count": 0,
  "provider_intent_count": 1405,
  "source_record_count": 1405,
  "matched_source_record_count": 781,
  "merged_metadata_proposal_count": 368,
  "normalized_only_fallback_proposal_count": 35,
  "canonical_paper_count": 292,
  "merge_review_queue_count": 4,
  "cost_event_count": 2141,
  "batch_run_count": 3,
  "severe_doi_conflict_count": 4,
  "total_batch_duration_ms": 2214794,
  "total_provider_latency_ms": 2197341,
  "provider_summary": [
    {
      "provider": "arxiv",
      "events": 9,
      "total_latency_ms": 18928,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "crossref",
      "events": 368,
      "total_latency_ms": 781668,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "europepmc",
      "events": 146,
      "total_latency_ms": 274387,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "none",
      "events": 736,
      "total_latency_ms": 0,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "openalex",
      "events": 368,
      "total_latency_ms": 379960,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "pubmed",
      "events": 146,
      "total_latency_ms": 364224,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "semanticscholar",
      "events": 368,
      "total_latency_ms": 378174,
      "estimated_cost_usd": 0.0
    }
  ],
  "paid_llm_usage": {
    "present": false,
    "note": "No paid LLM call path was exercised in this replay run."
  }
}
```

### Treatment
```json
{
  "status": "ok",
  "failed_stage": null,
  "error_message": null,
  "source_db": "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db",
  "output_db": "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_trackA_author_blob_fb_treat_20260421c.db",
  "policy_profile": "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml",
  "policy_profile_name": "conditional_sources_v2_author_blob_fallback_only",
  "stages": [
    "enrich",
    "merge",
    "dedup"
  ],
  "source_candidate_count": 368,
  "replay_candidate_count": 368,
  "normalized_candidate_count": 368,
  "dirty_doi_source_count": 0,
  "dirty_doi_output_count": 0,
  "dirty_doi_repaired_count": 0,
  "provider_intent_count": 1405,
  "source_record_count": 1405,
  "matched_source_record_count": 750,
  "merged_metadata_proposal_count": 367,
  "normalized_only_fallback_proposal_count": 35,
  "canonical_paper_count": 292,
  "merge_review_queue_count": 3,
  "cost_event_count": 2140,
  "batch_run_count": 3,
  "severe_doi_conflict_count": 3,
  "total_batch_duration_ms": 2449924,
  "total_provider_latency_ms": 2437167,
  "provider_summary": [
    {
      "provider": "arxiv",
      "events": 9,
      "total_latency_ms": 23938,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "crossref",
      "events": 368,
      "total_latency_ms": 793026,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "europepmc",
      "events": 146,
      "total_latency_ms": 454182,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "none",
      "events": 735,
      "total_latency_ms": 0,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "openalex",
      "events": 368,
      "total_latency_ms": 413222,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "pubmed",
      "events": 146,
      "total_latency_ms": 394876,
      "estimated_cost_usd": 0.0
    },
    {
      "provider": "semanticscholar",
      "events": 368,
      "total_latency_ms": 357923,
      "estimated_cost_usd": 0.0
    }
  ],
  "paid_llm_usage": {
    "present": false,
    "note": "No paid LLM call path was exercised in this replay run."
  }
}
```
