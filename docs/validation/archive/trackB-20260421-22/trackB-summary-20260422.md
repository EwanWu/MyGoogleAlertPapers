# Track B Unpaywall re-run summary (20260422)

## Design
- Control: v2 source_records + merge+dedup only (no new enrich)
- Treatment: v2 source_records + Unpaywall enrich + merge+dedup
- Fix applied: best_oa_url now reads from best_oa_location.url (not top-level)

## Profiles
- control: `conditional_sources_v2`
- treatment: `conditional_sources_v2_unpaywall`

## Key metrics

| Metric | Control (v2) | Treatment (+Unpaywall) | Delta |
|---|---|---|---|
| canonical_paper_count | 292 | 292 | **0** |
| merge_review_queue_count | 4 | 4 | **0** |
| normalized_only_fallback | 35 | 35 | 0 |
| matched_source_record | 781 | 781 | 0 |

## Unpaywall OA URL coverage

- Unpaywall total records: 0
- Unpaywall matched: 0
- OA URL filled (url IS NOT NULL): **0**
- Fill rate: None

## Interpretation

- canonical_paper_count: primary correctness metric — should be flat
- merge_review_queue_count: should not increase
- OA URL fill rate: primary value metric — should be > 0 after bug fix

## Bug fix verification

If oa_url_count > 0, the url field bug is confirmed fixed.
If oa_url_count == 0 with up_matched > 0, the fix is not working.
