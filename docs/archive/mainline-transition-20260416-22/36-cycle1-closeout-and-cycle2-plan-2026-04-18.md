# Cycle 1 结束总结与 Cycle 2 coding / 实验计划（2026-04-18）

## 这份文档的用途

这是一份面向当前项目主线的短周期执行文档。

目标有两个：

1. 用最短篇幅结束当前第一周期的结论收口
2. 给出下一周期可直接执行的 coding 与实验计划

本文默认建立在以下已稳定结论之上：

- Package A 已证明 `normalized_only_fallback` 值得保留
- Package B 已证明 broad fallback guardrail 不应作为默认策略上线
- 当前主线默认策略应回到 `conditional_sources_v2`

---

## 一、Cycle 1 已完成的内容

Cycle 1 可以视为从“策略与验证底座建立”到“默认主线路径收敛”的阶段。

### 1. 主链路与 replay substrate 已经站稳

项目已经具备完整可运行管线：

- `init-db`
- `scan-mailbox`
- `parse-mails`
- `normalize-candidates`
- `enrich-candidates`
- `merge-metadata`
- `dedup-candidates`
- `report-*`
- `export-review-queue`

同时，same-batch replay / fixed-seed replay 已可用于真实策略比较，而不再只是名义上的“profile 切换”。

### 2. Package A 结论已稳定

在固定 249-candidate slice 上：

- baseline: `176 canonical`
- `conditional_sources_v2`: `204 canonical`
- delta: `+28 canonical`
- review queue: 不增加
- severe DOI conflict: 不增加

因此，`normalized_only_fallback` 已从想法变成 evidence-backed baseline direction。

### 3. Package B 结论已稳定

在 formal larger fixed seed (`368 candidates / 1405 provider intents`) 上：

- `v2`: `293 canonical / 2 review / 368 merged / 777 matched_source_record`
- `v4`: `284 canonical / 10 review / 367 merged / 780 matched_source_record`

解释：

- `v4` 只有极小 matched-source gain
- 但 canonical 更差，review 更高
- 因此 broader/default recommendation 回退到 `conditional_sources_v2`

### 4. 长跑执行鲁棒性已有实质提升

Package B 不只是 policy comparison，也完成了以下 execution hardening：

- 修复 OpenAlex `primary_location.source = null` bug
- 增加 stage timeout
- 增加 enrich progress logging
- 增加 checkpoint commit
- 建立 fixed-seed resume + summary workflow

---

## 二、Cycle 1 的正式收口结论

如果把 Cycle 1 压缩成一句话：

> 项目主管线和 replay validation 底座已经建立，默认 merge policy 主线收敛到 `conditional_sources_v2`，后续工作不应再继续扩展 broad fallback guardrail，而应转入 very narrow anti-garbage patch 和受控 provider experiment。

### 当前主线默认理解

- 默认策略：`conditional_sources_v2`
- 保留 normalized-only fallback
- 不将完整 `v4` 作为默认部署策略
- 后续优化只能做 narrow、high-precision、可复验证据驱动的小步实验

---

## 三、Cycle 2 的目标定义

Cycle 2 不再追求“做更多功能”，而是解决两个更窄、更重要的问题：

1. **在不伤 recall 的前提下，能否给 `v2` 加上最小安全 anti-garbage patch**
2. **Unpaywall 作为 experimental OA-enhancement source，是否真的值得纳入标准比较框架并保留**

因此，Cycle 2 应拆成两条顺序执行的工作流：

- **Track A**: `v2` 上的 very narrow anti-garbage patch
- **Track B**: Unpaywall 标准化实验接入

执行顺序上，**Track A 优先于 Track B**。

原因是：

- 当前第一优先级仍是主线 correctness / precision 的稳态改进
- Unpaywall 更像 enhancement source，而不是当前 canonical correctness 的第一主矛盾

---

## 四、Cycle 2 Track A: narrow anti-garbage patch

## 4.1 目标

在 `conditional_sources_v2` 基线之上，只增加非常窄、非常明确的垃圾拦截规则。

### 设计原则

只允许加入这类规则：

- obvious author-blob title
- obvious malformed-title
- 其他可以用简单、明确、可测试规则识别的垃圾 case

明确**不做**：

- broad `low_source_title_similarity` gate
- broad `sparse_metadata_low_source_title_similarity` gate
- 任何会重演 `v4` 风格 review 膨胀的泛化 guardrail

## 4.2 代码任务

### A1. merge 规则实现

主文件：

- `src/mygooglealertpapers/pipeline/merge.py`

计划：

1. 新增 narrow anti-garbage helper / rule block
2. 将规则限定在 fallback-sensitive 的高风险场景
3. 保持 trace 可解释，明确标记触发原因

### A2. profile 配置

新增一个窄 patch profile，例如：

- `config/policy_profiles/conditional_sources_v2_narrow_antigarbage.yaml`

要求：

- 继承 `v2` 主线逻辑
- 仅增加 minimal anti-garbage rule set
- 不引入 broad similarity guardrail

### A3. 测试补充

新增 / 扩展测试：

- obvious author-blob case 应被降级或阻断
- 明显 malformed-title case 应被降级或阻断
- 正常 fallback recover case 不应被误杀
- canonical / review 行为应与规则预期一致

建议重点补到：

- `tests/test_policy_and_merge_fallback.py`
- 如有必要新增更细粒度 merge rule test file

## 4.3 实验设计

### 对照组
- `conditional_sources_v2`

### treatment
- `conditional_sources_v2_narrow_antigarbage`

### 实验对象
- 继续使用当前 larger fixed seed

### 主要终局指标
- `canonical_paper_count`
- `merge_review_queue_count`
- `merged_metadata_proposal_count`
- 代表性错误 case 的人工审计结果

### 过线标准

只有在以下条件同时满足时，patch 才值得保留：

1. canonical 不出现明显下降
2. review 不出现明显膨胀
3. 能明确减少高风险垃圾 canonical 或脏 fallback case
4. 规则具有可解释性，不依赖模糊阈值堆砌

---

## 五、Cycle 2 Track B: Unpaywall 标准化实验接入

## 5.1 目标

回答的问题不是“Unpaywall 能不能返回东西”，而是：

> 它在当前主线管线中，是否带来值得保留的真实边际贡献。

## 5.2 当前判断

已有信息表明：

- Unpaywall 作为 DOI-only source 是可用的
- 它的主要价值在 OA status / OA link / access enhancement
- 它不应被视为核心 bibliographic authority

因此，Track B 的前提必须是：

> Unpaywall 只作为 optional / experimental / OA-enhancement provider 进入标准比较框架。

## 5.3 代码任务

### B1. provider 实现

新增文件：

- `src/mygooglealertpapers/enrich/unpaywall.py`

要求：

- DOI-only lookup
- 返回结构与现有 provider 体系兼容
- 明确区分 bibliographic fields 与 OA/access fields

### B2. provider 接线

需要检查并修改的可能文件：

- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/config.py`
- policy profile YAML
- 相关 provider registry / enable switch 代码

### B3. replay framework 接线

要求 Unpaywall 可以被标准 replay 调用，而不是停留在单独的 ad hoc probe。

重点不是 hit-rate probe，而是让它进入：

- fixed-seed replay
- merge outcome comparison
- summary/report generation

### B4. merge policy 约束

必须明确：

- Unpaywall 不作为 canonical 主记录 authority
- 不与 Crossref / OpenAlex 在 bibliographic truth establishment 上同级竞争
- 它主要服务于 OA status / URL / access enhancement

## 5.4 实验设计

### 对照组
- `conditional_sources_v2`

### treatment
- `conditional_sources_v2 + Unpaywall enhancement`

### 主要评价指标
- `source_record_count`
- `matched_source_record_count`
- `merged_metadata_proposal_count`
- `merge_review_queue_count`
- `canonical_paper_count`
- OA status / OA URL / PDF access coverage 改善情况
- 额外 latency / request 成本

### 判定原则

仅当它满足以下之一时，才值得保留：

1. 明显提升 OA/access value，且几乎不引入冲突或 review 成本
2. 对最终 merge/canonical 终局有明确正增益
3. 它带来的额外调用成本和复杂度与收益相称

如果它只增加一些 source hit 或 source_record，但不改善终局，也不明显增加 OA 实用价值，则不应默认保留。

---

## 六、严格执行约束：避免资源浪费式轮询

这个约束是 Cycle 2 的硬规则。

此前已经踩过坑：长跑实验如果采用高频轮询或低价值 follow-up，会造成不必要的 token / tool / session 资源浪费。

因此 Cycle 2 的所有长跑实验都应遵守：

### 6.1 不允许的做法

- 高频手动轮询 `sessions_list` / `subagents list`
- 短间隔反复 exec / poll 检查同一长任务
- 用 one-shot follow-up 代替完整的链式状态跟踪
- 依赖隐式 announce 导致多通道环境下的错误回报

### 6.2 允许且推荐的做法

对长跑任务固定采用：

- **chained sparse follow-up**
- `sessionTarget=current`
- `delivery.mode=none`
- 必要时由当前会话自己读取结果并继续下一步

### 6.3 运行原则

1. 长任务启动后，不做密集轮询
2. 用 cron 安排稀疏检查点
3. 每次 follow-up 只做高价值判断：
   - 是否完成
   - 是否失败
   - 是否需要 resume / summary / intervention
4. 如果任务未完成，不重复输出低信息量状态
5. 若需要多段跟踪，使用链式 cron，而不是单次提醒或人工盯跑

### 6.4 这条规则的目的

目标不是“少看一眼”，而是：

- 减少工具循环造成的资源浪费
- 把资源用在真正的 merge / replay / summary 终局判断上
- 避免把控制逻辑本身变成主要成本源

---

## 七、建议的执行顺序

## Step 1. 完成 Track A coding
- 新增 narrow anti-garbage 规则
- 新增 profile
- 补测试

## Step 2. 完成 Track A replay
- 固定 seed
- 运行 `v2` vs `v2_narrow_antigarbage`
- 使用链式 sparse cron follow-up，不做密集轮询

## Step 3. 写 Track A decision memo
- 只回答该 patch 是否值得保留

## Step 4. 再进入 Track B coding
- 实现 Unpaywall provider
- 接入 replay framework
- 明确 field-level merge 限制

## Step 5. 完成 Track B replay
- `v2` vs `v2 + unpaywall enhancement`
- 仍采用 fixed-seed comparison + sparse cron follow-up

## Step 6. 写 Track B decision memo
- 只回答它是否值得作为默认 enhancement 保留

---

## 八、当前最小可执行版本

如果只做最小而正确的一轮推进，推荐如下：

### 本轮最小 coding 范围
1. 先只做 `v2_narrow_antigarbage`
2. 先不并行推进 Unpaywall 主线接入
3. 先用同一 larger fixed seed 结束第一轮 policy 小实验

### 本轮最小实验产物
1. 一个新 profile
2. 一组新增测试
3. 一份 fixed-seed replay 对照结果
4. 一份短 decision memo

这能以最小成本回答当前最重要的问题：

> 我们能不能在不重演 `v4` 失败路径的前提下，把 `v2` 再收紧一点点。

---

## 九、最终压缩版

> Cycle 1 已经完成默认策略收敛，主线停在 `conditional_sources_v2`；Cycle 2 应先做 very narrow anti-garbage patch 的小步验证，再把 Unpaywall 作为 OA-enhancement experimental provider 接入标准 replay 框架；所有长跑实验必须采用链式 sparse cron follow-up，避免再次犯资源浪费式轮询错误。
