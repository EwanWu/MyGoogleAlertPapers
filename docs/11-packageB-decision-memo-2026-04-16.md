# Package B decision memo (2026-04-16)

## One-line decision

Package B 的 broader/default policy recommendation **回退到 `conditional_sources_v2`**。`conditional_sources_v4_fallback_guardrail_salvage` 只保留为窄范围实验/诊断 profile，不作为默认部署策略。

## Why this decision changed

较早的小样本结论曾让 `v4` 看起来可接受，因为它在固定 249-candidate slice 上只救回了 1 条高 precision case，同时没有暴露太多 guardrail 代价。

但在 formal larger fixed seed (`368 candidates / 1405 provider intents`) 上，`v4` 的整体表现明显差于 `v2`：

- `v2`: `293 canonical / 2 review / 368 merged / 777 matched_source_record`
- `v4`: `284 canonical / 10 review / 367 merged / 780 matched_source_record`

即：

- `canonical -9`
- `review +8`
- `merged -1`
- `matched_source_record +3`

结论很明确：`v4` 虽然多拿到少量 source match，但没有转化成更好的 merge 终局，反而把更多原本 `v2` 会通过的 fallback-only case 挡进了 review。

## Mechanism-level interpretation

这次 larger-slice regression 的核心不在 enrich，而在 merge fallback policy：

- `v4` 把“高 precision 的反垃圾/author-blob 检测”
- 和“广泛的 low title similarity guardrail”

绑在了一起。

在较大 fixed seed 上，真正造成退化的是后者。也就是说：

- **值得保留的方向**：明显 author-blob / malformed-title 拦截
- **当前不该默认保留的方向**：broad `low_source_title_similarity` / `sparse_metadata_low_source_title_similarity` 默认阻断

## Operational conclusion

本轮较大样本比较已经足够支持一个部署判断：

> 对 Package B 当前阶段，整体表现优先于额外保守性，因此默认策略应回到 `v2`。

## Recommended next step

如果继续做 Package B policy 迭代，推荐路线不是继续扩展完整 `v4`，而是：

1. 以 `v2` 作为主路径
2. 只保留 very narrow 的 anti-garbage patch
3. 用同一 larger fixed seed 重新验证

建议只测试这种窄 patch：

- obvious author-blob title
- obvious malformed-title rejection

不要默认带上 broad low-similarity guardrail。

## Canonical docs to read now

如果后续 agent 或人类只读最少文档，优先读这几份：

1. `docs/11-packageB-decision-memo-2026-04-16.md`（本 memo）
2. `docs/12-packageB-phase-summary-and-archive-guide-2026-04-16.md`
3. `docs/10-packageB-large-slice150-v2-v4-decision-analysis-2026-04-16.md`
4. `docs/validation/packageB-large-slice150-summary-20260416_slice150.md`

## Accounting note

本轮 formal replay 未使用 paid LLM path。

- `No paid LLM call path was exercised in this replay run.`
