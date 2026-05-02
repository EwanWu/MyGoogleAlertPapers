# Day12 validation: targeted non-arXiv reject71 + review08 runner reproducibility check (2026-05-02)

## Objective
Verify that the new day12 four-slice runner reproduces the already-established day11 stable replay outcome for:

- `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08`

using:
- donor `source_record` reuse
- `merge + dedup` only
- per-slice residual audit export

## Runner
- `scripts/run_day12_targeted_nonarxiv_reject71_review08_large_20260502.py`

## State / log
- state: `data/benchmark/run_state/day12_targeted_nonarxiv_reject71_review08_large_20260502.state.json`
- log: `data/logs/day12_targeted_nonarxiv_reject71_review08_large_20260502.log`

## Slices
- `large_fixed`
- `fresh30`
- `pkg3_guardrail100`
- `issac100`

## Result
All four day12 runs reproduced the prior day11 stable replay outputs exactly on the checked decision metrics.

### Per-slice exact match
| slice | canonical | review | merged proposals | matched source records | normalized-only fallback |
|---|---:|---:|---:|---:|---:|
| `large_fixed` | `283 -> 283` | `2 -> 2` | `358 -> 358` | `530 -> 530` | `37 -> 37` |
| `fresh30` | `72 -> 72` | `0 -> 0` | `92 -> 92` | `114 -> 114` | `20 -> 20` |
| `pkg3_guardrail100` | `195 -> 195` | `2 -> 2` | `240 -> 240` | `339 -> 339` | `33 -> 33` |
| `issac100` | `207 -> 207` | `4 -> 4` | `238 -> 238` | `339 -> 339` | `26 -> 26` |

### Aggregate exact match
- canonical papers: `757 -> 757`
- review queue: `8 -> 8`
- merged proposals: `928 -> 928`
- matched source records: `1322 -> 1322`
- normalized-only fallback proposals: `116 -> 116`

## Interpretation
### Known
- the day12 runner is functionally reproducible against the previously validated day11 deterministic result
- donor reuse + merge-only replay is wired correctly across all four slices
- residual audit export is wired into the same runner successfully

### Inferred
- this route now has a durable execution entrypoint rather than an ad hoc command bundle
- future threshold micro-iterations can reuse this runner pattern without reintroducing live-provider noise

## Bottom line
The new day12 runner passed the minimal reproducibility gate:

> it reproduces the known day11 `targeted_nonarxiv_reject71_review08` stable replay outcome exactly across all 4 slices.
