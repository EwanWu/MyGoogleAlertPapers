# Her 版系统分析、路线比较与综合继承方案（2026-04-15）

## 1. 任务目标

本报告面向 `~/NewCareer/Hermes_TEST/MyGoogleAlertPapers`（以下简称 Her 版）与当前主项目 `~/NewCareer/Openclaw/proj/MyGoogleAlertPapers` 的系统比较，目标是回答四个问题：

1. Her 版到目前为止到底在试图解决什么问题。
2. 它已经形成了哪些文档、分析框架、代码改动和工程假设。
3. 它与当前主项目相比，哪些方向更强，哪些方向更弱，哪些结论尚未被严格证明。
4. 应如何对二者做“路线综合、批判继承、吸收有益部分”，形成下一阶段更稳健的主路线。

---

## 2. 本次实际检查范围

### 2.1 Her 版工作树状态

- 路径：`~/NewCareer/Hermes_TEST/MyGoogleAlertPapers`
- 当前分支：`feature/provider-experiment`
- git 状态显示：
  - 已修改未提交：
    - `src/mygooglealertpapers/cost/tracker.py`
    - `src/mygooglealertpapers/enrich/semanticscholar.py`
    - `src/mygooglealertpapers/pipeline/cost_stats.py`
    - `src/mygooglealertpapers/pipeline/enrich.py`
  - 未跟踪文件：
    - `data/enrich_run200.log`
    - `data/provider_experiment_results.json`
    - `docs/17-run200-analysis-and-optimization-plan.md`
    - `docs/18-technical-meeting-briefing-2026-04-13.md`
    - `docs/validation/package3-guardrail-100-detailed-analysis.md`
    - `docs/validation/package3-guardrail-100-validation.md`
    - `scripts/provider_experiment.py`
    - `src/mygooglealertpapers/enrich/unpaywall.py`

### 2.2 关键文档与代码

重点阅读/核查了以下 Her 版材料：

- `docs/17-run200-analysis-and-optimization-plan.md`
- `docs/18-technical-meeting-briefing-2026-04-13.md`
- `data/provider_experiment_results.json`
- `scripts/provider_experiment.py`
- `src/mygooglealertpapers/enrich/unpaywall.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/cost/tracker.py`
- `src/mygooglealertpapers/pipeline/cost_stats.py`
- `src/mygooglealertpapers/enrich/semanticscholar.py`

同时对照了当前主项目中的：

- `docs/16-validation-infrastructure-blueprint-2026-04-12.md`
- `docs/17-project-catchup-and-next-step-report-2026-04-15.md`
- `docs/18-current-problems-solutions-and-phased-blueprint-2026-04-15.md`
- `scripts/replay_validation.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/pipeline/merge.py`
- `src/mygooglealertpapers/cost/tracker.py`
- `src/mygooglealertpapers/pipeline/cost_stats.py`
- `config/policy_profiles/conditional_sources_v2.yaml`

### 2.3 额外验证

- Her 版测试：`PYTHONPATH=src python3 -m pytest tests -q` 通过。
- Her 版 `data/mgap_run200.db` 统计核查：
  - raw mail: 203
  - scholar alert: 130
  - candidate: 486
  - source_record: 1874
  - merged proposal: 420
  - canonical: 324
  - review queue: 11
  - all-unmatched candidate: 66
  - dirty DOI (`.pdf` / `/download`): 21

---

## 3. Her 版的核心设计主线

Her 版不是在做“重新发明一个系统”，而是在现有 pipeline 基础上，围绕一次 **200 封邮件真实运行** 的经验结果，推动一个更偏“实验优化型”的分支。

其设计主线可以概括为一句话：

> 用一次较大规模 live run 暴露 pipeline 的真实瓶颈，然后围绕 provider 组合、DOI 质量、merge 漏损、性能和成本做经验驱动的修补与优化。

更具体地说，Her 版的世界观是这样的：

1. **当前系统已经可跑，不再是纯规划问题。**
2. **真正的问题在运行时漏损、provider ROI 不均、串行性能过慢。**
3. **应优先根据实测数据做局部修补，而不是继续抽象层面的宏观规划。**
4. **provider 不是越多越好，而是应分层、条件化、可比较。**
5. **成本与资源占用要开始记，但它采用的是“先用可获得代理指标顶上”的实验性做法。**

这是一个很典型的“现场工程师”路线，优点是问题感强、落点具体，缺点是容易把一次 live run 的观察，过快上升为系统级结论。

---

## 4. Her 版文档所表达的主要判断

## 4.1 `docs/17-run200-analysis-and-optimization-plan.md` 的价值

这是 Her 版最有内容、也最有价值的文档。它不是泛泛路线图，而是建立在 `data/mgap_run200.db` 统计上的“问题分级 + 修复建议”文档。

它给出的关键判断基本有五类。

### A. 识别了一个真实的 P0 数据漏损问题

Her 版指出：

- 486 个 normalized candidate 中，只有 420 个 merged proposal。
- 缺失的 66 个 candidate，其所有 `source_record` 都是 `matched=0`。
- 现有 merge 逻辑只处理 `matched=1` 的 source，导致这些 candidate 被静默跳过。

这个判断是对的，而且非常重要。

它不是“指标不好看”的问题，而是 **系统性 recall 漏损**。这意味着当前系统并非只是有 review queue 或 conflict，而是会让一部分候选在 merge 前直接蒸发。

### B. 识别了 dirty DOI 是上游关键病灶之一

Her 版从数据库中指出约 10.7% 的 DOI 含 `.pdf`、`/download` 等尾巴，导致 provider 查询失败，再沿链条造成全 provider no-match，最终落入前述 66 条漏损。

这个因果链条是合理的：

`dirty DOI -> 查询失败 -> 全 matched=0 -> merge 跳过 -> 候选丢失`

这比泛泛而谈“DOI 提取质量要提升”更强，因为它把上游解析错误和下游 recall 漏损连起来了。

### C. 它把 provider 看成可比较的资源组合，而不是神圣固定配置

Her 版对 provider 命中率和延迟的关注非常强，结论包括：

- Crossref / OpenAlex 是主力。
- Semantic Scholar 命中弱。
- Europe PMC 只在 PMID 驱动时靠谱，title 模糊搜索性价比低。
- OpenAlex 批量 DOI 查询存在稳定性问题。

这条思路的价值不在于每个结论绝对正确，而在于它引入了一个很必要的框架：

> provider 选择应该是经验型、可验证、可切换的策略问题。

### D. 它非常敏感地抓住了 enrich 串行性能瓶颈

Her 版发现总耗时 58.3 分钟中，enrich 占 93.6%。

这一点基本也成立。它将焦点从 merge / dedup / parse 转移到 enrich，是符合当前阶段主要矛盾的。

### E. 它开始把“输入源解耦”当作工程问题

Her 版提出 `import-eml`，本质上是在说：

- IMAP 不应是整条链路的强耦合入口；
- 真正需要的是把 ingest 输入层做成可替换；
- 这样 validation、debug、回放、重现实验都会简单很多。

这个方向是对的，而且和当前主项目的 validation/replay 路线并不冲突，反而高度兼容。

## 4.2 `docs/18-technical-meeting-briefing-2026-04-13.md`

该文件当前是空文件。

这意味着 Her 版虽然命名上像“技术汇报”，但并没有形成第二份独立的高质量策略文档。实际的内容重心基本还是 `docs/17-run200-analysis-and-optimization-plan.md` 与若干实验文件。

---

## 5. Her 版代码改动的实质含义

Her 版当前真正的代码改动，并不多，但反映出很明确的工程偏好。

## 5.1 `unpaywall.py`：引入 DOI-only 的 OA 补充源

新增 `src/mygooglealertpapers/enrich/unpaywall.py`，实现基于 DOI 的 Unpaywall 查询。

它提供的信息主要是：

- `is_oa`
- `oa_status`
- OA landing page / PDF URL
- title / venue / year
- 少量作者字符串
- 可能的 PMID / PMCID

### 我对这个改动的判断

**优点：**

- 目标明确，不是和 Crossref/OpenAlex 完全重复造轮子。
- 它引入的是“开放获取状态/链接”这个当前主链路中相对薄弱的元数据维度。
- 对后续全文抓取、附件访问、优先阅读可能有实际价值。

**局限：**

- 它不是一个强 merge provider。
- 不提供 abstract，作者字段也弱。
- 在当前系统阶段，它更像“附加 enrichment”，而不是决定 canonical 正确性的核心来源。
- 若直接把它和 Crossref/OpenAlex 同级看待，会高估其对主任务的贡献。

### 结论

Unpaywall 值得吸收，但应被定位为：

> OA/链接增强源，而不是核心书目信息主源。

## 5.2 `scripts/provider_experiment.py`：建立小样本 provider 对照实验习惯

该脚本以 30 个 clean DOI candidate 为样本，对比 Unpaywall 与现有 provider。

从结果文件与复算统计看：

- 样本数：30
- Unpaywall 命中：25/30（83.3%）
- Semantic Scholar 命中：9/30（30.0%）
- Crossref 命中：25/30（83.3%）
- OpenAlex 命中：24/29（82.8%）
- Unpaywall 平均延迟：1409ms
- Semantic Scholar 平均延迟：1438ms
- OA 数：13/30
- 有 OA PDF：1/30

并且 overlap 上主要是：

- `crossref + openalex + unpaywall`：15
- `crossref + openalex + semanticscholar + unpaywall`：9
- 完全无命中：5

### 我对该实验的判断

**它有用，但不是最终证据。**

它说明三件事：

1. Unpaywall 作为 DOI-only source 是可用的。
2. 它比 Semantic Scholar 更贴近当前 DOI 驱动场景。
3. 它带来的主要增益是 OA 状态/链接，不是核心元数据覆盖革命。

但这个实验也有明显局限：

- 只抽了 30 条。
- 只看 clean DOI，绕开了当前最大病灶之一 dirty DOI。
- 只比较 provider 命中和字段覆盖，没有嵌入整条 merge/dedup/canonical 结果。
- 没有问“引入 Unpaywall 后 canonical 数、review 数、quiet error 数到底变化多少”。

### 结论

这个脚本应保留，但应从“证明应该加 Unpaywall”改造为：

> 一个标准化 provider 评估 harness，用于比较 provider 对最终 pipeline 输出的真实边际贡献。

## 5.3 `cost/tracker.py` + `pipeline/enrich.py`：把字节流量硬塞进 token/cost 框架

这是 Her 版最值得警惕的改动。

它做了几件事：

1. 在 `enrich.py` 中 monkey-patch `urllib.request.urlopen`，记录请求和响应字节数。
2. 用 `BytesTracker` 暂存每个 provider 的字节量。
3. 在 `CostTracker.record_stage_cost()` 里，把：
   - `tokens_prompt = request_bytes`
   - `tokens_completion = response_bytes`
   - `tokens_total = total_bytes`
4. 再用一个粗糙公式估算：
   - `$0.01 / MB`

### 这条思路的问题

#### 问题 1：语义污染

数据库 schema 中的 token 字段本来表达 token，不该被重定义成 bytes。

这会带来两个后果：

- 统计报表会在语义上误导人；
- 后续如果真要接入 token/billing 统计，会和现有数据混淆。

#### 问题 2：成本模型并不真实

公共 scholarly API 的主要成本往往不是“按流量线性计费”。

很多 provider：

- 免费但限速；
- 以配额/政策约束为主；
- 或者需要把运营成本和用户实际货币成本分开看。

因此 `$0.01/MB` 更像一个随手设定的资源 proxy，不是 monetary accounting。

#### 问题 3：全局 monkey patch 很脆弱

`urllib.request.urlopen` 全局 patch 有明显工程风险：

- 对并发不安全；
- 对 provider 归属不严格；
- 对 batch 查询可能归因错误；
- 读取 response 全量后再包回 `addinfourl`，会影响流式行为与调试语义；
- 如果以后 provider 不都走 urllib，该方案会出现体系断裂。

#### 问题 4：当前 tracker 设计并不适合作为长期观测基础设施

它更像一次实验中为了快速得到“MB 级资源量级”而加的临时探针，而不是正式成本系统。

### 结论

Her 版在“我要先记资源量”这个方向上是对的，但当前实现 **不应直接并入主线**。

正确吸收方式应是：

- 保留“资源统计要做”的动机；
- 放弃“用 token 字段装 bytes + 伪美元计费”的实现；
- 改为建立独立字段或独立表，明确区分：
  - request_count
  - latency
  - bytes_in / bytes_out
  - provider_quota_cost
  - estimated_usd（仅在有真实价格表时）

## 5.4 `pipeline/cost_stats.py`：报表增强是对的，底层口径不对

Her 版把 cost stats 扩展到：

- total request bytes
- total response bytes
- total transfer
- per-provider transfer
- estimated cost

**报表方向是合理的。**

但由于底层成本口径不对，所以报表也只能当作“实验性资源摘要”，不能当正规财务/账单视图。

## 5.5 `pipeline/enrich.py` 中对 `semanticscholar.py` 的改动

Her 版在 `semanticscholar.py` 中增加了一句注释，并确保 `urllib.request.urlopen` 的模块级引用可以被 monkey-patch 捕获。

这说明 Her 版的修改是为了让“字节追踪钩子”生效，而不是在改善 Semantic Scholar 本身的匹配逻辑。

换言之，这个改动本身没有产品逻辑价值，只是配合其资源追踪实验。

---

## 6. Her 版相对当前主项目，强在哪里

## 6.1 强在“从真实运行中抓问题”

Her 版最强的地方，是它不是停在抽象路线图，而是从 200-mail 真实运行中直接抓出了：

- 66 条 candidate 漏损
- 21 条 dirty DOI
- provider ROI 不均
- enrich 串行瓶颈
- IMAP 强耦合

这些都不是虚问题。

## 6.2 强在“provider 组合优化”意识更强

当前主项目已经进入 validation infrastructure 思维，但 Her 版更激进地把 provider 视为可裁剪、可替换、可对照的对象。

这对于后续做：

- source policy profile
- treatment vs baseline
- provider ROI 分析
- conditional routing

很有启发价值。

## 6.3 强在“输入层解耦”意识更清楚

Her 版提出 `import-eml`，这个方向很实用。

它能直接服务于：

- 回放验证
- 离线复现实验
- 无邮箱权限条件下的调试
- 数据集化

## 6.4 强在工程直觉上更果断

Her 版敢做快速实验，例如：

- Unpaywall provider probe
- byte-level traffic estimation
- provider-specific comparison harness

虽然并不都适合直接主线吸收，但它们帮助暴露了值得正式化的需求。

---

## 7. Her 版相对当前主项目，弱在哪里

## 7.1 弱在“缺乏严格验证闭环”

当前主项目最核心的成熟点，不是代码更多，而是已经开始形成：

- replay validation blueprint
- baseline/treatment 对照思维
- same-batch comparison 约束
- guardrail baseline
- review/canonical/cost 联合观察框架

Her 版虽然问题感强，但很多结论来自一次 live run，缺少严格的可重复比较基线。

这意味着它善于发现问题，但还不够善于证明“某个改动真的解决了问题且没有引入新偏差”。

## 7.2 弱在“把局部 proxy 过快制度化”

最典型的就是 byte-based cost hack。

这不是不能做，而是不能假装它已经是“真实 cost accounting”。

## 7.3 弱在“性能优化优先级略前置”

Her 版很想尽快并行化 enrich，这个方向长期没问题。

但在当前阶段，如果 replay substrate 还没关上、policy 注入还不标准、query cache reset 还不严格，那么过早并行化会让实验更难解释。

也就是说：

- 并行化是重要的，
- 但不应先于 validation closure 成为主线最高优先级。

## 7.4 弱在“部分关键问题只诊断未落地”

Her 版最重要的两个修复想法：

- DOI clean
- merge fallback for all-unmatched

目前主要停留在分析和计划中，尚未成为真正落地、可回放验证的主干代码。

也就是说，它提出了正确的问题，但还没把这些问题变成系统工程资产。

---

## 8. 当前主项目相对 Her 版，强在哪里

当前主项目的优势不在“更激进”，而在“更像一个正在形成实验基础设施的主干系统”。

### 8.1 更强的阶段判断

当前主项目已经明确：项目不是 planning-only，而是 **late prototype / early hardening / validation infrastructure transition**。

这个判断比 Her 版更准确，因为它不再把主要矛盾定义为单点优化，而是定义为：

> 缺的是可重复、可比较、可解释的验证底座。

### 8.2 更强的 validation 路线

主项目已经明确下一优先级是：

- same-batch replay
- policy profile 注入
- replay reset contract 完整化
- standardized outputs

这条路线虽然没 Her 版那样“立刻修一个问题很爽”，但它更能决定后续所有优化是否可信。

### 8.3 更强的 guardrail / review 框架意识

主项目已经把“review queue、canonical blocked、conflict grading”作为可靠性框架的一部分，而不是单纯追求 canonical 数量上涨。

这在科学文献 pipeline 中非常关键，因为“多合并出来几条”并不自动等于“更正确”。

### 8.4 更强的成本核算方向判断

主项目已经识别到：

- 当前 cost_event 基本还是 schema 占位；
- 真正需要的是 provider pricing config + request_count + estimated_cost_usd 的正式化；
- 不能把实验性代理指标误当成正式 monetary accounting。

---

## 9. 二者综合后的核心判断

我对两条路线的综合结论是：

> 主项目的主线判断更正确，Her 版的问题抓取更锋利。

换句话说：

- **主项目更适合做 trunk。**
- **Her 版更适合做 problem-discovery / tactical-innovation feeder branch。**

因此，不应“拿 Her 版替换主项目路线”，也不应“完全忽略 Her 版”。

正确做法是：

> 以主项目的 validation-first 主线为骨架，吸收 Her 版在 DOI 清洗、all-unmatched fallback、provider 评估、输入源解耦、OA 增强上的具体洞见。

---

## 10. 我主张吸收的部分

## 10.1 立即吸收：DOI 清洗问题定义

Her 版对 dirty DOI 的问题定义是具体且可操作的，应直接纳入主线近期任务。

这部分值得吸收的不是某个正则原样文本，而是：

- 把 dirty DOI 明确视为 recall bug；
- 在 normalize 阶段尽早处理；
- 将其纳入 replay validation 的对照指标。

## 10.2 立即吸收：all-unmatched candidate 不能静默消失

Her 版对 66 条漏损的诊断非常关键。

当前主线应吸收这一点，并把它升级为明确规则：

> 只要有 normalized candidate，就不允许因“所有 source matched=0”而在 merge 处无声蒸发。

但这里要注意，吸收的是 **产品规则**，不是随手插一个 fallback patch 就结束。

应当把它设计成：

- 低置信度 proposal
- 明确标记 provenance 为 normalized-only fallback
- 可在 validation/report 中单独统计

## 10.3 吸收：provider experiment harness 思路

`scripts/provider_experiment.py` 的价值在于它提供了一个模板。

应吸收为：

- 标准 provider ablation / ROI experiment harness
- 但输出指标要从“命中率”提升到“最终 canonical/review/blocked/accepted merge quality”

## 10.4 吸收：Unpaywall 作为 OA enhancement source

可以吸收，但定位要降一级：

- 不是 core bibliographic authority
- 而是 OA / full-text accessibility enhancement layer

更合适的用途是：

- canonical 已建立后，补 OA status / best link / PDF link
- 为后续下载、阅读、全文处理服务

## 10.5 吸收：EML/import 解耦方向

Her 版提出的 `import-eml` 值得进入中短期路线。

它与 replay validation 并不冲突，反而能增强 replay 与 reproducibility。

---

## 11. 我主张拒绝或改造后再吸收的部分

## 11.1 不应直接吸收：字节伪 token 成本系统

`cost/tracker.py` 当前实现不应直接进入主项目。

应改造为：

- 单独资源指标字段/表
- token 仍是 token
- bytes 仍是 bytes
- price 仅在有真实 pricing 配置时计算

## 11.2 不应直接吸收：全局 urllib monkey patch

原因：

- 对并发和 batch 都脆弱
- 归因不可靠
- 维护性差

更合理做法是：

- 在 provider 客户端内部显式记录请求/响应大小
- 或封装统一 HTTP client 层

## 11.3 暂不作为最高优先级吸收：大规模并行 enrich

这件事要做，但不是现在第一个做。

正确顺序应是：

1. replay workflow closure
2. DOI clean + all-unmatched fallback
3. same-batch replay comparison
4. 再做并行化

否则很难解释性能提升是否伴随正确性/缓存行为变化。

## 11.4 暂不直接吸收：把 Unpaywall 作为替代 Semantic Scholar 的主 provider 结论

Her 版的小样本实验说明 Unpaywall 在当前 clean DOI 子集上比 Semantic Scholar 更有价值。

但这并不足以支持“一刀切替换”。

更合理的策略是：

- 保留为 profile-level option
- 在 specific use case 上比较其边际收益
- 让 replay 数据决定它该进入哪个层级

---

## 12. 综合后建议的主路线

## 12.1 总体原则

主项目未来 1 个阶段的核心目标，不应定义为“继续加 provider”或“尽快并行化”，而应定义为：

> 先把正确性修复与验证基础设施闭环做实，再把 Her 版暴露出的高价值局部修复纳入可比较实验框架，最后再推进性能和 provider 组合优化。

## 12.2 近程 Phase A：验证闭环 + P0 漏损修复

### A1. 关闭 replay workflow 缺口

- 让 `scripts/replay_validation.py` 真正注入 policy profile
- enrich/merge 真正读取 profile 生效
- replay reset 增加 `query_cache` 清理
- 规范 replay markdown/json 产出

### A2. 吸收 Her 版的两个 P0 修复

- DOI clean
- all-unmatched candidate fallback proposal

### A3. 新增关键对照指标

same-batch replay 中至少比较：

- merged proposal count
- canonical count
- review queue count
- canonical_blocked count
- normalized-only fallback proposal count
- dirty DOI repaired count

## 12.3 中近程 Phase B：provider 评估正式化

### B1. 把 Her 版 provider_experiment 思路升级

形成标准 provider comparison harness，比的不只是命中率，还要比：

- canonical 增益
- review 增减
- conflict 变化
- accepted merge audit 结果
- wall-clock
- request_count / bytes / quota / estimated cost

### B2. 将 Unpaywall 放入 enhancement profile

建议不要直接进入核心 merge authority，而是：

- 作为 optional OA enrichment
- 可在特定 profile 中启用
- 用 replay 数据决定是否保留

## 12.4 中程 Phase C：输入层与运行层解耦

- 设计 `import-eml`
- 允许 snapshot / EML 驱动 ingest
- 让 validation 不依赖 IMAP 在线连接

## 12.5 后续 Phase D：并行 enrich 与资源观测重构

- 并行化 Crossref/OpenAlex/optional provider
- 显式 HTTP client instrumentation
- 独立资源口径，不污染 token 字段
- provider pricing config / quota model

---

## 13. 最终立场

如果必须一句话总结我对 Her 版的结论，那就是：

> Her 版是一个很有价值的“经验驱动问题发现分支”，但它还不是更好的主线；真正应做的是把它发现的硬问题，纳入当前主项目已经开始形成的 validation-first 主干框架中。

更直白一点：

- **Her 版看问题更尖锐。**
- **当前主项目定主线更稳。**
- **二者综合后，最强方案不是二选一，而是“主项目做骨架，Her 版提供高价值修补件和实验线索”。**

---

## 14. 建议的直接下一步

我建议下一步进入一个明确的实施包，而不是继续停留在比较层面：

### Package A（立即执行）

1. 修 replay workflow closure
2. 加 `query_cache` strict reset
3. 实现 DOI clean
4. 实现 normalized-only fallback merge proposal
5. 产出 same-batch baseline vs treatment replay 报告

### Package B（其后执行）

1. provider experiment harness 正式化
2. Unpaywall 作为 OA enhancement profile 接入
3. accepted merge audit export
4. 真正资源/成本核算模型

如果要我给当前两条路线做一句 judgment：

> 该继承 Her 版的问题意识，不该继承它尚未严谨化的统计和成本实现；该吸收它的 P0 修复方向，不该让它取代主项目的 validation 主线。
