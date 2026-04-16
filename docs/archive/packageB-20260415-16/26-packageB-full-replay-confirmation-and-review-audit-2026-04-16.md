# Package B full replay confirmation and review audit（2026-04-16）

## 1. 本轮目标
确认 `conditional_sources_v3_fallback_guardrail` 在 **full replay（enrich + merge + dedup）** 下是否仍保持与 manual replay 一致的结论，并对新增的 8 条 review case 做第二轮结构化判断。

## 2. Full replay 是否复现了 manual replay 结论
### 2.1 核心结论：**是，终局一致**

| 指标 | v2 | v3 manual | v3 full | 结论 |
|---|---:|---:|---:|---|
| source_record | 951 | 951 | 951 | 一致 |
| matched_source_record | 498 | 498 | 512 | full enrich 命中略增 |
| merged_metadata_proposal | 249 | 248 | 248 | 与 manual 一致 |
| merge_review_queue | 2 | 10 | 10 | 与 manual 一致 |
| canonical_paper | 204 | 195 | 195 | 与 manual 一致 |

因此：

> `v3` 的 guardrail 结论 **不依赖 manual replay 的偶然状态**。即使从 base 100 DB 重新做 full replay，最终 `merge/review/canonical` 终局仍保持一致。

### 2.2 运行与资源信息
- full replay DB: `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_full_20260416.db`
- summary: `docs/validation/packageB-conditional-sources-v3-fallback-guardrail-replay-100-full-2026-04-16.{json,md}`
- provider intents: `951`
- batch duration: `1141992 ms`（约 19.0 min）
- paid LLM usage: `none`

### 2.3 需要正确解读的一点
full replay 的 `dirty_doi_output_count = 9`，而 manual replay 相关文档里是 0。
这 **不是回归**，而是因为这次 full replay 只跑了 `enrich + merge + dedup`，没有重跑 `normalize`，所以它继承了 base 100 DB 里的脏 DOI 状态。

结论上应解读为：
- **Package B guardrail 本身已复现成功**
- 但 **DOI cleaning 属于 Package A normalize 修复链**，不是这次 v3 guardrail replay 自动覆盖的内容

## 3. v3 新增的 8 条 review case
相对于 v2 原本 2 条 review，v3 新增了以下 8 条：

- `cand_054270b0fef2b17a`
- `cand_1d53b41d67c6e37e`
- `cand_3c0daf67a3c4f756`
- `cand_505b2326b7b8f0e5`
- `cand_7237121835e51fe0`
- `cand_8c0fcffbabdce4e6`
- `cand_cc340e92866d3360`
- `cand_e4783c70fe9603a2`

## 4. 二审判断

| candidate_id | guardrail reason | 当前判断 | 理由摘要 |
|---|---|---|---|
| `cand_054270b0fef2b17a` | low_source_title_similarity | **review 合理** | 俄文题目本身像真实综述，但 provider 证据明显跑偏，无 DOI/PMID/PMCID，不应 direct canonical |
| `cand_1d53b41d67c6e37e` | title_has_author_tail_pollution | **review 合理，但可后续 salvage** | Crossref 标题高度对齐（0.822），但 candidate 标题尾部混入作者/学位信息，像 parser 污染；不该 direct accept，但适合后续做 title-clean salvage |
| `cand_3c0daf67a3c4f756` | low_source_title_similarity | **review/偏 reject** | Neuroimaging + biomarker candidate 与 provider 命中严重偏移，当前证据不足 |
| `cand_505b2326b7b8f0e5` | sparse_metadata_low_source_title_similarity | **review/偏 reject** | 无作者/venue/year/identifier，provider 结果弱且跑偏，典型“不能 direct canonical”的 case |
| `cand_7237121835e51fe0` | low_source_title_similarity | **review 合理** | 看起来像会议摘要或 late-breaking abstract，标题可能真实，但 provider 支撑弱，不宜直接入 canonical |
| `cand_8c0fcffbabdce4e6` | low_source_title_similarity | **review 合理** | 题目尾部有截断/污染迹象，且 provider 支撑不足，直接 canonical 风险高 |
| `cand_cc340e92866d3360` | low_source_title_similarity | **review 合理** | 中文题目可能真实，但 provider 证据明显错配，不足以 direct accept |
| `cand_e4783c70fe9603a2` | low_source_title_similarity | **review 合理** | 中文题目可能真实，但外部证据最弱（max sim 0.246），继续 review 是保守且正确的 |

## 5. 综合判断
### 5.1 已知（established）
- v3 full replay 复现了 manual replay 的终局：`248 merged / 10 review / 195 canonical`
- v3 新增 review 的 8 条全部都是“证据不足但未必可直接判死”的 case
- 没有看到明显“本应 direct accept 却被 v3 大规模误杀”的证据

### 5.2 推断（inference）
- v3 guardrail 现在已经达到一个比较健康的状态：
  - **不是粗暴回滚 fallback**
  - 而是把高风险 normalized-only fallback 从 direct canonical 路径移到 review
- 8 条新增 review 中，绝大多数都支持继续保留 review，而不是放回 direct accept

### 5.3 值得保留的细化洞察
`cand_1d53b41d67c6e37e` 很重要，因为它提示了一类“**本体可能真实，但标题尾部被作者串污染**”的 salvage case。
这意味着未来可以考虑新增一条更克制的后处理：

- 先做 title tail cleanup
- 再重新比较 cleaned title 与 provider title
- 若高相似，则可从 review 恢复为 direct accept

这会比单纯继续收紧 guardrail 更有价值。

## 6. 当前建议
### 建议 1
把 `conditional_sources_v3_fallback_guardrail` 视为新的 **主 treatment 候选**。当前证据已经足够支持它优于 v2 的 direct fallback 行为。

### 建议 2
下一轮不要优先继续“收紧 guardrail”，而应优先做一条 **parser / title cleanup salvage path**，重点针对：
- author tail pollution
- 截断尾巴 / ellipsis 污染
- 标题后拼作者/学位信息

### 建议 3
如果要继续 validation，优先做：
1. 针对 `cand_1d53...` 这类 case 的 salvage 原型
2. 在同一 249-candidate slice 上复跑
3. 验证能否只恢复少量高置信真实 case，而不把坏 case 放回 canonical

## 7. 结论
当前我认为可以把这轮 Package B 总结为：

> `v3 fallback guardrail` 已被 full replay 复现确认，方向正确，且新增拦下的 8 条 review case 大多都挡得对。
> 下一步最有价值的工作不是继续加硬拦截，而是补一条更精细的 **污染标题 salvage path**。
