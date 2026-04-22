# MyGoogleAlertPapers 当前编程计划（吸收 Her 版后的执行版，2026-04-15）

## 1. 计划定位

这不是新的战略分析文档，而是接下来准备执行的**编程实施计划**。

它建立在三份已有结论之上：

- `docs/17-project-catchup-and-next-step-report-2026-04-15.md`
- `docs/18-current-problems-solutions-and-phased-blueprint-2026-04-15.md`
- `docs/19-her-branch-analysis-and-integration-report-2026-04-15.md`

总原则不变：

> 以当前主项目的 validation-first 主线为骨架，吸收 Her 版在 P0 漏损修复、provider 实验意识、输入层解耦、OA 增强方面的有益部分，但不直接吸收其尚未严谨化的成本实现和脆弱 instrumentation。

---

## 2. 新补录的执行约束

以下两条是本轮计划中新增、且应明确执行的约束。

### 2.1 记账优先记录“付费 LLM token”，而不是泛化资源占用

本项目后续确实可能引入 LLM，用于：

- 难例文章判别
- merge / review 边界案例裁决
- 文献阅读理解与结构化整理
- 其他需要模型推理的辅助环节

因此，记账系统的首要目标应是：

> **优先支持对付费 LLM 调用的 token 与费用记账。**

落实原则如下：

1. 如果当前阶段没有实际发生付费 LLM 调用，则**不强行记录 token 成本**。
2. 当前阶段不把“存储空间占用”“数据库体积”“响应字节数”之类指标当作核心记账目标。
3. 非 LLM provider 的资源统计可以保留为次级运营指标，但不应喧宾夺主，不应污染主账本语义。
4. `cost_event` 的正式演化方向，应优先兼容未来的 LLM token / cost accounting，而不是为字节流量代理指标服务。

换句话说：

- **主账本关注 paid LLM tokens / USD**
- **非 LLM provider 先记录 request_count / latency 即可**
- **字节、存储体积不是当前阶段优先项**

### 2.2 Unpaywall 可以纳入，但必须作为待验证策略对象

Unpaywall 不应被先验地视为“应当纳入主链路”的既定事实。

更合适的原则是：

> **Unpaywall 可以进入候选方案池，但它的优先级、有效性、真实边际收益，必须通过实验验证决定。**

落实原则如下：

1. Unpaywall 暂定为 **optional / experimental / OA-enhancement provider**。
2. 不直接把它提升为核心 bibliographic authority。
3. 它是否保留、在哪一层触发、是否默认启用，应由 replay / comparison 结果决定。
4. 对 Unpaywall 的评价重点不是“它能不能返回东西”，而是：
   - 是否提升最终可用信息质量
   - 是否增加 OA link / access value
   - 是否引入额外冲突或噪音
   - 是否值得其调用成本与复杂度

---

## 3. 当前主线目标

当前不是继续“加功能”的阶段，而是先把系统推进到：

**可比较、可验证、可修复、可为未来 LLM 记账留接口** 的状态。

因此本阶段目标定义为：

> 先完成 replay validation 闭环和 P0 正确性修复，再把 provider 比较与 Unpaywall 纳入标准实验框架，最后才进入更激进的性能优化与扩展。

---

## 4. 实施顺序总览

## Phase A，立即执行：验证闭环 + P0 正确性修复

目标：让当前主项目获得一个可信的比较基座，并修复已明确的 candidate 漏损问题。

### A1. Replay workflow closure

实施内容：

1. 让 `scripts/replay_validation.py` 真正把 `--policy-profile` 注入运行时配置。
2. 让 enrich 阶段按 profile 生效：
   - provider enable / disable
   - 条件触发规则
   - provider routing / query policy
3. 让 merge 阶段按 profile 生效：
   - suppression knobs
   - fallback knobs
   - 相关 merge policy 选项
4. replay reset 时严格清理 `query_cache`。
5. 统一 replay 输出格式：
   - JSON summary
   - Markdown report

交付结果：

- replay workflow 从“半自动脚本”升级为“可信比较工具”

### A2. DOI clean

实施内容：

1. 在 normalize 阶段实现 DOI 后缀清洗。
2. 重点覆盖已知脏 DOI 模式：
   - `.pdf`
   - `/download`
   - `_reference.pdf`
   - 类 Oxford 深路径 PDF 尾巴
3. 为清洗逻辑补测试。

交付结果：

- dirty DOI 不再继续污染 downstream enrich / merge

### A3. all-unmatched candidate fallback proposal

实施内容：

1. 修改 merge 逻辑，避免 candidate 因所有 `source_record.matched=0` 而静默消失。
2. 对这类 candidate 生成 **normalized-only fallback proposal**。
3. 在 proposal 或 trace 中显式标注其 provenance / low-confidence 属性。
4. 为该路径补测试。

交付结果：

- normalized candidate 不再在 merge 前无声蒸发
- 66 条漏损类问题被制度化修复

### A4. same-batch replay comparison

在 A1-A3 完成后，执行严格 same-batch replay，对照 baseline 与 treatment。

最低比较指标：

- normalized count
- merged proposal count
- canonical count
- review queue count
- canonical_blocked count
- normalized-only fallback proposal count
- dirty DOI repaired count
- request_count / latency（非 LLM provider）
- paid LLM token / estimated USD（若本轮实际发生，否则显式记为“未发生”）

交付结果：

- 一份可解释的 baseline vs treatment replay 报告

---

## Phase B，随后执行：provider 比较正式化

目标：把 Her 版的 provider 实验意识，升级成标准化策略评估能力。

### B1. Provider experiment harness 正式化

实施内容：

1. 把当前零散实验升级为标准 comparison harness。
2. 比较对象不只包括命中率，还包括：
   - canonical 增益
   - review 变化
   - blocked case 变化
   - accepted merge audit 样本表现
   - wall-clock
   - request_count / latency
   - 若涉及 LLM，则记录 paid tokens / cost

### B2. Unpaywall 实验接入

实施内容：

1. 将 Unpaywall 作为 **experimental provider profile** 纳入比较。
2. 其定位先限定为：
   - OA status / landing page / access enhancement
   - 而非核心 merge authority
3. 通过 profile-level comparison 判断：
   - 是否值得保留
   - 是否默认启用
   - 触发条件应如何收窄或放宽

交付结果：

- Unpaywall 的位置由实验决定，而不是凭直觉决定

---

## Phase C，中程执行：审核与输入层解耦

目标：增强系统的人机协同和复现能力。

### C1. accepted-merge audit export

实施内容：

1. 导出已接受 merge 中的高风险子集。
2. 支持按以下条件抽样或导出：
   - conflict but accepted
   - DOI from single provider
   - PubMed involved
   - preprint / journal ambiguity

### C2. `import-eml` / 输入层解耦

实施内容：

1. 增加 `import-eml` 或等价离线入口。
2. 让 ingest 能由 IMAP 之外的数据源驱动。
3. 为 validation / replay / regression 测试提供更稳定输入。

---

## Phase D，后续执行：性能优化与正式成本系统

目标：在验证基础设施稳定后，再做更激进的性能和记账升级。

### D1. enrich 并行化

前提：必须在 replay substrate 稳定之后再做。

实施内容：

1. 评估 Crossref / OpenAlex / optional provider 的并行化。
2. 保证并行后缓存行为、结果归因、异常处理仍可解释。

### D2. 正式成本系统

实施原则：

1. 优先为未来 LLM 使用做 paid-token accounting。
2. 非 LLM provider 先保留 request_count / latency 的运营指标。
3. 不用 token 字段去装 bytes。
4. 不采用全局 monkey patch 方式做资源归因。
5. 若以后确有必要，再单独设计 provider 级资源字段或表。

---

## 5. 明确不做的事项（当前阶段）

以下内容当前明确**不直接纳入主线实施**：

1. 不直接吸收 Her 版的全局 `urllib` monkey patch。
2. 不直接吸收“bytes 伪装 token”的成本记录方式。
3. 不把存储空间占用、数据库体积等作为当前核心记账指标。
4. 不在 replay 基础设施未闭环前把并行 enrich 提为最高优先级。
5. 不先验认定 Unpaywall 应成为默认核心 provider。

---

## 6. 当前待批准的最小执行包

如果现在开始执行，我建议先只做 **Package A**，范围保持严格收敛：

1. replay workflow closure
2. `query_cache` strict reset
3. DOI clean
4. normalized-only fallback merge proposal
5. same-batch baseline vs treatment replay report

这一步暂时**不**做：

- Unpaywall 主线接入
- enrich 并行化
- 正式 LLM token 账本的完整实现
- 输入层大改造

但会在设计上为后续两件事留好接口：

- paid LLM token accounting
- Unpaywall profile-based evaluation

---

## 7. 批准后执行方式

若批准，我将按以下顺序直接实施：

1. 先做代码接线与测试
2. 再做 replay 对照运行
3. 然后写本轮实施报告到 `docs/`
4. 最后汇总：
   - 结果变化
   - 新增风险
   - token / 成本记录情况（若本轮未发生 LLM 调用，则明确写明未发生）

---

## 8. 一句话版

当前编程计划的最简表达是：

> 先把 replay 验证底座和 P0 漏损修复做实，把 paid LLM token accounting 作为后续正式记账主目标预留接口，把 Unpaywall 作为必须经实验验证的候选策略对象，而不是直接默认吸收进主链路。
