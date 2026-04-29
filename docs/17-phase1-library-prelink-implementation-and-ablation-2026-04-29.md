# Phase 1 exact library prelink：实现落地与对照实验（2026-04-29）

## 结论先行

Phase 1 已不再是蓝图，而是**已落地、已测试、已做 live 对照验证**的功能层。

当前固定推进结论：

1. **继续把 `exact library-first prelink` 作为本阶段主线。**
2. **不要回退到“先 enrich 再看能不能认出来”** 的旧路径；这在已有 library 存在时会无意义重打大量 provider 请求。
3. **当前证据已经足够支持把 Phase 1 视为正式推进方案，而不是探索性分支。**

---

## 本次真正落地了什么

### 1. schema / data model

已新增并接入：

- `candidate_resolution_status`
- `paper_identity_alias`

并补充了配套索引，以及 `paper_candidate_normalized` 上若干 identifier / alias 字段索引，用于 prelink lookup。

### 2. repository 层

已新增：

- candidate ↔ paper link upsert
- candidate resolution status upsert
- canonical exact-id lookup
- alias lookup / alias upsert
- 从既有 `candidate_paper_link + paper_candidate_normalized` 回填 alias 的辅助逻辑

同时 `Repository.connect()` 已确保在连接已有 DB 时自动补 schema，使历史 DB 可直接参与 Phase 1 实验。

### 3. pipeline 层

已新增模块：

- `src/mygooglealertpapers/pipeline/candidate_resolution.py`

当前实现的是 **Phase 1 exact library-first short-circuit**：

- 先查 `doi / pmid / pmcid`
- 再查 alias 型 exact key：`arxiv / scholar_cluster / canonical_url`
- 命中后直接写入：
  - `candidate_paper_link`
  - `candidate_resolution_status`
- 并在后续 `enrich` / `merge` 中跳过这些 candidate

### 4. runtime / CLI / profile

已接入：

- `runtime_rules.library_prelink_enabled`
- 新 CLI：`resolve-candidates`
- control profile：
  - `config/policy_profiles/openalex_batching_identifier_plus_title_core_no_library_prelink.yaml`

### 5. enrich / merge 联动

- `enrich_candidates(...)` 已在 provider dispatch 前执行 library prelink
- `merge_metadata(...)` 已跳过已 prelink 的 candidate
- enrich dispatch summary 已暴露 prelink 相关统计

### 6. 测试

新增并通过：

- DOI exact prelink 可直接跳过 provider dispatch
- arXiv alias 可通过既有 link 回填 alias 后命中
- prelinked candidate 不再进入 merge proposal

并重新跑过全量 `pytest tests -q`，结果通过。

---

## 这次对照实验怎么做的

### 设计

为了测“已有 library 存在时，Phase 1 到底能省多少”，我做的是最贴近真实复投场景的实验：

- **历史库**：`data/mgap_mainline_treat_20260422_mainline.db`
- **新进候选来源**：`data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- 把 seed 中前一批候选注入历史库，作为“新收到、但可能其实库里已经有”的 incoming candidate
- 新 candidate 统一加前缀 `phase1_150_`

### control / treatment

两组保持相同 lane shape：

- `enabled_lanes = [identifier_fastpath, title_core]`

唯一差异：

- **control**：关闭 `library_prelink_enabled`
- **treatment**：开启 `library_prelink_enabled`

### 实际运行命令

都跑：

- `enrich-candidates --limit 10000`
- `merge-metadata --limit 10000`
- `dedup-candidates --limit 10000`

---

## 对照结果

完整 JSON：

- `docs/validation/day6-phase1-library-prelink-ablation-150-20260429.json`

### treatment（开启 library prelink）

- incoming candidate count: **155**
- library prelinked candidate count: **149**
- prelink hit ratio: **96.1%**
- planned provider intents: **611**
- prelink-skipped provider intents: **585**
- runnable provider intents: **3**
- dispatch groups: **2**
- dispatch requests: **2**
- enrich duration: **6008 ms**
- merge duration: **14 ms**
- dedup duration: **10 ms**

prelink 规则命中构成：

- `url_canonical_exact`: **78**
- `doi_exact`: **63**
- `pmid_exact`: **3**
- `pmcid_exact`: **3**
- `arxiv_exact`: **2**

### control（关闭 library prelink）

control 是负对照。它的差距在运行中已经足够明显，所以我在结论已成立后停止了它，避免无意义继续烧 provider 时间。

在停止前已经观察到：

- incoming candidate count: **155**
- library prelinked candidate count: **0**
- planned provider intents: **611**
- runnable provider intents: **588**
- dispatch groups: **270**
- 已实际发出的 dispatch requests（下界）: **132**
- 已处理 runnable intents（下界）: **275**
- 已运行时间（下界）: **418854 ms**（约 **6m 59s**）
- 且此时**仍未完成**

lane 观察：

- `identifier_fastpath`: 112 groups
- `title_core`: 158 groups
- 已发出的 title-core requests（下界）: **127**

---

## 怎么解释这个结果

### 1. Phase 1 不是“小优化”，而是量级变化

对同一批 incoming candidates：

- runnable intents：`588 -> 3`
- dispatch groups：`270 -> 2`
- 已发 requests：`>=132 -> 2`
- wall time：`>418.854s -> 6.008s`

也就是说：

- runnable-intent reduction ≈ **99.49%**
- dispatch-group reduction ≈ **99.26%**
- request reduction（按已发下界算）≥ **98.48%**
- wall-time speedup（按已观测下界算）≥ **69.7x**

这是**阶段性架构收益**，不是小修小补。

### 2. 最大收益来自“文章级短路”，不是 query cache 本身

之前已经知道 query cache 能挡住“同 provider + 同 query key”的重复请求。

这次证据更明确：

> 真正缺的是 **provider query 之前的 article-level resolution**。

也就是：先判断“这篇文章库里其实已经有了”，再决定是否还要去打 provider。

### 3. exact prelink 的 precision / ROI 很高

本阶段只用了强确定性键：

- DOI / PMID / PMCID
- arXiv
- canonical URL
- scholar cluster

这比直接上 fuzzy global title-linking 风险低很多，ROI 却已经非常高。

---

## 当前固定蓝图（请视为本阶段正式推进方案）

这一段是刻意固化的，避免后面漂移：

### Phase 1（现在）

**目标：先把 exact library-first short-circuit 做扎实。**

固定工作包：

1. 保持 `candidate_resolution_status` / `paper_identity_alias` / `candidate_paper_link` 这套结构不回退
2. 继续验证 exact prelink 在不同历史库 / 批次上的稳定性
3. 让 prelinked candidate 在后续 merge / dedup / replay 汇总里有更完整统计
4. 进一步审计剩余未命中的 6 个 candidate，确认它们为何没能 exact prelink

### Phase 2（下一步）

**same-batch candidate clustering**

目标是解决“同一批里多个 candidate 其实指向同一篇文章，但在 pre-dedup 之前尚未合流”的问题。

### 暂不做

- 不做 fuzzy global title-only auto-prelink
- 不把弱 title+author 规则直接升级为 production short-circuit
- 不把这个阶段重心重新拉回 broad matching policy churn

---

## 这次实验对后续 runtime 策略的影响

当前推荐顺序已经更清楚了：

1. **先做 library prelink**
2. 对剩余 unresolved candidate 再走 `identifier_fastpath`
3. 再走 `title_core`
4. 更慢的 fallback 继续保持非默认 / 单独预算控制

换句话说：

> 现在的 enrich runtime 不应只理解为“lane scheduling 问题”，还应理解为“先把可直接短路的 candidate 从 lane 系统里移除”。

这两层现在开始形成真正组合：

- 上层：`library prelink`
- 下层：`provider lanes + budgets`

---

## 产物索引

代码：

- `src/mygooglealertpapers/pipeline/candidate_resolution.py`
- `src/mygooglealertpapers/db/schema.py`
- `src/mygooglealertpapers/db/repository.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/pipeline/merge.py`
- `src/mygooglealertpapers/pipeline/enrich_stats.py`
- `src/mygooglealertpapers/cli.py`
- `src/mygooglealertpapers/config.py`

profile：

- `config/policy_profiles/openalex_batching_identifier_plus_title_core_no_library_prelink.yaml`

测试：

- `tests/test_candidate_resolution.py`

实验：

- `docs/validation/day6-phase1-library-prelink-ablation-150-20260429.json`

蓝图 / 档案：

- `docs/16-duplicate-provider-query-elimination-plan-2026-04-29.md`
- `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md`

---

## 一句话阶段判断

**Phase 1 exact library prelink 已经被证明值得继续深挖。**

它不是“可能有帮助”，而是已经在真实历史库场景下表现出**接近两位数量级的同步请求压缩能力**，应作为接下来这个阶段的固定主线继续推进。
