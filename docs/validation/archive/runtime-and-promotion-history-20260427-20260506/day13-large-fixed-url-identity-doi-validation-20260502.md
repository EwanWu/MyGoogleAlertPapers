# Day13 large-fixed validation: deterministic URL-identity DOI recovery (2026-05-02)

## Objective
Validate whether the narrow patch

- `src/mygooglealertpapers/normalize/identifiers.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml`

still helps on `large-fixed` (`data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`, 368 candidates), not just on `small-fixed`.

The patch scope stays narrow:
- only `non-arXiv + url_canonical_only`
- only deterministic DOI recovery from `url_canonical`
- current rules:
  - `nature_article_slug`
  - `recursive_url_decode`

## Runs
### Base
```bash
PYTHONPATH=src python3 scripts/replay_validation.py \
  --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db \
  --output-db data/benchmark/day13_large_fixed_current_default_20260502.db \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml \
  --report-out docs/validation/day13-large-fixed-current-default-20260502.json \
  --limit 1000000 \
  --stages enrich merge dedup
```

### Treatment
```bash
PYTHONPATH=src python3 scripts/replay_validation.py \
  --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db \
  --output-db data/benchmark/day13_large_fixed_url_identity_doi_20260502.db \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml \
  --report-out docs/validation/day13-large-fixed-url-identity-doi-20260502.json \
  --limit 1000000 \
  --stages enrich merge dedup
```

## Recoverable candidates on this slice
`recover_doi_from_url_identity(url_canonical)` found `10` deterministic recoverable candidates:

- `cand_210c27dfc78ab052` → `nature_article_slug` → `10.1038/s41598-026-43624-3`
- `cand_6712f73abd8e5a01` → `nature_article_slug` → `10.1038/s41598-026-43624-3`
- `cand_671ed1ecf3aa215c` → `nature_article_slug` → `10.1038/s43856-026-01413-z`
- `cand_721f728d8e406dd5` → `nature_article_slug` → `10.1038/s44161-026-00785-8`
- `cand_8c0fcffbabdce4e6` → `recursive_url_decode` → `10.14366/usg.23232`
- `cand_983e32088eed4586` → `nature_article_slug` → `10.1038/s41598-026-38473-z`
- `cand_99e05fb4078181d5` → `nature_article_slug` → `10.1038/s43856-026-01413-z`
- `cand_aafaa7c0485410af` → `nature_article_slug` → `10.1038/s44303-026-00156-9`
- `cand_caed51f7383710a2` → `nature_article_slug` → `10.1038/s41598-026-43624-3`
- `cand_ef45f083c154b55c` → `nature_article_slug` → `10.1038/s41598-026-42032-x`

## Result summary
### Top-line outcome
| metric | base | treatment | delta |
|---|---:|---:|---:|
| `provider_intent_count` | 680 | 681 | +1 |
| `source_record_count` | 680 | 681 | +1 |
| `matched_source_record_count` | 537 | 543 | +6 |
| `merged_metadata_proposal_count` | 357 | 358 | +1 |
| `normalized_only_fallback_proposal_count` | 29 | 29 | 0 |
| `canonical_paper_count` | 282 | 283 | +1 |
| `merge_review_queue_count` | 2 | 2 | 0 |
| `cost_event_count` | 1405 | 1407 | +2 |
| `total_batch_duration_ms` | 707047 | 665839 | -41208 |

### Dispatch/runtime outcome
| metric | base | treatment | delta |
|---|---:|---:|---:|
| `planned_provider_intents` | 1405 | 1393 | -12 |
| `runnable_provider_intents` | 755 | 755 | 0 |
| `dispatch_request_count` | 413 | 407 | -6 |
| `title_lane_group_count` | 340 | 326 | -14 |
| `title_lane_intent_count` | 414 | 394 | -20 |
| `title_lane_request_count` | 266 | 253 | -13 |
| `post_openalex_suppressed_group_count` | 74 | 73 | -1 |
| `post_openalex_unsuppressed_targeted_group_count` | 52 | 48 | -4 |
| `non_batch_dispatch_request_count` | 410 | 404 | -6 |

### `url_canonical_only` request shift
Base:
- `openalex.url_canonical_only`: `126`
- `crossref.url_canonical_only`: `52`

Treatment:
- `openalex.url_canonical_only`: `121`
- `crossref.url_canonical_only`: `48`

So the patch removed:
- `5` OpenAlex title requests
- `4` Crossref title requests

while adding deterministic DOI-path work only where recoverable.

## Semantic effect
### What actually improved
There was exactly **one new merged/canonical win**:

- `cand_8c0fcffbabdce4e6`
- base:
  - `openalex[title]` unmatched
  - `crossref[title]` returned wrong DOI `10.14366/usg.25200`
  - no merged proposal
- treatment:
  - recovered DOI from `url_canonical` via `recursive_url_decode`
  - `openalex[doi_batch]` matched `10.14366/usg.23232`
  - `crossref[doi]` matched `10.14366/usg.23232`
  - new merged proposal created:
    - title: `Ultrasonography of acute retroperitoneum`
    - venue: `Ultrasonography`
    - DOI: `10.14366/usg.23232`

### Additional matched-source gains without output-count change
Matched source records increased on 5 candidates:
- `cand_721f728d8e406dd5` (`1 -> 2`)
- `cand_8c0fcffbabdce4e6` (`0 -> 2`)
- `cand_983e32088eed4586` (`1 -> 2`)
- `cand_aafaa7c0485410af` (`1 -> 2`)
- `cand_ef45f083c154b55c` (`1 -> 2`)

Interpretation: most recovered DOI cases were already eventually resolved by title or Crossref, so the main large-slice gain is not broad semantic expansion but a mix of:
- cleaner routing
- fewer title-lane requests
- a small but real recall gain on a hard residual candidate

### Safety check
- `merge_review_queue_count` stayed `2 -> 2`
- review members stayed unchanged:
  - `cand_3a6f282d35458d76` → `severe_conflict:doi`
  - `cand_380600011de29f8b` → `severe_conflict:doi`
- no new severe-review spill was introduced

## Interpretation
### Known
- The patch survives `large-fixed` validation.
- It is still narrow and behaviorally clean.
- It reduces title-lane pressure and overall dispatch count.
- It produces one real new canonical paper on this slice.
- It does not enlarge the review queue.

### Inferred
- This patch is worth keeping, because it buys both runtime improvement and a small recall gain with very limited blast radius.
- The gain profile is exactly what we wanted from a micro-lane: mostly route cleanup, occasionally rescuing a stubborn residual miss.
- The remaining larger recall bottleneck is no longer “missing deterministic DOI from obvious URL identities” in general; after this patch, the next layer is more likely in acceptance / post-match policy rather than raw identifier recovery.

### Speculative
- If we continue in this direction, the only plausible extensions worth testing are similarly deterministic publisher-local rules, not broader fuzzy URL heuristics.
- The stronger next runtime/recall opportunity may now be the repository/venue acceptance boundary previously seen in `cand_e6e0961ddf95e426`, rather than more DOI extraction breadth.

## Decision
**Promote / keep this patch.**

Reason:
- narrow scope
- `dispatch_request_count -6`
- `title_lane_request_count -13`
- `matched_source_record_count +6`
- `canonical_paper_count +1`
- `merge_review_queue_count +0`
- `total_batch_duration_ms -41208`

This is a clean positive on `large-fixed`, not just on `small-fixed`.
