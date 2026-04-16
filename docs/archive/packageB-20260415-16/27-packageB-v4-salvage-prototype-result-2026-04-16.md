# Package B v4 salvage prototype result（2026-04-16）

## 1. 原型目标
在 `v3 fallback guardrail` 基础上，仅增加一条非常克制的 salvage 路径：

- 只针对 `author tail pollution`
- 先清理标题尾部混入的作者/学位信息
- 清理后若与 provider title 高相似，且该 provider row 带 identifier（DOI/PMID/PMCID），则允许从 review 恢复为 accept

对应 profile：
- `config/policy_profiles/conditional_sources_v4_fallback_guardrail_salvage.yaml`

## 2. 实现内容
### merge 逻辑新增
- `_strip_author_tail_pollution(...)`
- `_best_source_title_match(...)`
- `_salvage_author_tail_pollution(...)`

### 触发条件
- `fallback_review_author_pollution: true`
- `fallback_author_pollution_salvage_similarity_threshold: 0.8`
- 仅当：
  1. cleaned title 相似度达到阈值
  2. 相比原始污染 title 有显著提升
  3. 最佳匹配 source row 带 identifier

才会从 review 恢复为 accept。

## 3. 单测
`pytest -q tests/test_policy_and_merge_fallback.py` 已通过。

新增测试覆盖：
- author-tail polluted fallback 在 cleaned title 与 source 高相似时可被 salvage

## 4. 小规模 replay 结果
### 运行方式
从 full v3 DB 直接做 `merge + dedup` 对照 replay：
- source: `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_full_20260416.db`
- output: `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v4_fallback_guardrail_salvage_20260416.db`
- summary: `docs/validation/packageB-conditional-sources-v4-fallback-guardrail-salvage-replay-100-2026-04-16.{json,md}`

### v3 -> v4 变化
| 指标 | v3 full | v4 salvage | 变化 |
|---|---:|---:|---:|
| merged_metadata_proposal | 248 | 248 | 0 |
| merge_review_queue | 10 | 9 | -1 |
| canonical_paper | 195 | 196 | +1 |

这是一个非常理想的原型结果：

> v4 只恢复了 **1** 条 case，没有额外放宽其它高风险 review。

## 5. 被成功救回的 case
- `cand_1d53b41d67c6e37e`

### 原始污染标题
`PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease Hugh S Markus, FMed Sci, Marco Egle MSc`

### 清理后标题
`PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease`

### 证据
- raw similarity: `0.822`
- cleaned similarity: `0.980`
- matched source: `crossref`
- supporting identifier: `doi present`

### 解释
这正是我们在前一轮人工判断里指出的“本体可能真实，但 parser 把作者/学位串进标题尾部”的典型 salvage case。

## 6. 当前判断
### established
- v4 salvage 原型在 249-candidate slice 上只影响 1 条 case
- 这 1 条正是此前最值得恢复的 `cand_1d53...`
- 没有看到新的误放宽迹象

### inference
- 这说明“guardrail + 极小范围 salvage”比继续单向收紧更优
- 后续最值得做的不是再加硬拦截，而是继续补少量高精度清理型 salvage

## 7. 建议
当前我倾向于把后续路线定为：
1. 保留 `v3` 的 guardrail 思路
2. 把 `v4` 作为下一轮更优候选
3. 后续只增补少量高精度 salvage，不做大范围放宽

如果继续推进，下一步最值得实现的是：
- ellipsis / truncation 尾部污染清理
- 标题后拼接作者名单但无 credential 的变体清理
- 仍然坚持“必须有 provider 高相似 + identifier 支撑”才允许恢复 accept
