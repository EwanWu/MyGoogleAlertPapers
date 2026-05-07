# Day13 large-fixed validation: truncated-title salvage rerun (2026-05-02)

## Objective
Validate the narrow truncated-title salvage patch on `large-fixed` after the earlier run was interrupted by session context overflow.

Comparison baseline:
- `data/benchmark/day13_large_fixed_url_identity_doi_20260502.db`

Rerun treatment:
- `data/benchmark/day13_large_fixed_urlid_truncated_title_salvage_rerun_20260502.db`
- report JSON: `docs/validation/day13-large-fixed-urlid-truncated-title-salvage-rerun-20260502.json`

## Interruption note
The first large-fixed attempt was **not** a project-code failure. Gateway logs showed:
- `2026-05-02T13:25:46Z` context overflow detected during tool loop
- `2026-05-02T13:27:21Z` auto-compaction succeeded

That first run left a partial DB without final report artifacts:
- `data/benchmark/day13_large_fixed_urlid_truncated_title_salvage_20260502.db`

This memo is based on the completed rerun.

## Patch summary
Files changed:
- `src/mygooglealertpapers/enrich/base.py`
- `tests/test_title_normalization.py`

Rule shape:
- keep normal title acceptance unchanged
- add a very narrow salvage path only when all are true:
  - title match is below normal threshold but `sim >= 0.84`
  - source title looks truncated (`. .`, `…`, or trailing `...`)
  - `first_author_matches(...) is True`
  - `venue_hint_matches(...) is True`
  - no year conflict

Targeted tests:
```bash
pytest -q tests/test_title_normalization.py
```
Passed.

## Headline result
### Durable routing / matching deltas
- `matched_source_record_count`: `543 -> 547` `(+4)`
- `dispatch_request_count`: `407 -> 403` `(-4)`
- `title_lane_request_count`: `253 -> 249` `(-4)`
- `post_openalex_suppressed_group_count`: `73 -> 77` `(+4)`
- `post_openalex_unsuppressed_targeted_group_count`: `48 -> 44` `(-4)`
- `merge_review_queue_count`: `2 -> 2` `(0)`
- `severe_doi_conflict_count`: `2 -> 2` `(0)`

### Output-layer deltas
- `merged_metadata_proposal_count`: `358 -> 359` `(+1)`
- `canonical_paper_count`: `283 -> 284` `(+1)`
- `normalized_only_fallback_proposal_count`: `29 -> 26` `(-3)`

## Candidate-level changes
The patch produced four clear OpenAlex rescues, each paired with suppression of the corresponding residual Crossref title request:

1. `cand_20f8d5e121253c15`
   - base: `openalex:title matched=0`, `crossref:title` unsuppressed
   - rerun: `openalex:title matched=1`, `crossref:title` suppressed
   - matched article DOI: `10.1016/j.nicl.2026.103990`

2. `cand_89794a7e8282a9b7`
   - base: `openalex:title matched=0`, `crossref:title` unsuppressed
   - rerun: `openalex:title matched=1`, `crossref:title` suppressed
   - matched article DOI: `10.4314/mmj.v37i5.13`

3. `cand_ba178f768ff6ab00`
   - base: `openalex:title matched=0`, `crossref:title` unsuppressed
   - rerun: `openalex:title matched=1`, `crossref:title` suppressed
   - matched article DOI: `10.1016/j.ekir.2026.106399`

4. `cand_ebc2f5c1d2ce68ca`
   - base: `openalex:title matched=0`, `crossref:title` unsuppressed
   - rerun: `openalex:title matched=1`, `crossref:title` suppressed
   - matched article DOI: `10.1016/j.jelectrocard.2026.154240`

These are the durable semantic wins from the patch.

## Important caution: one live-drift artifact
There was also one unrelated live-provider drift case:
- `cand_8994637b2b637b39`

Base run:
- no merge proposal
- Crossref unmatched article: `Familial Hypokalemic Periodic Paralysis with Permanent Myopathy`

Rerun:
- Crossref still unmatched, but returned a different article
- a new low-confidence `normalized_only` proposal appeared:
  - title: `Permanent weakness and myopathy in hypokalemic periodic paralysis`
  - venue: `Acta Myologica`

Interpretation:
- the observed `canonical_paper_count +1` is **not clean evidence of the truncated-title salvage rule itself**
- it appears to come from live provider response drift, not from the four deterministic truncation rescues above

So the stable conclusion should be based on:
- `matched_source_record +4`
- `dispatch_request_count -4`
- `title_lane_request_count -4`
- no review/conflict regression

not on `canonical_paper_count +1` alone.

## Runtime interpretation
This rerun did **not** show a wall-time speedup:
- `total_batch_duration_ms`: `665839 -> 724093`
- `total_provider_latency_ms`: `654373 -> 712795`

Provider latencies moved the wrong way despite fewer requests:
- Crossref latency: `325586 -> 356006`
- OpenAlex latency: `297769 -> 322562`

Interpretation:
- request volume improved in the expected direction
- but live network / provider variability dominated the realized wall time on this single rerun
- therefore this run supports a **routing-efficiency / semantic-correctness** claim, not a robust runtime-speed claim

## Conclusion
Keep the truncated-title salvage patch.

Why:
- it stays narrow
- it converts four previously unmatched OpenAlex truncated-title cases into accepted matches on `large-fixed`
- it suppresses four residual Crossref title requests
- it does not enlarge review queue or DOI-conflict counts

What not to claim:
- do **not** claim a stable wall-time improvement from this rerun
- do **not** treat the `canonical +1` headline as fully durable patch evidence, because one extra canonical record appears to be live provider drift (`cand_8994637b2b637b39`)

Best durable summary:
> The truncated-title salvage patch is worth retaining as a narrow precision-preserving acceptance improvement. On `large-fixed`, it cleanly rescued four OpenAlex truncated-title cases and reduced the residual Crossref title workload by four, without increasing review/conflict risk. Runtime remained noisy in live conditions, so promotion should be justified by semantic/routing gains rather than by this rerun's wall-time.
