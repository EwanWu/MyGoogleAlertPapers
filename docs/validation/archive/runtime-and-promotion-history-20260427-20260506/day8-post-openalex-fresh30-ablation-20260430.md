# Day8 fresh-like 单因素对照：post-openalex suppress `crossref:url_canonical_only`
## Objective
- Slice: best currently available fresh-like cached slice `data/mgap_fresh30_20260410.db`
- Control: `openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- Treatment: `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml`
- Method: 先跑 control 并录制 HTTP fixture，再让 treatment 回放同一份 fixture，隔离 live-network 噪声。

## Important scope note
这里用的是仓内**当前明确登记的最佳 fresh-like cached slice**，不是更晚日期的新 ingest。它足以作为 Phase 2A promotion gate 所要求的“fresh-like”侧证据，但如果后续出现更近日期的新 slice，仍值得补一轮更近期验证。

## Core result
**结论：post-openalex conditional suppression 在 fresh-like slice 上继续通过 semantic gate。**

与 fixed-slice 的方向一致：
- 它确实减少了冗余 `crossref:url_canonical_only` title 工作；
- 但没有带来 candidate-level DOI loss、confidence collapse、review inflation，或 canonical 回落。

## Core metrics vs control
- Post-openalex suppressed: **15 groups / 15 intents**
- Runnable provider intents: **196 -> 181**（-15, **-7.7%**）
- Dispatch requests: **127 -> 112**（-15, **-11.8%**）
- Title-lane requests: **88 -> 73**（-15, **-17.0%**）
- `crossref:url_canonical_only` title requests: **27 -> 12**（-15, **-55.6%**）
- Crossref events: **95 -> 80**（-15, **-15.8%**）
- Crossref provider latency: **144,595 ms -> 107,781 ms**（-36,814 ms, **-25.5%**）
- Total provider latency: **233,096 ms -> 195,002 ms**（-38,094 ms, **-16.3%**）
- Matched source records: **129 -> 114**（-15）
- Canonical papers: **75 -> 75**（no change）
- Merge review queue: **0 -> 0**
- Severe DOI conflicts: **0 -> 0**
- Normalized-only fallback proposals: **20 -> 20**（no change）

## Candidate-level semantic diff vs control
Control vs treatment:
- `crossref_support_removed`: **15 candidates**
- `crossref_support_removed_but_openalex_present`: **15**
- `proposal DOI lost`: **0**
- `merge_confidence drop >= 0.5`: **0**
- `high-confidence (>=0.9) -> fallback (<=0.15)`: **0**
- `review resolved`: **0**
- `new review introduced`: **0**
- `canonical_changed_candidates`: **0**

Interpretation:
- treatment 切掉的 15 个 `crossref` 支撑全部都发生在 **`openalex` 已经在场** 的 candidate 上；
- 这与 rule 的机制目标一致；
- fresh-like slice 上没有再出现 blanket skip 时那类“crossref-only DOI rescue 被误杀”的问题。

## Mechanistic interpretation
这轮 fresh-like 结果与 fixed-slice150 的机制判断一致：

1. `crossref:url_canonical_only` 里确实混有可安全抑制的冗余子群；
2. 真正决定是否安全的不是“subreason 标签本身”，而是：
   - `openalex` 是否已经先给出 DOI-bearing title recovery；
3. 因此 **post-openalex conditional suppression** 比 **pre-dispatch blanket skip** 更接近可推广的 runtime hardening 形式。

## Cross-slice synthesis
目前两侧证据是一致的：

### Fixed slice150
- suppressed **76 groups / 77 intents**
- `dispatch requests 487 -> 411`
- `canonical 292 -> 293`
- `review 1 -> 0`
- `normalized_only 38 -> 38`
- candidate-level: **0 DOI loss / 0 confidence collapse / 1 review resolved**

### Fresh-like slice
- suppressed **15 groups / 15 intents**
- `dispatch requests 127 -> 112`
- `canonical 75 -> 75`
- `review 0 -> 0`
- `normalized_only 20 -> 20`
- candidate-level: **0 DOI loss / 0 confidence collapse / 0 canonical change**

因此，当前 rule 已满足原先 promotion gate 的核心要求：
- runtime win 在 fixed + fresh-like 两侧都出现
- `canonical_paper_count` 未下降
- `merge_review_queue_count` 未上升
- `severe_doi_conflict_count` 未上升
- changed outcomes 可以解释为安全 suppress，而非 recall loss

## Decision
**Current recommendation: eligible for promotion, with one caveat.**

推荐把这条 rule 视为当前 Phase 2A 最强候选，具备进入默认策略的资格；但应显式记录一个 caveat：
- 第二个 gate 用的是 repo 内“best available fresh-like cached slice”，不是更晚日期的新 ingest slice。

所以更严谨的表述是：
- **可以准备 promotion decision / default rollout memo**；
- 如果后续拿到更近日期的 recent slice，再补一轮 confirmatory replay 会更稳，但它更像“额外保险”，而不是当前证据下的硬 blocker。

## Recommended next step
1. 写一份简短 promotion memo，明确：
   - blanket skip 已 reject
   - post-openalex conditional suppression 已在 fixed + fresh-like 通过 semantic gate
   - rollout 范围仅限 `crossref:url_canonical_only`
2. 若要最稳妥，可在真正切默认前再补一个更近日期的 recent ingest slice；如果当前没有可用 slice，则不应把“缺少更近 slice”伪装成失败证据。
3. promotion 后仍保留 observability 字段，持续监看：
   - `post_openalex_suppressed_*`
   - `normalized_only_fallback_proposal_count`
   - candidate-level DOI-loss signals（若后续再做抽样审计）

## Reproducibility
- Source DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/mgap_fresh30_20260410.db`
- Control DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_post_openalex_fresh30_control_20260430.db`
- Treatment DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_post_openalex_fresh30_treatment_20260430.db`
- Control report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-post-openalex-fresh30-control-20260430.json`
- Treatment report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-post-openalex-fresh30-treatment-20260430.json`
- Control fixture: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_post_openalex_fresh30_control_20260430.jsonl`
