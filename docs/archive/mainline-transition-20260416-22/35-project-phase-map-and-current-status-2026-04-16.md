# MyGoogleAlertPapers 项目阶段地图与当前状态（2026-04-16）

## 这份文档的用途

这是一份面向后续 agent 或人类接手者的高层入口文档。

目标不是复述所有历史过程，而是用最少阅读成本回答四个问题：

1. 项目现在做到哪一阶段了
2. 哪些阶段性结论已经稳定
3. 当前默认该采用什么策略
4. 下一步最值得做什么

如果是第一次接手项目，建议先读本文，再决定是否下钻到 Package A / Package B 的细节文档。

---

## 一句话总览

项目当前处于：

> **late prototype / early hardening / validation-infrastructure transition**

也就是：

- 主链路已经可运行
- 多轮真实 slice 验证已经完成
- correctness 不再是纯猜测
- 当前重点已经从“把功能做出来”转向“把策略比较、证据归档和长跑执行稳定化”

这不是 planning 阶段，也还不是 production-ready。

---

## 项目主线目标

项目目标可以压缩为：

`Google Scholar alert emails -> candidate extraction -> normalization -> external enrichment -> conservative merge -> dedup -> canonical paper store`

核心约束一直是三条：

1. mailbox 读写安全
2. canonical 库不被错误 identifier / noisy metadata 污染
3. 整个流程必须可验证、可复跑、可做资源/accounting 说明

---

## 阶段地图

## Phase 0. 基础管线成型

这一阶段已经完成。

已具备完整 CLI 阶段：

- `init-db`
- `scan-mailbox`
- `parse-mails`
- `normalize-candidates`
- `enrich-candidates`
- `merge-metadata`
- `dedup-candidates`
- `report-*`
- `export-review-queue`

数据库主干也已经成型，包括：

- candidate / normalized candidate
- provider query cache
- source record
- enrichment status
- merged proposal
- canonical paper
- candidate-paper link
- merge review queue
- cost event
- batch run

结论：项目不是 toy repo，而是已经形成可执行研究管线。

---

## Phase 1. Package A, replay substrate 与 normalized-only fallback 建立

这一阶段的核心问题是：

> 能不能把 replay comparison 做成真正可用的策略比较基线，并验证 normalized-only fallback 是否值得保留。

### 已稳定的结论

Package A 的关键结论已经成立：

- policy profile 已经真实接入执行
- replay validation workflow 已经能输出标准化比较结果
- DOI clean 已验证有效
- `normalized_only_fallback` 已经在 same-batch replay 上显示明显收益

在固定 249-candidate slice 上：

- baseline: `176 canonical`
- conditional_sources_v2 / normalized-only fallback treatment: `204 canonical`
- delta: `+28 canonical`
- review queue: 不增加
- severe DOI conflict: 不增加

### 当前对项目的意义

这意味着：

- `conditional_sources_v2` 不是“想法”，而是已有 replay 证据支撑的工作默认路径
- provider 未命中导致的 candidate 蒸发问题，已经被 fallback 机制显著兜住

### 当前该怎么看 Package A

Package A 不是当前主要不确定性来源了。
它更像是：

- 当前默认基线的建立阶段
- 后续 Package B 以及更晚阶段比较的地基

### Canonical doc

- `docs/21-packageA-implementation-and-replay-results-2026-04-15.md`

### Canonical evidence

- `docs/validation/packageA-baseline-guardrail-replay-100-2026-04-15.{md,json}`
- `docs/validation/packageA-conditional-sources-v2-replay-100-2026-04-15.{md,json}`

---

## Phase 2. Package B, fallback guardrail tightening 与 larger-slice decision

这一阶段的核心问题是：

> 在 normalized-only fallback 已经证明有价值后，如何进一步收紧高风险 case，而不把整体收益吃掉。

### Package B 内部发生了什么

这一阶段经历了三步：

1. **v3 guardrail**
   - 对 normalized-only fallback 增加 stricter guardrail
2. **v4 narrow salvage**
   - 尝试在更严格 guardrail 上只救回极少量高 precision case
3. **formal larger-slice replay**
   - 在更大的 fixed seed 上重新比较 `v2` 与 `v4`

### 当前稳定结论

Package B 的最终部署结论已经明确：

- broader/default policy recommendation 回到 **`conditional_sources_v2`**
- `conditional_sources_v4_fallback_guardrail_salvage` 只保留为**窄范围实验/诊断 profile**

在 formal larger fixed seed (`368 candidates / 1405 provider intents`) 上：

- `v2`: `293 canonical / 2 review / 368 merged / 777 matched_source_record`
- `v4`: `284 canonical / 10 review / 367 merged / 780 matched_source_record`

因此：

- `canonical -9`
- `review +8`
- `merged -1`
- `matched_source_record +3`

解释很清楚：

- `v4` 的广泛 low-similarity fallback guardrail 太贵
- 它增加了 review 负担，并压低 canonical yield
- 少量 salvage 收益不够抵消这个代价

### 这一阶段的另一个 durable outcome

Package B 不只是 policy 比较，还暴露并修复了 larger replay orchestration 的脆弱点：

- OpenAlex `primary_location.source = null` bug 已修复
- 增加了 stage timeout
- 增加了 enrich progress logging
- 增加了 checkpoint commit
- 增加了 fixed-seed resume + summary workflow

也就是说，Package B 同时推进了：

- **策略判断能力**
- **长跑验证鲁棒性**

### 当前该怎么看 Package B

Package B 的核心决策已经结束。
后续不应继续围绕完整 `v4` 扩展启发式，而应：

- 回到 `v2`
- 只在非常窄的 anti-garbage patch 上继续试验

### Canonical docs

- `docs/33-packageB-decision-memo-2026-04-16.md`
- `docs/34-packageB-phase-summary-and-archive-guide-2026-04-16.md`
- `docs/32-packageB-large-slice150-v2-v4-decision-analysis-2026-04-16.md`

### Canonical evidence

- `docs/validation/packageB-large-slice150-summary-20260416_slice150.{md,json}`
- `docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.{md,json}`
- `docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.{md,json}`

---

## 当前默认策略与代码含义

如果现在有人问“当前主线默认该怎么理解”，答案是：

### 当前默认策略基线

- 使用 Package A 确立的 `conditional_sources_v2` 方向
- 保留 normalized-only fallback
- 不把完整 `v4` 作为默认策略

### 当前更可信的工程方向

- broad recall 仍然重要
- guardrail 必须 narrow and high-precision
- 对 fallback-only case 的收紧不能靠广泛 low similarity gate 一刀切

### 当前不应作为默认的方向

- broad `low_source_title_similarity` default blocking
- broad `sparse_metadata_low_source_title_similarity` default blocking
- 尚未被正式比较证明值得进入主链路的附加 source / heuristic

---

## 当前最值得读的文档顺序

如果是新 agent / 新人，推荐阅读顺序为：

1. `docs/35-project-phase-map-and-current-status-2026-04-16.md`
2. `docs/33-packageB-decision-memo-2026-04-16.md`
3. `docs/34-packageB-phase-summary-and-archive-guide-2026-04-16.md`
4. `docs/21-packageA-implementation-and-replay-results-2026-04-15.md`
5. `docs/validation/packageB-large-slice150-summary-20260416_slice150.md`

如果需要进一步追代码锚点，再看：

- `src/mygooglealertpapers/pipeline/merge.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/enrich/openalex.py`
- `scripts/replay_validation.py`

---

## 当前仍然打开的问题

虽然 Package B 的主决策已经完成，但项目仍有几个后续工作入口：

### 1. narrow anti-garbage patch 是否值得保留

当前最合理的下一步 policy 实验是：

- 从 `v2` 出发
- 只保留 obvious author-blob / malformed-title rejection
- 不带 broad low-similarity guardrail
- 再用同一 larger fixed seed 验证

### 2. 文档与长期状态同步机制要继续执行

这次 Package B 已经做了 active / archive 分层。
后续其它阶段也应遵守相同模式：

- active 层只留 current decision / current state / canonical evidence
- 过渡性文档转 archive

### 3. 长后台任务 follow-up 模式要固定为链式

这次 larger-slice formal replay 暴露出一个非代码但很实际的问题：

- one-shot follow-up 不够
- current-session follow-up 不能默认依赖 announce / 隐式 delivery

今后对长跑任务应固定采用：

- chained sparse follow-up
- `sessionTarget=current`
- 当前会话回报优先 `delivery.mode=none`

---

## 当前最值得做的下一步

如果现在继续推进项目，我的推荐顺序是：

1. **以 `v2` 为主线，做 very narrow anti-garbage patch 实验**
2. 继续保持文档 active / archive 分层，不再堆积 phase-local 中间报告
3. 如后续进入 Package C 或新的 source/policy 迭代，先复用当前 replay substrate，而不是重新发明比较流程

---

## 最终压缩版结论

如果把当前项目状态压成最短版本：

> MyGoogleAlertPapers 的主管线和 replay substrate 已经站稳；Package A 证明了 normalized-only fallback 值得保留，Package B 证明了 broad fallback guardrail 不该默认上线；当前默认策略应回到 `conditional_sources_v2`，下一步只应尝试 very narrow 的 anti-garbage patch，而不是继续扩展完整 `v4`。
