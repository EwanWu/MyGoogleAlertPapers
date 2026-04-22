# Corrected Unpaywall position experiment (20260422_batch50)

## What was corrected
- The first summary mixed in builtin_default merge rules through `unpaywall_only`, which disabled `normalized_only_fallback` and made the candidate-level downstream delta invalid.
- The first placement comparison undercounted post-merge/post-dedup cost because it only had cache for candidate-level DOI queries.

## Baseline current enrich cost
- provider latency total: `983056` ms
- canonical papers: `165`
- review queue: `2`

## Candidate-level Unpaywall, corrected downstream check
- canonical delta: `0`
- review delta: `0`
- normalized_only_fallback delta: `0`
- matched_source_record delta: `83`

## Placement comparison
| placement | unique DOI | OA URL DOI | matched fill rate | estimated latency ms |
|---|---:|---:|---:|---:|
| candidate_level | 76 | 30 | 0.4225 | 85343 |
| post_merge | 151 | 88 | 0.6069 | 161336 |
| post_dedup | 150 | 87 | 0.6042 | 160288 |

## Recommendation
- best_position: `post_dedup`
- 在相同 merge_rules 下，candidate-level 加入 Unpaywall 没有改变 canonical 数或 review queue。
- post-dedup 可覆盖 87 个带 OA URL 的 DOI，高于 candidate-level 的 30。

## Artifacts
- corrected json: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/unpaywall-position-batch50-summary-20260422_batch50-corrected.json`
- corrected md: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/unpaywall-position-batch50-summary-20260422_batch50-corrected.md`
- unpaywall cache: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/unpaywall-position-batch50-unpaywall-cache-20260422_batch50.json`
