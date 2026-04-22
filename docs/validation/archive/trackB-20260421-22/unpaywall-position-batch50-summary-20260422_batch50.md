# Unpaywall position experiment, oldest cached 50-mail batch (20260422_batch50)

## What I ran
- Seed source: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- Batch choice: oldest 50 locally cached Google Scholar alert mails
- Mail date range: `18-Mar-2026 21:59:59 +0000` -> `02-Apr-2026 06:41:39 +0000`
- Mail count: `50`
- Candidate count: `188`
- DOI-positive normalized candidates: `88`

## Constraint
- Live IMAP mailbox access currently fails with EXAMINE Unsafe Login, so this run uses the oldest reproducible locally cached Scholar mails instead.

## Baseline current enrich cost (conditional_sources_v2)
- total_provider_latency_ms: `983056`
- canonical_paper_count: `165`
- merge_review_queue_count: `2`
- paid_llm_usage_present: `False`

### Provider breakdown
- arxiv: events=2, total_latency_ms=2806, estimated_cost_usd=0.0
- crossref: events=188, total_latency_ms=373498, estimated_cost_usd=0.0
- europepmc: events=77, total_latency_ms=124326, estimated_cost_usd=0.0
- none: events=376, total_latency_ms=0, estimated_cost_usd=0.0
- openalex: events=188, total_latency_ms=173804, estimated_cost_usd=0.0
- pubmed: events=77, total_latency_ms=157990, estimated_cost_usd=0.0
- semanticscholar: events=188, total_latency_ms=150632, estimated_cost_usd=0.0

## Incremental Unpaywall overhead on top of baseline
- added_latency_ms: `85343`
- added_latency_ratio_vs_baseline: `0.0868`
- added_remote_events: `76`
- added_cache_hits: `12`
- added_provider_intents: `88`
- added_source_records: `88`

## Candidate-level output delta vs baseline
- canonical_paper_count delta: `-18`
- merge_review_queue_count delta: `0`
- normalized_only_fallback_proposal_count delta: `-18`
- matched_source_record_count delta: `83`

## Placement comparison
| Placement | unique DOI | matched | OA url | fill rate | latency ms | request reduction vs current |
|---|---:|---:|---:|---:|---:|---:|
| candidate_level_current | 76 | 71 | 30 | 0.4225 | 85343 | 0.0 |
| post_merge_proposal_level | 146 | 71 | 30 | 0.4225 | 79772 | -0.9211 |
| post_dedup_canonical_level | 145 | 71 | 30 | 0.4225 | 79772 | -0.9079 |

## Recommendation
- best_position: `post_dedup_canonical_level`
- 在这批 50 封邮件上，candidate-level 插入已经改变了下游输出，因此不应前置到 merge 之前。
- post-dedup 与 post-merge 的 OA URL 覆盖相同，因此应优先选择调用数更少的 post-dedup。
- 相对 current candidate-level，post-dedup 预计把 Unpaywall 唯一 DOI 请求从 76 降到 145，减少比例约 -0.9079。

## Artifacts
- selection: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/unpaywall-position-batch50-selection-20260422_batch50.json`
- baseline report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/unpaywall-position-batch50-baseline-20260422_batch50.json`
- summary json: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/unpaywall-position-batch50-summary-20260422_batch50.json`
- log: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/logs/unpaywall_position_batch50_20260422_batch50.log`
- state: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/task_state/unpaywall_position_batch50_20260422_batch50.json`
