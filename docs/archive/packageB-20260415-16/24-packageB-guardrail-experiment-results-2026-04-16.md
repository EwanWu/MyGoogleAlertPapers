# Package B guardrail experiment 结果（2026-04-16）

## 实验设计

- baseline: `baseline_guardrail`
- treatment v2: `conditional_sources_v2`
- treatment v3: `conditional_sources_v3_fallback_guardrail`
- 本次 v3 与 v2 的唯一区别：**只修改 merge fallback guardrail，不改 provider routing / enrich 输出**
- 因此 v3 复用了 v2 的 `source_record`，只重跑 `merge + dedup`，避免 provider 波动混进结论。


## 总表

| 指标 | baseline | v2 | v3 | v3-v2 |
|---|---:|---:|---:|---:|
| matched_source_record | 503 | 498 | 498 | +0 |
| merged | 219 | 249 | 248 | -1 |
| fallback | 0 | 30 | 29 | -1 |
| fallback_review | 0 | 0 | 8 | +8 |
| canonical | 176 | 204 | 195 | -9 |
| review | 2 | 2 | 10 | +8 |

## 关键结果

- v2 -> v3: merged `249 -> 248`，只少了 **1** 条（被直接 reject）
- v2 -> v3: fallback direct canonical `30 -> 29`，少了 **1** 条
- v2 -> v3: fallback_guardrail review `0 -> 8`，新增 **8** 条
- v2 -> v3: canonical `204 -> 195`，下降 **9** 条
- v2 -> v3: review queue `2 -> 10`，增加 **8** 条

## guardrail 实际拦下的 case

- direct reject:
  - `cand_400e144162689110`
- fallback -> review:
  - `cand_054270b0fef2b17a`
  - `cand_1d53b41d67c6e37e`
  - `cand_3c0daf67a3c4f756`
  - `cand_505b2326b7b8f0e5`
  - `cand_7237121835e51fe0`
  - `cand_8c0fcffbabdce4e6`
  - `cand_cc340e92866d3360`
  - `cand_e4783c70fe9603a2`

## 与前面 LLM 审计的对齐

- top-10 首轮 LLM 审计里，非 accept case 共 9 条（7 review + 2 reject）
- 本次最小 guardrail 实际拦住其中 **9/9** 条：1 条 direct reject，8 条转 review
- 这说明“作者串拦截 + 作者污染拦截 + 低相似/稀疏证据降级”这组最小规则已经覆盖了首轮发现的主要风险模式

## 深入解释

这次结果说明 guardrail 设计方向是对的，而且足够克制：
- 它没有大幅吞掉 fallback recall
- 只损失 1 条 merged / direct fallback accept
- 但成功把 8 条证据不足或明显污染 case 从 direct canonical 路径挪到了 review
- 同时拦掉了 1 条明显 parser 残片
- 相比 v2，净效果是：**用 1 条 recall 代价，换来 8 条高风险 case 不再直接入 canonical**

## 仍然需要注意的地方

1. 当前 v3 仍保留 29 条 fallback proposal，其中 21 条继续 direct accept。
2. 这 21 条里，按前面审计，很多是自带 DOI 或 provider/title 支撑较强的 case，方向上是合理的。
3. 下一步不一定要继续收紧；更应该先审核新增 review 的 8 条是否确实都该挡。

## 建议下一步

1. 对这 8 条新增 review case 做人工/LLM 二审，确认是否都值得留在 review
2. 若其中大多数最终仍判 review/reject，则 v3 guardrail 可以视为成功收敛
3. 然后再决定是否要把 v3 profile 升级为新的主 treatment
