# MyGoogleAlertPapers：当前问题、解决方案、进度分析与近中远蓝图（2026-04-15）

## 1. 项目当前所处位置

这个项目已经完成了最关键的一步：**从概念验证跨入可运行原型**。

但它还没有进入“可放心大规模扩展”的状态。更准确地说，当前处于：

**late prototype -> early hardening -> validation/productization transition**

也就是：
- 主链路已经存在并多次跑通
- 第一轮正确性控制已经取得实质进展
- 下一阶段的瓶颈不再是“能不能跑”，而是“能不能稳定、可比、可扩展、可记账地跑”

---

## 2. 当前项目存在的问题，按层次拆解

## 2.1 问题一，验证基础设施还没有真正产品化

### 表现
虽然已经有：
- replay blueprint
- `scripts/replay_validation.py`
- `config/policy_profiles/conditional_sources_v2.yaml`

但目前 replay workflow 还没有真正成为“标准验证底座”。

主要缺口有两个：
1. `--policy-profile` 还没有真正驱动 enrich / merge 行为
2. replay reset contract 没有清理 `query_cache`，会污染严格对比

### 本质
当前的 replay 更像“半自动实验脚本”，还不是“可信的比较实验平台”。

### 风险
如果不先解决这个问题：
- 后续 source policy 改动的收益很难精确归因
- 正确性改进和缓存/环境效应会混在一起
- 结论容易被误读

### 解决方案
1. 把 policy profile 接入 `Settings`
2. enrich 阶段按 profile 控制：
   - provider enable/disable
   - Europe PMC / arXiv / PubMed trigger rules
   - provider ordering
3. merge 阶段按 profile 控制：
   - suppression rules
   - fallback policy knobs
4. replay reset 时强制清理 `query_cache`
5. replay 产出统一 JSON + Markdown report
6. 明确 baseline / treatment profile 命名与入口

---

## 2.2 问题二，成本记账 schema 已有，但真实账单能力几乎为空

### 表现
`cost_event` 已有字段：
- `request_count`
- `tokens_prompt`
- `tokens_completion`
- `tokens_total`
- `estimated_cost_usd`

但当前 `CostTracker` 实际写入仍然是：
- request_count = 0
- token = 0
- estimated_cost_usd = 0

### 本质
现在记录的是 **latency/event proxy**，不是实际 monetary accounting。

### 风险
- 无法做真实成本比较
- 无法判断某种 source policy 是“更快但更贵”还是“更快也更省”
- 无法为未来 LLM fallback 做经济边界控制

### 解决方案
1. 新增 `config/provider_pricing.yaml`
2. 对每个 provider request 记录：
   - request_count
   - latency_ms
   - estimated_cost_usd
3. 对免费 provider 也显式记录 `0 USD`
4. 若未来加入 LLM fallback，再接入 token accounting
5. 升级 `report-cost`：
   - per-provider events
   - per-provider total latency
   - per-provider estimated USD
   - batch total estimated USD
   - average cost per candidate / per merged paper

---

## 2.3 问题三，正确性风险已经从“粗错”转成“隐蔽错”

### 表现
当前 100-mail guardrail live run：
- review queue = 0
- pipeline 可稳定结束

这说明大类系统性错误已经被明显压制。

但这并不等于 canonical assignment 全对。
当前更危险的问题变成了：
- 被系统接受、但实际上 quietly wrong 的 merge
- 单 provider 主导 DOI 的 case
- title/venue 差异被判断为 benign，但底层实体不同
- preprint / journal / version relation 还不够显式

### 本质
项目已经越过“明显错误多发”的阶段，进入“残余错误更少但更难发现”的阶段。

### 风险
- canonical store 可能出现低频高伤害污染
- 随着规模扩大，少量静默错误会逐渐积累

### 解决方案
1. 建立 accepted-merge audit sampling 机制
2. 每轮策略更新后抽查：
   - conflict but accepted
   - PubMed involved
   - DOI from single provider
   - arXiv / journal version ambiguity
3. 增加 `audit_export` 或标准 SQL 导出脚本
4. 未来将 merge judgment 从“规则拼接”进一步演化为“evidence ledger + decision trace”

---

## 2.4 问题四，merge judgment 仍然是规则化 guardrail，不是完整证据系统

### 表现
当前 merge 已有：
- field preference
- conflict grading
- severe conflict blocking
- PubMed DOI suppression

但它仍然偏向“规则驱动的局部修补”。

### 本质
系统已具备 guardrail，但还没有形成完整的 evidence-centric merge reasoning。

### 风险
- 后续每增加一个 provider 或 suppression rule，规则相互作用会更复杂
- 规则数增长后，局部修复可能开始带来难以预测的耦合副作用

### 解决方案
中期需要从当前 rule-based merge 进化到更结构化的 merge model：
1. 对每个字段维护 evidence trace
2. 区分：
   - candidate-side evidence
   - identifier-led evidence
   - title-fallback evidence
   - biomedical bridge evidence
3. 对 DOI / PMID / PMCID 建立 stronger source-of-truth hierarchy
4. 输出 “为什么选这个字段” 和 “为什么压制另一个字段” 的结构化原因

---

## 2.5 问题五，provider strategy 已开始条件化，但尚未成为可实验的策略系统

### 表现
项目已经实践出一些对的方向：
- PubMed fallback demotion
- Europe PMC narrowed biomedical bridge
- arXiv narrow trigger

但这些还没有完全沉淀成统一的策略层。

### 本质
目前“策略”还部分散落在代码条件分支里，而不是独立的实验对象。

### 风险
- 策略比较成本高
- 试验不可重复
- 新同学/未来自己难以快速复现当时决策

### 解决方案
1. 将 provider strategy 参数化
2. profile 明确表达：
   - enabled providers
   - trigger modes
   - query policy
   - fallback rules
   - suppression rules
3. 任何策略变更必须以 profile 名称进入 replay comparison
4. 让“策略版本”成为一等对象，而不是口头描述

---

## 2.6 问题六，可扩展性问题已经暴露，尤其在 enrichment IO 端

### 表现
100-mail run 中：
- enrich 占总时间约 96%
- 扫描、normalize、merge、dedup 的成本几乎可以忽略

### 本质
主瓶颈在外部 provider IO，而不是本地算法。

### 风险
规模从 ~100 扩到 ~8000 时：
- 总 wall-clock 可能线性放大
- provider 抖动会主导实验时间
- 如果没有更强缓存/批处理/调度机制，开发节奏会被大幅拖慢

### 解决方案
1. 优先做 replay + cache correctness，而不是再加 provider
2. 对 provider 分层：
   - core providers: Crossref, OpenAlex
   - conditional bridge: Europe PMC
   - narrow specialized: arXiv
   - marginal / optional: Semantic Scholar
3. 做 provider ROI analysis：
   - latency
   - yield
   - corrected merges gained
   - severe conflicts introduced
4. 对低收益高开销 provider 考虑进一步收窄触发条件

---

## 2.7 问题七，review workflow 还不够成熟

### 表现
当前有 review queue 和 export，但还不算完整“人工审核工作流”。

### 本质
系统已经开始把难例挡住，但挡住之后如何高效处理，还没有形成稳定机制。

### 风险
- 一旦后续规模扩大，review case 累积会形成新瓶颈
- 审核结果难以回流成规则改进

### 解决方案
1. review export 中增加：
   - blocking reason
   - field-level evidence summary
   - supporting providers
   - conflicting identifiers
2. 明确 review 的最小输出格式（JSONL/CSV/Markdown）
3. 审核结论回流到：
   - suppression rule backlog
   - test fixtures
   - hard-case registry

---

## 2.8 问题八，repo hygiene 和“状态可读性”仍然偏弱

### 表现
- README 相对滞后
- 有关键未提交文件
- 当前项目真实状态主要靠读多份文档才能拼出来

### 本质
项目技术进展速度快于 repo 状态整理速度。

### 风险
- 上下文切换成本高
- 新实验结果与当前默认策略不容易一眼区分
- 以后复盘困难

### 解决方案
1. 更新 README status
2. 定义 `CURRENT_DEFAULT_POLICY.md` 或在 docs 中维护一页 current state
3. 将未提交的重要 replay / validation 文件整理进有意义的 commit
4. 每轮重大验证后输出一页 short executive update

---

## 3. 项目进度分析

我把进度拆成几个维度评估，而不是只给一个总百分比。

## 3.1 主管线可运行度
**85%**

原因：
- scan / parse / normalize / enrich / merge / dedup 全链路已存在
- 多轮真实 slice 已跑通
- 单元测试已通过

剩余差距：
- 更强的 replay 化
- 更规范的策略切换
- 更强的 review / audit 回路

## 3.2 正确性控制进度
**65%**

原因：
- 已完成第一轮大类错误收敛
- PubMed 噪声问题已明显控制
- 冲突分级与 canonical blocking 已到位

剩余差距：
- quietly wrong accepted merges 仍未被系统性量化
- 版本关系/弱冲突/单源 DOI 还需更细证据体系

## 3.3 验证基础设施进度
**40%**

原因：
- blueprint 已形成
- replay script 已出现
- policy profile 已出现

剩余差距：
- 尚未真正闭环成标准 workflow
- cache reset / policy injection 还未完成
- 结果产物尚未完全标准化

## 3.4 成本与资源记账进度
**20%**

原因：
- schema 已有
- latency/event 已记录

剩余差距：
- request_count 未实装
- estimated_cost_usd 未实装
- 真实 monetary comparison 还不能做

## 3.5 扩展到大规模数据的准备度
**35%**

原因：
- 小到中等 slice 已验证
- enrich IO 瓶颈已明确

剩余差距：
- replay 基础设施未固化
- provider ROI 未完全参数化
- 大规模前缺少更强成本/时长控制

## 3.6 生产级可信度
**25%**

原因：
- 当前仍是研究型原型，不是 production system
- 但架构方向是对的，且已经明显超出 toy 阶段

---

## 4. 项目蓝图：近中远三阶段

## 4.1 近期阶段（现在到下一轮稳定 replay 验证）

### 目标
把项目从“可运行原型”推进到“可重复比较的研究工程平台”。

### 核心任务
1. 完成 Package A replay workflow 闭环
2. 让 policy profile 真正驱动执行
3. 修正 replay reset contract，纳入 `query_cache`
4. 统一 replay report 输出
5. 做一轮 baseline vs conditional strict same-batch replay
6. 建立 accepted-merge audit sampling

### 近期阶段的交付物
- 可用的 `replay_validation.py`
- baseline / conditional profile 文件
- 标准 replay JSON/Markdown report
- audit export 脚本或查询模板
- 一次严格同批比较结果

### 成功标准
- 同一 normalized candidate set 可以一键重跑
- policy change 可以被清晰归因
- replay 结果可被重复解释

### 我建议的近期优先级顺序
1. replay workflow 闭环
2. audit sampling
3. 一轮严格 replay 对比
4. 再考虑新的 suppression rule

---

## 4.2 中期阶段（validation-first hardening 阶段）

### 目标
把当前 rule-based guardrail 升级为更稳定、可解释、可比较的 correctness system。

### 核心任务
1. 建立 suppression rule registry
2. 对 DOI / PMID / PMCID 建立更强 evidence hierarchy
3. 完成 monetary cost accounting
4. 做 provider ROI dashboard / report
5. 优化 provider selection policy
6. 完善 review workflow 和 hard-case registry
7. 把 merge 逻辑往 evidence-ledger 方向推进

### 中期阶段的交付物
- `provider_pricing.yaml`
- 升级版 `report-cost`
- rule registry / suppression trace
- hard-case dataset
- provider ROI analysis 文档
- 更结构化的 merge decision trace

### 成功标准
- 每次策略改动都可以从 correctness、latency、cost 三个维度比较
- review case 可以回流成系统改进
- provider 加减法不再是拍脑袋，而是可量化决策

---

## 4.3 远期阶段（可扩展论文资料基础设施阶段）

### 目标
从“邮件驱动的论文抓取原型”发展为“可信、可扩展、可持续维护的 literature intelligence substrate”。

### 远期方向
1. 扩展到更大邮箱历史（例如 ~8000 mails）
2. 强化 canonical paper / version link / provenance 模型
3. 引入 richer export / downstream analysis interfaces
4. 建立 topic / author / venue / influence 等上层分析层
5. 仅在确有必要时加入 LLM fallback

### 远期前提
远期工作只有在以下条件满足后才值得做：
- replay validation 已稳定
- correctness hardening 有持续可比结果
- cost accounting 已可用
- review workflow 已能闭环

### 远期成功标准
- 系统能在更大规模下保持可信度
- canonical store 不因规模化而快速污染
- 新增上层分析能力建立在稳定底座上，而不是建立在脆弱 ingestion 上

---

## 5. 我的总体判断

这个项目目前最大的矛盾不是“功能不够多”，而是：

**已经有足够多的功能，但还缺一个足够坚实的实验与比较底座。**

因此最优策略不是继续横向扩功能，而是：

1. 先固化 replay validation
2. 再固化成本记账
3. 再推进 correctness system 的结构化升级
4. 最后才考虑更大规模与更高层分析

一句话概括：

> 这个项目已经完成了第一阶段“能工作”，现在必须进入第二阶段“能被严格比较、严格解释、严格扩展”。
