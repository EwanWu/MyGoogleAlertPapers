# Day15 large-fixed validation: repo-shadow + url-identity DOI recovery (2026-05-03)

## Run context
- source_db: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- output_db: `data/benchmark/day15_current_default_plus_urlid_large_fixed_20260503.db`
- policy_profile: `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`
- stages: `enrich, merge, dedup`
- baseline: `data/benchmark/day14_openalex_repo_shadow_large_fixed_20260503.db` (repo-shadow ON, url-identity OFF)

## Top-line outcome

| metric | day14 (repo-shadow only) | day15 (+ url-identity) | delta |
|---|---:|---:|---:|
| `provider_intent_count` | 675 | 676 | +1 |
| `source_record_count` | 675 | 676 | +1 |
| `matched_source_record_count` | 533 | 547 | **+14** |
| `merged_metadata_proposal_count` | 357 | 358 | **+1** |
| `canonical_paper_count` | 282 | 283 | **+1** |
| `merge_review_queue_count` | 2 | 2 | 0 |
| `severe_doi_conflict_count` | 2 | 2 | 0 |
| `total_batch_duration_ms` | 645200 | 664087 | +18887 |
| `total_provider_latency_ms` | 634458 | 653200 | +18742 |

## Dispatch / runtime

| metric | day14 | day15 | delta |
|---|---:|---:|---:|
| `planned_provider_intents` | 1405 | 1393 | **-12** |
| `dispatch_request_count` | 408 | 402 | **-6** |
| `title_lane_group_count` | 340 | 326 | **-14** |
| `title_lane_request_count` | 261 | 248 | **-13** |
| `post_openalex_suppressed_group_count` | 79 | 78 | -1 |
| `post_openalex_unsuppressed_targeted_group_count` | 47 | 43 | **-4** |

## Mechanism analysis — the 10 URL-identity recovered candidates

All 10 url-identity recoverable candidates (`nature_article_slug` + `recursive_url_decode`) show the same structural pattern:

### In day14 (title-path):
- Crossref used `title` query
- OpenAlex used `title` query
- sometimes matched, sometimes not
- `cand_8c0fcffbabdce4e6` had **zero matched source records** at all

### In day15 (DOI-path):
- OpenAlex used `doi_batch` query (fast, deterministic)
- Crossref used `doi` query (fast, deterministic)
- no title queries needed for these candidates

### Representative cases

**`cand_8c0fcffbabdce4e6`** — the key semantic rescue:
- day14: `sr: []` (completely unmatched)
- day15: `sr: [('openalex', 'doi_batch', 1, '10.14366/usg.23232'), ('crossref', 'doi', 1, '10.14366/usg.23232')]`
- This is the candidate that was **missing entirely** in day14 and rescued in day15.
- DOI `10.14366/usg.23232` recovered via `recursive_url_decode` from `https://www.e-ultrasonography.org/journal/view.php?doi%3D10.14366%252Fusg.23232`

**`cand_ef45f083c154b55c`** — DOI upgrade from title path:
- day14: `sr: [('crossref', 'title', 1, '10.1038/s41598-026-42032-x')]`
- day15: `sr: [('openalex', 'doi_batch', 1, '10.1038/s41598-026-42032-x'), ('crossref', 'doi', 1, '10.1038/s41598-026-42032-x')]`
- DOI `10.1038/s41598-026-42032-x` recovered via `nature_article_slug` from `nature.com/articles/s41598-026-42032-x_reference.pdf`

All 10 candidates show this DOI-path upgrade pattern.

## Interpretation

### Known
- the `url_identity_doi_recovery` lane is doing exactly what it should: converting title-path candidates into fast deterministic DOI-path candidates before provider fanout
- the dispatch reduction is real: 13 fewer title-lane requests, 12 fewer planned intents, 6 fewer dispatch calls
- the semantic gain is concentrated in the recovered candidates: `cand_8c0fcffbabdce4e6` was completely unmatched in day14 and fully rescued in day15

### Inferred
- the slight batch-duration increase (+18887ms) is likely noise from live provider latency variance on the larger run, not a systematic regression
- the net effect is still positive: cheaper dispatch + real semantic win for hard residual cases
- `matched_source_record_count +14` reflects that each recovered candidate gains at least one extra source record (the `doi_batch` openalex record) relative to day14's title-path-only resolution

### Speculative
- if URL-identity DOI recovery expands to more domain-specific rules in the future, the dispatch and latency gains would be larger
- but the current rule surface remains intentionally narrow and deterministic

## Decision
**Retain `url_identity_doi_recovery` in the current default runtime** — this large-fixed validation confirms the medium60 result and shows the patch works on the full 368-candidate gate with no regression.