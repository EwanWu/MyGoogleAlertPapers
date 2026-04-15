# MyGoogleAlertPapers 项目接手报告（2026-04-15）

## 1. 这是什么项目
这是一个 **local-first** 的 Google Scholar 邮件驱动论文资料库管线，目标是：

`Google Scholar alert emails -> 候选论文抽取 -> 标准化 -> 外部元数据补全 -> 保守合并 -> 去重 -> canonical paper store`

核心约束不是“尽量多抓”，而是：
1. 邮箱读取安全，尤其是 read-only / unread 安全
2. canonical 库不能被错误 DOI/PMID 污染
3. 整个流程要可验证、可复跑、可估算资源开销

---

## 2. 当前代码库真实状态

项目已经明显超过“规划阶段”，现在处于：

**可运行原型 + 多轮真实邮件验证完成 + 正在进入验证基础设施与成本记账产品化阶段**

### 已实现主链路
CLI 已具备完整阶段：
- `init-db`
- `scan-mailbox`
- `parse-mails`
- `normalize-candidates`
- `enrich-candidates`
- `merge-metadata`
- `dedup-candidates`
- `report-*`
- `export-review-queue`

### 已实现核心数据层
数据库 schema 已包含：
- `mail_ingestion_record`
- `raw_mail_snapshot`
- `paper_candidate`
- `paper_candidate_normalized`
- `query_cache`
- `source_record`
- `candidate_enrichment_status`
- `merged_metadata_proposal`
- `canonical_paper`
- `candidate_paper_link`
- `merge_review_queue`
- `cost_event`
- `batch_run`

这说明项目的主干不是纸面设计，而是已经形成了完整的可执行研究管线。

---

## 3. 我对当前架构的理解

### 3.1 ingest / parse
- 从 IMAP 只读扫描 Google Scholar 邮件
- 保存 raw snapshot
- 从邮件正文中抽取 paper candidates

### 3.2 normalize
- 做标题、作者、venue、URL、identifier 的标准化
- 当前已提取 DOI / PMID / PMCID / arXiv id

### 3.3 enrich
当前 provider 逻辑已不是最初简单串行查源，而是：
- Crossref
- OpenAlex
- Semantic Scholar
- PubMed
- Europe PMC
- arXiv

并且具备：
- provider-level intent planning
- provider-level resumability
- authoritative query cache
- OpenAlex DOI batch path
- `ok / no_match / error` 三类状态记录

### 3.4 merge
merge 侧已经进入“保守正确性”阶段，不再只是拼字段：
- field preference
- conflict grading（A/B/C）
- PubMed title-fallback DOI suppression
- canonical blocking guardrail
- review queue

### 3.5 dedup
去重层已能把 merged proposal 映射到 canonical paper，并输出 candidate-paper link。

---

## 4. 项目进度判断

## 4.1 已经完成的关键里程碑
从 git 历史和文档看，主线推进是连贯的：
1. provider-level enrichment resumability
2. authoritative query cache hardening
3. Semantic Scholar 接入与匹配收紧
4. merge guardrails + review queue
5. PubMed fallback demotion
6. Europe PMC / arXiv 条件接入
7. validation infrastructure blueprint 制定

### 当前 HEAD 前后的真实状态
已提交到 `main` 的最近主线：
- `06b86c9` docs: add validation infrastructure blueprint
- `9508bfd` docs: add conditional-source validation and cost reports
- `11e071b` feat: add conditional europepmc and arxiv enrichment paths
- `ef53a68` feat: make pubmed merge fallback-only for core fields
- `040607c` feat: demote pubmed to fallback enrichment path

未提交但已存在的重要工作：
- `scripts/replay_validation.py`
- `config/policy_profiles/conditional_sources_v2.yaml`
- `docs/validation/package3-guardrail-100-validation.md`
- `docs/validation/package3-guardrail-100-detailed-analysis.md`

这说明项目已经从“correctness 规则修补”继续推进到“validation workflow productization”，但这部分还没收口提交。

---

## 5. 目前最可信的验证结论

## 5.1 live 100-mail guardrail run
`data/mgap_pkg3_guardrail_100.db`

结果：
- normalized candidates: `249`
- source records: `996`
- merged proposals: `203`
- canonical papers: `164`
- review queue: `0`
- grade A/B/C: `36 / 4 / 12`
- canonical blocked: `0`

这说明当前默认 guardrail 策略在真实 100-mail slice 上：
- 能完整跑通
- 不会造成 review queue 爆炸
- 主系统性错误（尤其 PubMed title DOI 噪声）基本已被压住

## 5.2 same-batch replay comparison
`data/mgap_pkg3_guardrail_100_replay_conditional_20260410.db`

在同一组 `249` normalized candidates 上：
- merged proposals: `203 -> 211`
- canonical papers: `164 -> 170`
- enrich wall time: `2219856 ms -> 1514821 ms`（约 `-31.7%`）
- review queue: `0 -> 2`

解释：
- 条件 source 策略总体更强
- arXiv / Europe PMC 带来了真实收益
- 同时暴露了 2 个严重 DOI conflict case
- 这更像“新 source 组合暴露潜在冲突”，不是粗暴退化

---

## 6. 我看到的关键强项

1. **架构已经成型**，不是 toy repo。
2. **验证文化是对的**，真实 mailbox slice + replay comparison，而不是只看 unit test。
3. **正确性优先级是健康的**，不是一味追 recall。
4. **provider 策略已经开始从‘全开’转向条件化调度**。
5. **项目已经有 cost schema 和 batch ledger**，虽然还没真正记全账。

---

## 7. 我看到的真正缺口

## 7.1 Package A 只完成了“脚手架”，还没有真正闭环
虽然已经出现：
- `scripts/replay_validation.py`
- `config/policy_profiles/conditional_sources_v2.yaml`

但当前实现存在两个关键未完成点：

### 缺口 A: policy profile 还没有真正驱动执行
`replay_validation.py` 接收 `--policy-profile`，但当前代码只是检查路径存在并把路径写入 summary，**没有把 profile 注入 enrich / merge 逻辑**。

也就是说，现在的 replay workflow 还没有真正做到“同一基线 + 显式策略切换”的产品化。

### 缺口 B: replay reset contract 还不够严格
当前脚本 reset 了：
- `source_record`
- `candidate_enrichment_status`
- `merged_metadata_proposal`
- `canonical_paper`
- `candidate_paper_link`
- `merge_review_queue`
- `cost_event`
- `batch_run`

但 **没有 reset `query_cache`**。

这会让 replay 可能继承旧缓存，从而污染“严格 apples-to-apples policy comparison”。

这点很关键，因为 blueprint 和更早的 replay 文档都把 `query_cache` 视为应清理对象。

## 7.2 monetary cost accounting 仍然是空壳
schema 有：
- `request_count`
- `tokens_prompt`
- `tokens_completion`
- `tokens_total`
- `estimated_cost_usd`

但当前 `CostTracker.record_stage_cost()` 仍然固定写：
- `request_count = 0`
- `tokens_* = 0`
- `estimated_cost_usd = 0.0`

所以项目现在的 `cost_event` 更准确地说只是：
- stage/provider event log
- latency accounting

还不是严格意义上的“billing accounting”。

## 7.3 validation 结论和开发优先级之间，还有最后一层没有产品化
现在文档已经很清楚地把下一阶段定义为：
1. replay workflow productization
2. DOI suppression continuation
3. real monetary cost accounting

我同意这个优先级。

---

## 8. 我对当前项目阶段的判断

最准确的标签是：

**late prototype / early hardening / validation-infrastructure transition**

不是：
- planning
- toy prototype
- production-ready

而是：
- 主管线能跑
- correctness 第一轮收敛完成
- 下一步应该把实验方法和成本记账固定下来，避免继续靠 ad hoc 比较

---

## 9. 我的下一步建议

## 建议 1，最高优先级
**先把 Package A replay validation workflow 做成真正可用的标准基线。**

具体要做：
1. 把 policy profile 真正接入 `Settings` 和 enrich / merge 决策
2. 让 replay script 按 profile 切 provider enable/disable 与 trigger policy
3. 把 `query_cache` 纳入 replay reset contract
4. 输出标准 JSON + Markdown summary
5. 固定 baseline profile 与 conditional profile 的可比较入口

这是现在最值钱的一步，因为之后所有 source policy / suppression rule / cost improvement 都要建立在它上面。

## 建议 2，第二优先级
**补真正的 monetary cost accounting。**

具体要做：
1. 增加 `config/provider_pricing.yaml`
2. 在 provider call site 记录 `request_count`
3. 对免费 provider 也显式记录 `estimated_cost_usd = 0`
4. 让 `report-cost` 同时输出：
   - provider event count
   - latency
   - estimated USD
   - batch total

## 建议 3，第三优先级
**在 replay workflow 固定后，再做一轮 strict same-batch comparison。**

推荐比较：
- baseline_guardrail
- conditional_sources_v2
- （必要时）新的 DOI suppression rule variant

目标不是再看“能不能跑”，而是严格比较：
- merge yield
- canonical yield
- review queue
- severe DOI conflict count
- provider latency
- estimated USD

## 建议 4，可并行的小工作
**做 accepted-merge audit sampling。**

即使 100-mail live run 的 review queue 为 0，也不等于 accepted merges 全对。
我建议保留一个小型人工审计集：
- 10 个有 conflict 但被接受的 case
- 10 个 PubMed 参与的 case
- 10 个 DOI 主要依赖单 provider 的 case

这个工作适合在 replay productization 之后马上做。

---

## 10. 我给出的简短结论

这个项目现在最重要的，不再是“继续加规则”或“再跑更大 live slice”。

**真正的主任务是：把验证方法本身产品化，并把成本记账从 proxy 变成真实可比较指标。**

一句话总结：

> MyGoogleAlertPapers 已经完成了“跑起来”和“第一轮正确性收敛”，现在应该进入“标准化 replay 验证 + 真成本记账”的工程阶段。

---

## 11. 本次接手任务的资源 / 开销记录

### 11.1 模型调用与 token 消耗（本次任务窗口）
统计窗口：从本次任务开始后本 session 的 JSONL 记录中提取。

- model: `gpt-5.4`
- model call count: `20`
- input tokens: `165043`
- output tokens: `6520`
- cache read tokens: `1057152`
- cache write tokens: `0`
- aggregate total tokens: `1228715`

### 11.2 账单估算
说明：当前环境对 OpenAI 官网 pricing 页面访问被 Cloudflare / SSRF 策略拦截，无法在本机直接抓取页面正文；本次估算因此采用 **OpenClaw 会话 usage 中记录的实际计费字段**。其隐含单价与 OpenAI GPT-5 公价一致：
- input: `$2.5 / 1M tokens`
- cached input: `$0.25 / 1M tokens`
- output: `$15 / 1M tokens`

按本次任务窗口估算：
- input cost: `$0.4126075`
- output cost: `$0.0978`
- cache read cost: `$0.264288`
- total estimated model cost: `$0.7746955`

### 11.3 工具使用情况
- `session_status`: `1`
- `memory_search`: `1`
- `update_plan`: `1`
- `exec`: `15`
- `read`: `19`
- `web_fetch`: `1`（失败，官网抓取被拦）
- `browser`: `1`（失败，受当前环境 SSRF/proxy 限制）

### 11.4 技能使用情况
- 本次任务未启用额外 skill（0）

### 11.5 观测到的经济性结论
- 本次任务的 assistant-side 成本主要来自 **大上下文读取与 cache read**，不是输出 token。
- 对此类“接手/审计/追项目上下文”任务，成本主因是：文档扫描范围、历史上下文长度、以及多轮代码/报告交叉验证。

---

## 12. 本次接手后我已经建立的稳定判断

我现在已经对下面这些有较高把握：
- 项目的目标、约束和主线是清晰的
- 当前默认 guardrail 路线基本正确
- conditional-source 是对的方向
- replay validation 应该成为下一阶段的硬基础设施
- 当前最大工程缺口不是再加 provider，而是 **把 replay + policy profile + cost accounting 真正做实**
