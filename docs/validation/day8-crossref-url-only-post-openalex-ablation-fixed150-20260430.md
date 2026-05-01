# Day8 fixed-slice150 单因素对照：post-openalex suppress `crossref:url_canonical_only`
## Objective
- Control: `openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- Treatment: `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml`
- Method: 复用同一份 control fixture (`http_fixture_day8_crossref_url_only_control_150_20260430.jsonl`) 做 replay，隔离 live-network 噪声。
- Rule under test: **不要预先 blanket skip** `crossref:url_canonical_only`；而是在 `openalex` title 先执行后，只有当 `openalex` 已经恢复出 DOI-bearing title match 时，才抑制后续 `crossref` title 请求。

## Core result
**结论：这个更窄的 post-openalex conditional suppression 在 fixed slice150 上通过了第一道 semantic gate。**

它不是“零风险证明”，但在当前 fixed-slice 证据上：
- 保住了之前 blanket skip 误杀的 30 个 `crossref-only DOI rescue` 语义；
- 同时吃到了大约 **60%** 的 `crossref:url_canonical_only` 请求节省；
- 并保留了那个唯一有价值的 precision gain（review/conflict cleanup case）。

## Core metrics vs control
- Suppressed post-openalex groups: **76 groups / 77 intents**
- Runnable provider intents: **755 → 678**（-77, **-10.2%**）
- Dispatch requests: **487 → 411**（-76, **-15.6%**）
- Title-lane requests: **340 → 264**（-76, **-22.4%**）
- Crossref events: **368 → 291**（-77, **-20.9%**）
- Crossref provider latency: **610,951 ms → 391,016 ms**（-219,935 ms, **-36.0%**）
- Total provider latency: **928,175 ms → 743,555 ms**（-184,620 ms, **-19.9%**）
- Matched source records: **608 → 533**（-75）
- Canonical papers: **292 → 293**（+1）
- Merge review queue: **1 → 0**（-1）
- Severe DOI conflicts: **1 → 0**（-1）
- Normalized-only fallback proposals: **38 → 38**（**no regression**）

## Why this is materially different from the rejected blanket skip
Compared with the earlier blanket `skip crossref:url_canonical_only` treatment:
- blanket skip saved **126** title-lane requests but caused **30 DOI losses** and `normalized_only` fallback inflation **38 → 68`
- post-openalex suppression saved **76** title-lane requests while causing:
  - **0 proposal DOI losses**
  - **0 high-confidence → fallback confidence drops**
  - **0 new review cases**
  - `normalized_only` fallback unchanged at **38**

So the new rule appears to recover the semantic regressions while still retaining:
- **76 / 126 = 60.3%** of the blanket title-lane request savings
- **77 / 127 = 60.6%** of the blanket crossref-event savings
- **219,935 / 342,869 = 64.1%** of the blanket crossref-latency savings

## Candidate-level semantic diff vs control
Control vs post-openalex treatment:
- `crossref_support_removed`: **75 candidates**
- `crossref_support_removed_but_openalex_present`: **75 candidates**
- `proposal DOI lost`: **0**
- `merge_confidence drop >= 0.5`: **0**
- `high-confidence (>=0.9) -> fallback (<=0.15)`: **0**
- `review resolved`: **1**
- `new review introduced`: **0**

Interpretation:
- 所有被移除的 `crossref` 支撑都发生在 **`openalex` 已在场** 的 candidate 上；
- 这和该 rule 的设计目标一致：只在 `openalex` 已恢复 DOI-bearing title match 后抑制 `crossref`；
- 之前 blanket skip 里最致命的那批 **30 个 crossref-only rescue cases** 没有再次出现语义退化。

## The retained precision gain
- `cand_e7ece68ba869a802` — *Bridging Histology and Tractography: First In Vivo Visualization of Short‐Range Prefrontal Connections Informed by Primate Tract‐Tracing*
  - Control: `severe_conflict:doi`（crossref preprint DOI `10.1101/2025.10.22.683760` vs openalex journal DOI `10.1002/hbm.70520`）进入 review。
  - Post-openalex treatment: 在 openalex 已给出 DOI-bearing match 后抑制 crossref，保留 journal article，成功 canonicalize。

## Mechanistic interpretation
这次 fixed-slice 结果说明，上一轮 decomposition 提出的结构性假设基本成立：

- blanket `crossref:url_canonical_only` 之所以失败，不是因为“不能抑制 crossref title”，而是因为 **抑制时机太早、粒度太粗**；
- 一旦把规则改成“**先看 openalex 是否已经给出 DOI-bearing title recovery**，再决定是否还要跑 crossref”，就能把：
  - **openalex 已足够** 的冗余子群抑制掉；
  - 同时保留 **crossref-only DOI rescue** 的必要请求。

而且这次 **76 suppressed groups** 与前一轮 candidate-level decomposition 中最可能可安全压掉的子群规模完全一致：
- `73` 个 `crossref + openalex same DOI`
- `2` 个 `openalex-only DOI-bearing`
- `1` 个 `crossref/openalex DOI conflict`

这说明当前 conditional suppression 的切分边界，至少在 fixed slice 上，和我们事先推出来的“可安全 suppressible 子群”是对齐的。

## Promotion status
- **Pass fixed-slice semantic gate**
- 但还**不能直接 promotion**，因为还缺：
  1. fresh-like / recent-slice control+treatment pair
  2. 跨 slice 稳定性确认（尤其要防止 openalex title recall 在近期样本上波动时重新放大 false suppress）

## Recommended next step
进入下一阶段时，推荐顺序是：

1. **Run fresh-like / recent-slice control+treatment pair**
   - control 仍用 promoted default
   - treatment 用当前 `post_openalex_skip_crossref_url_only` profile
   - 继续使用 control-record / treatment-replay methodology if possible
2. **Gate by the same semantic criteria**
   - canonical papers 不下降
   - merge review burden 不上升
   - severe DOI conflict 不上升
   - normalized-only fallback 不上升
   - candidate-level 不出现新的 DOI loss / confidence collapse
3. **Only if fresh-like also passes**, then consider promotion or a narrow runtime flag rollout

## Reproducibility
- Control report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-crossref-url-only-control-150-20260430.json`
- Blanket-skip report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-crossref-url-only-treatment-150-20260430.json`
- Post-openalex report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-post-openalex-skip-crossref-url-only-fixed150-20260430.json`
- Control fixture: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_crossref_url_only_control_150_20260430.jsonl`
- Control DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_crossref_url_only_control_150_20260430.db`
- Post-openalex DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_post_openalex_skip_crossref_url_only_fixed150_20260430.db`
