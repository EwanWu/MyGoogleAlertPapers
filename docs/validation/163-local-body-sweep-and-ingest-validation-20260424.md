# 163 本机 body sweep + early-ingest 验证 memo（2026-04-24）

## 结论

本轮 163 Windows-local body sweep 已达到当前项目定义下的“可接入资料库”标准，并且证据已从单封 / 19 封 smoke test 扩展到 **21 页、1878 封正文的全量 early-ingest 验证**。

按当前项目边界，“接入资料库”定义为：
- 正文能稳定进入现有 SQLite schema 的早期层，尤其是 `mail_ingestion_record` 与 `raw_mail_snapshot`
- 后续 `parse-mails` 与 `normalize-candidates` 可正常产出 `paper_candidate` / `paper_candidate_normalized`
- **不要求** 同一长流程内同步完成 `enrich-candidates`、`merge-metadata`、`dedup-candidates`、`enrich-paper-oa`

这与 2026-04-23 固化的解耦 runbook 一致：
- `runbooks/163-local-mail-modular-pipeline-2026-04-23.md`
- `runbooks/163-local-body-ingest-smoketest-2026-04-23.md`
- `runbooks/163-local-body-multisample-smoketest-2026-04-23.md`

---

## 本次输入与命令

### Windows 侧 body sweep

小样本 2-page probe:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 `
  -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_sweep_test_p2b.jsonl `
  -PageLimit 2 `
  -MaxTargets 100
```

10h 主运行:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 `
  -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_sweep_10h.jsonl `
  -PageLimit 900 `
  -MaxTargets 6600
```

### WSL 侧 early-ingest 验证

20 封 mixed smoke test:

```bash
./scripts/run_163_local_pipeline_timed.sh \
  data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_10h_smoke20.jsonl \
  /tmp/mgap_163_local_sweep10h_smoke20.db \
  data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing_sweep10h_smoke20.json
```

1878 封全量 early-ingest:

```bash
export INIT_DB=1 IMPORT_LIMIT=5000 PARSE_LIMIT=10000 NORMALIZE_LIMIT=50000
./scripts/run_163_local_pipeline_timed.sh \
  data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_10h.jsonl \
  /tmp/mgap_163_local_sweep10h_full.db \
  data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing_sweep10h_full.json
```

---

## 观测结果（Known）

## A. body sweep 抓取结果

### 2-page probe

- `page_limit=2`
- `pages_visited=2`
- `attempted_new=100`
- `success=100`
- `failures=0`
- `elapsed_seconds=540.676`
- `avg_seconds_per_success=5.407`
- 输出：`data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_test_p2b.jsonl`

### 10h 主运行

- `page_limit=900`
- `pages_visited=21`
- `attempted_new=1878`
- `success=1878`
- `failures=0`
- `reached_target_limit=false`
- `elapsed_seconds=24267.564`，即 **6h 44m 27.6s**
- `avg_seconds_per_success=12.922`
- 输出：`data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_10h.jsonl`
- 文件大小：约 **80 MB**

### 10h 输出结构抽样

从 `scholar_body_fetch_sweep_10h.jsonl` 抽样检查：
- 记录包含 `body_text`, `body_html`, `body_source`, `body_iframe_id`, `body_iframe_url`, `opened_page_url`, `message_id`, `headers` 等建库所需字段
- `body_text` / `body_html` 非空，符合 `import-local-bodies` 所需输入模式

### 10h sweep 的正文来源分布

全量 `1878` 行统计：
- `body_source=iframe`: `1744`
- `body_source=dom`: `134`

因此当前 163 正文抓取应视为 **双路径渲染**：
- 主路径：`iframe`
- 次路径：`dom`

但两条路径都已进入下游验证，不构成当前 blocker。

### 10h sweep 的邮件类型分布

按 subject 规则粗分：
- `citation`: `874`
- `related_work`: `860`
- `new_article`: `51`
- `other`（主要是 subject 截断或命名变体）: `93`

### 21 页 page probe

用户已确认当前 163 邮箱 UI 设置为：**每页固定显示 100 封邮件**（包含其他来源邮件，不仅限 Scholar alerts）。这意味着当前 sweep 的分页容量是稳定约束，而不是随 DOM 曝露随机波动。

总列表页为 21 页，每页 `letter_count=100`，其中 scholar-like 行数范围约 `77-96`。全 run 的 `page_url` 只有 **1 个唯一值**，说明当前 163 inbox URL **不编码当前分页状态**。

---

## B. 时间成本

### 1. body sweep 成本

| Run | Success | Elapsed (s) | Avg s / mail |
|---|---:|---:|---:|
| 2-page probe | 100 | 540.676 | 5.407 |
| 10h main run | 1878 | 24267.564 | 12.922 |

主运行相对 2-page probe 的 per-mail 成本放大约：

- `12.922 / 5.407 = 2.39x`

### 2. 按页平均耗时（来自 10h JSONL）

页深越大，平均每封耗时越高：

- page 1: `4.332 s/mail`
- page 5: `6.975 s/mail`
- page 10: `12.234 s/mail`
- page 15: `14.806 s/mail`
- page 21: `15.145 s/mail`

对全量 1878 封做线性拟合：

- `elapsed_per_mail ≈ 5.232 + 0.614 * (page_no - 1)` 秒

由此得到：
- 基线成本约 `9826.4 s`，即 **2.73 h**
- 由页深额外引入的成本约 `11679.9 s`，即 **3.24 h**

也就是说，本次 10h run 的主要额外成本 **不是正文解析本身**，而是深页恢复 / 翻页相关开销。

### 3. early-ingest 成本

#### 20 封 mixed smoke test

来源：`data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing_sweep10h_smoke20.json`

- 总耗时：`1.571 s`
- `import-local-bodies`: `0.192 s`
- `parse-mails`: `0.260 s`
- `normalize-candidates`: `0.165 s`
- 核心三步合计：`0.617 s`
- 核心平均：`0.03085 s/mail`

#### 1878 封全量 early-ingest

来源：`data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing_sweep10h_full.json`

- 总耗时：`16.633 s`
- `import-local-bodies`: `2.493 s`
- `parse-mails`: `11.855 s`
- `normalize-candidates`: `1.283 s`
- 核心三步合计：`15.631 s`
- 核心平均：`0.008323 s/mail`

#### 对比

- body sweep：`24267.564 s`
- full early-ingest：`16.633 s`

二者量级比约：
- `24267.564 / 16.633 ≈ 1459x`

当前瓶颈几乎完全在 **163 UI 抓正文**，而不在 SQLite 侧 early-ingest。

---

## C. early-ingest 验证结果

### 20 封 mixed smoke test

- 输入：`scholar_body_fetch_sweep_10h_smoke20.jsonl`
- 组成：`8 related_work + 6 citation + 3 new_article + 3 other`
- 正文来源混合：`15 iframe + 5 dom`

结果：
- `import-local-bodies`: `processed=20, imported=20, skipped=0, no_body=0`
- `parse-mails`: 找到 `20` 封未解析 Scholar 邮件
- `normalize-candidates`: `169` 条全部 normalize 成功
- DOI: `41`
- PMCID: `2`

top canonical URL domains:
- `www.sciencedirect.com: 67`
- `ieeexplore.ieee.org: 25`
- `link.springer.com: 17`
- `academic.oup.com: 15`
- `www.researchsquare.com: 15`

### 1878 封全量 early-ingest

结果：
- `import-local-bodies`: `processed=1878, imported=1878, skipped=0, no_body=0`
- `parse-mails`: 找到 `1878` 封未解析 Scholar 邮件
- `normalize-candidates`: `15284` 条全部 normalize 成功
- DOI: `3930`
- PMCID: `29`
- arXiv: `49`

top canonical URL domains:
- `www.sciencedirect.com: 7209`
- `link.springer.com: 1877`
- `academic.oup.com: 1781`
- `ieeexplore.ieee.org: 1772`
- `www.researchsquare.com: 1762`
- `www.nature.com: 156`
- `onlinelibrary.wiley.com: 65`
- `arxiv.org: 49`
- `www.mdpi.com: 38`
- `pmc.ncbi.nlm.nih.gov: 29`

### 判定

按当前 runbook 标准，本轮已经满足：

- `imported == fetched_success`
- `no_body = 0`
- `parse-mails` 正常
- `normalize-candidates` 正常
- canonical domains 由真实 publisher 域主导
- 未见 `void(0)` / `r.mail.163.com` / 163 chrome 导航 DOM 污染主导结果

因此：

> **当前 163 Windows-local body sweep 已经可以稳定接入现有资料库的 early-ingest 边界。**

---

## 对“深页翻页 + UI 导航成本累积”的分析

## Known

1. 当前 `run_body_fetch_sweep()` 的主循环在每封邮件后都会执行：
   - 打开邮件
   - 提取正文
   - `_return_to_inbox(page, current_page_url)`
   - 下一封前再 `_ensure_list_page(page, current_page_no, ...)`

2. `_return_to_inbox()` 当前实现是：

```python
await page.goto(inbox_url, wait_until='domcontentloaded', timeout=30000)
await page.wait_for_timeout(1200)
```

3. 10h run 中 21 页的 `page_url` 实际只有 1 个唯一值，因此这个 `goto(inbox_url)` **不会保留当前分页位置**。

4. `_ensure_list_page()` 当前靠连续点击 `next/prev` 恢复目标页，属于 **O(page depth)** 的恢复路径。

5. 页深与每封平均耗时近似线性增长，且线性项可解释约 **3.24 小时** 的额外成本。

## Inferred

当前主要慢点不是“打开邮件正文很慢”，而是：

- 每封邮件抓完后都被 `goto()` 拉回到分页未知的列表入口
- 之后为了回到 page `N`，脚本又线性点击 `next` `N-1` 次
- 当目标页深较大时，这个成本在同一页的每一封邮件上被重复支付

换句话说，当前 sweep 虽然逻辑上是“按页处理”，但运行时更像是：

> **按页收集 roster，然后对页内每一封邮件都重新做一次“从入口回到该页”的导航。**

这正是页深成本累积的根源。

## Speculative but high-confidence estimate

如果能让“从邮件返回列表”时保留当前页，而不是回到 page 1 风格入口，那么本轮 10h run 的主体时间有机会从：

- 现状：约 **6.74 h**

下降到大致：

- 约 **2.7-3.5 h** 区间

也就是 **约 2x 左右提速** 是现实可期待的。

---

## 可行解决方案矩阵

## 方案 A. 用 history.back() / UI back 替代 `goto(inbox_url)`，保留当前列表页

### 思路
在打开一封邮件后，正文提取完成时不要 `goto()` 回列表入口，而是优先尝试：
- 浏览器 `history.back()`
- 或 163 read view 内置“返回列表”按钮

目标是回到**同一分页、同一列表上下文**。

### 优点
- 改动最小
- 不需要重做 index schema
- 如果 163 SPA history 正常，可直接砍掉深页重复恢复成本

### 风险
- 163 可能用单页应用（SPA）切模块，`history.back()` 未必总是稳定
- 回退后列表 DOM 是否立即可用，需要额外 ready-state 校验
- 回退后滚动位置可能变化，但这比“重新从 page 1 点 20 次 next”便宜得多

### 推荐度
**高，作为第一优先试验。**

---

## 方案 B. 按页驻留处理，不在页内每封邮件后重建分页位置

### 思路
让 sweep 真正变成“页级工作流”：
1. 到达 page `N`
2. 收集 page `N` 的 rows
3. 逐封打开正文
4. 每次都回到 page `N` 的列表态
5. 当前页完成后只翻页一次进入 page `N+1`

### 优点
- 直接贴合当前 sweep 的语义
- 能显著减少 `_ensure_list_page()` 的重复调用
- 与方案 A 兼容

### 风险
- 需要一个稳定的“回到当前页列表态”实现
- 163 若在打开邮件后重绘整个列表模块，可能仍需少量校正逻辑

### 推荐度
**高，建议与方案 A 绑定实现。**

---

## 方案 C. 在 index 阶段捕获稳定 read-id / read URL，后续直接按邮件 ID 打开 read view

### 思路
当前最本质的优化是把正文抓取从“依赖列表页定位”改成“依赖稳定邮件 ID”。

如果能在 index 阶段或首次点击时拿到稳定 read identifier，例如：
- `read.ReadModule` 中的 `id`
- 真实 `mid`
- 或 163 row DOM 中可提取的 message token

那么后续 body fetch 可直接：
- 在同一浏览器上下文里打开 read route
- 不再依赖翻页回到 page `N`

### 优点
- 从根本上去掉深页依赖
- 正文抓取从 O(page depth) 退化为近似 O(1) / mail
- 后续可以更容易做断点续跑 / worker tab / 更干净的重放

### 风险
- 需要额外 reverse engineer 163 row DOM / onclick / route payload
- 当前 index JSONL 还没有保存这种稳定 ID
- 实现复杂度高于 A/B

### 推荐度
**中高。** 这是最有价值的中期重构方向，但不应阻塞 A/B 的近端提速。

---

## 方案 D. 双标签页 / worker-tab 模式，列表页保持驻留，正文在第二个 tab 中打开

### 思路
把列表页当作“只负责定位”的 anchor tab，正文抓取在第二个 tab 中进行。这样列表 tab 永远停在 page `N`，不被 read view 污染。

### 优点
- 概念上干净
- 如果能拿到 read URL / message id，会很强

### 风险
- 若没有稳定 read-id，第二个 tab 仍难以直接打开目标邮件
- Playwright 对真实 Chrome 多 tab 控制复杂度更高

### 推荐度
**中。** 更适合作为方案 C 的延伸，而不是当前第一刀。

---

## 推荐路线

### 推荐顺序

1. **先做方案 A+B**
   - 目标：最小改动验证“保留当前页返回列表”是否足以把 10h run 降到约 3h 级别
   - 这是当前收益 / 风险比最高的方案

2. **并行侦查方案 C 的可行性**
   - 在 live DOM 中找 row 上是否存在稳定 message token / onclick / route payload
   - 一旦能稳定拿到 read-id，就可以规划第二阶段重构

3. **若 A 不稳定，再考虑 B + UI back 专门实现，或 C 驱动的 worker-tab 方案**

### 最小实验设计

建议先做一个极小 patch + A/B test：

- 目标页：例如 page 8 或 page 12
- 样本：连续 20-30 封
- 对照：
  - 旧逻辑：`goto(inbox_url)` + `_ensure_list_page()`
  - 新逻辑：`history.back()` 或 UI back 保留当前页
- 记录：
  - `avg_seconds_per_success`
  - 回退成功率
  - 列表页恢复正确率
  - 是否再次出现 page drift

如果单页内 per-mail 成本从 `~14-15s` 下降到 `~5-7s`，就说明主瓶颈判断成立。

## 2026-04-24 live benchmark（A+B patch 后）

### Patch 摘要

已对 `scripts/windows_local/read_163_scholar_with_manual_pause.py` 做最小 A+B patch：
- 抓完单封后优先 `history.back()` 返回列表
- 仅当保不住当前页时才 fallback 到 `goto(inbox_url)`
- 在 sweep 页内引入 `current_page_preserved`，避免每封邮件都重复 `_ensure_list_page()`
- summary 新增 `return_method_counts`

### 环境补充

由于当前 WSL 存在 `http_proxy/https_proxy/all_proxy`，`http://127.0.0.1:9222/json/version` 可能出现“HTTP 看似可达、但 WebSocket 实际不可达”的假阳性。最终使用的可用链路是：
- Windows Chrome: `127.0.0.1:9222`
- Windows `portproxy`: `0.0.0.0:9223 -> 127.0.0.1:9222`
- WSL 侧 CDP endpoint: `http://<WindowsHostIP>:9223`

### Benchmark 1: page 1 / 5 mails

命令：

```bash
python3 scripts/windows_local/read_163_scholar_with_manual_pause.py \
  run-body-sweep \
  --cdp-endpoint http://<WindowsHostIP>:9223 \
  --output-jsonl data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_backtest5_v5.jsonl \
  --page-limit 1 \
  --max-targets 5
```

结果：
- `attempted_new=5`
- `success=5`
- `failures=0`
- `elapsed_seconds=32.249`
- `avg_seconds_per_success=6.45`
- `return_method_counts = {history_back: 5, goto: 0}`

解释：page 1 基本验证了 patch 机制层面成立，返回列表时已不是旧的 `goto` 路径。

### Benchmark 2: page 12 / 5 mails（targeted deep-page test）

做法：先用历史 full-run JSONL 预填 `page < 12` 的 existing keys（`961` 行），让 sweep 跳过前 11 页已知记录，只在 page 12 首次处理 `5` 封新目标。

结果：
- `pages_visited=12`
- `attempted_new=5`
- `success=5`
- `skipped_existing=961`
- `elapsed_seconds=105.909`
- `avg_seconds_per_success=21.182`
- `return_method_counts = {history_back: 5, goto: 0}`

解释：这轮主要证明 **即使在深页，回退也能 5/5 保住 `history.back` 路径**。但样本只有 `5` 封，固定的前 11 页 traversal 成本占比过高，因此不能直接拿 `21.182 s/mail` 当作深页稳态成本。

### Benchmark 3: page 12 / 20 mails（代表性深页样本）

同样先预填 `page < 12` 的 existing keys（`961` 行），再在 page 12 处理 `20` 封新目标。

结果：
- `pages_visited=12`
- `attempted_new=20`
- `success=20`
- `skipped_existing=961`
- `failures=0`
- `elapsed_seconds=181.084`
- `avg_seconds_per_success=9.054`
- `return_method_counts = {history_back: 20, goto: 0}`

### Benchmark 4: `--start-page 12 --page-limit 1` / 20 mails

在 A+B patch 之后，进一步加入：
- `--start-page N`：从指定 inbox page 开始 sweep
- `--start-from-current-page`：从当前可见 inbox page 继续 sweep

对 page 12 重新做 targeted benchmark，仍先预填 `page < 12` 的 existing keys（`961` 行），但这次直接：

```bash
python3 scripts/windows_local/read_163_scholar_with_manual_pause.py \
  run-body-sweep \
  --cdp-endpoint http://<WindowsHostIP>:9223 \
  --output-jsonl data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_backtest_page12_startpage20_seed.jsonl \
  --start-page 12 \
  --page-limit 1 \
  --max-targets 20
```

结果：
- `requested_start_page=12`
- `effective_start_page=12`
- `pages_visited=1`
- `attempted_new=20`
- `success=20`
- `failures=0`
- `elapsed_seconds=129.56`
- `avg_seconds_per_success=6.478`
- `return_method_counts = {history_back: 20, goto: 0}`

### Wrapper benchmark: Windows PowerShell `run_163_body_fetch_sweep.ps1`

为防止“代码支持了新语义，但日常入口仍退回旧习惯”，又对 Windows wrapper 本身做了一次真实验证：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartPage 12 -PageLimit 1 -MaxTargets 10 -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_wrappertest_page12_seed.jsonl
```

结果：
- `requested_start_page=12`
- `effective_start_page=12`
- `pages_visited=1`
- `attempted_new=10`
- `success=10`
- `failures=0`
- `avg_seconds_per_success=5.831`
- `return_method_counts = {history_back: 10, goto: 0}`

说明 wrapper 已经正确传递了新的 start semantics，而不是只在 direct Python CLI 上生效。

### Live benchmark 结论

已知旧 full-run 中，page 12 的经验均值约为：
- `14.598 s/mail`

而 patch 后的两个 page 12 live benchmark 给出：
- 保页返回，但仍从 page 1 traversal 到 page 12：`9.054 s/mail`
- 保页返回 + 直接从 `--start-page 12` 开始：`6.478 s/mail`
- Windows wrapper `-StartPage 12` 实测：`5.831 s/mail`

对应粗略改进幅度约：

- `1 - 9.054 / 14.598 ≈ 38.0%`
- `1 - 6.478 / 14.598 ≈ 55.6%`
- `1 - 5.831 / 14.598 ≈ 60.1%`

因此可以得出高置信度判断：

1. **A+B patch 已经成功击中了主瓶颈。**
2. 深页 slowdown 的主因确实是“每封邮件抓取后丢失当前页，再线性恢复 page N”。
3. `history.back()` 在当前 163 UI 上表现稳定，至少在 page 1 与 page 12 的 live benchmark 中均达到：
   - `goto = 0`
   - `history_back = 100%`
4. **进一步减少首次抵达 page N 的 traversal 成本也是值得做的，并且已经被 `--start-page 12` benchmark 直接验证。**
5. 当前 sweep 的最优近端使用方式应为：
   - 常规从头抓取：`--start-page 1`
   - 深页续跑：`--start-page N`
   - 当前页恢复/接力：`--start-from-current-page`
6. 中期仍值得推进 index 阶段抓稳定 read-id，使正文抓取进一步从列表定位型转为 ID 驱动。

## 2026-04-24 read-id / mid 侦查与第一阶段实现

### 观测

对当前真实 163 列表页做 DOM + page-source 探针后，得到以下结论：

1. row 元素本身没有可直接复用的：
   - `href`
   - `onclick`
   - `data-mid`

2. 但 row 的 `id` 具有稳定结构，例如：

```text
1777000608049_733xtbC3QHPWWmtmHtTQAA3q1777001200113Dom
```

如果去掉：
- 前缀时间戳 `1777000608049_`
- 后缀时间戳 + `Dom`，即 `1777001200113Dom`

则得到核心 token：

```text
733xtbC3QHPWWmtmHtTQAA3q
```

3. 打开邮件后的 read route / iframe 中，真实 id 形如：

```text
733:xtbC3QHPWWm+tmHtTQAA3q
```

4. 两者满足精确归一化关系：

```text
normalize(read_mid) = read_mid.replace(':', '').replace('+', '')
normalize(read_mid) == core_token_from_row_id
```

5. 当前 page source 中可以直接 regex 抓到一批 `readhtml3.jsp?mid=...`，因此：
   - `row.node_id` -> `read_mid_token`
   - `page source mids` -> `read_mid`
   - 二者可以在当前页做 exact token join

### 第一阶段实现

已在 `scripts/windows_local/read_163_scholar_with_manual_pause.py` 中加入：

- `_node_id_mid_token()`
- `_page_visible_mid_map()`
- `_attach_read_mid_fields()`

并让这层 enrichment 同时作用于：
- `run-index`
- `run-body-sweep`

当前新字段：
- `read_mid_token`
- `read_mid`
- `read_route_id`
- `read_mid_source=page_source_regex`

### Live probe 结果

当前页面 live probe：
- `row_count=86`
- `mid_map_count=25`
- `mapped_count=18`

说明：
- 这已经足够支持 **partial ID capture**
- 但还不足以宣称“当前 index 页面总能 100% 还原所有 visible rows 的 `read_mid`”

当前最合理判断是：
- 页面源码里暴露的 `mid` 是真实且可 join 的
- 但暴露范围受当前页面缓存 / 已加载 read modules 影响
- 因此 **第一阶段最适合做 partial capture + 继续观察覆盖率**，而不是立刻把 sweep 全面改写成“纯 read-id 驱动、不再依赖列表定位”

### 下一步建议

1. 先让新字段进入后续增量 index / sweep 产物，积累覆盖率数据
2. 统计：
   - Scholar rows 中 `read_mid` 覆盖率
   - 不同页深 / 不同页面状态下的覆盖率波动
3. 如果覆盖率足够高，再进入第二阶段：
   - 优先用 `read_mid` 直接打开 read route
   - 对缺失 `read_mid` 的少数样本保留列表定位 fallback

## 2026-04-24 ID-first direct-fetch prototype 测试

在第一阶段 `read_mid` partial capture 可用之后，继续做了一个 **ID-first, list-free** 的原型测试：
- 不再点击列表 row 打开正文
- 直接用 `read_mid` 构造 `readhtml3.jsp?mid=...` URL
- 在同一已登录浏览器 context 中直接拉正文 HTML
- 仍复用现有 `_body_record()` 产出结构

### Smoke test: page 12 / 5 mapped mails

命令语义：
- 从 page 12 收集当前页已能映射出 `read_mid` 的目标
- 直接按 `mid` 拉正文

结果：
- `collected_targets=5`
- `success=5`
- `failures=0`
- `elapsed_seconds=14.271`
- `avg_seconds_per_success=1.977`
- 当前页 `mapped_rows=18`

这个速度显著快于现有列表定位型抓取：
- 对比 page 12 wrapper benchmark：`5.831 s/mail`
- 当前 direct-fetch smoke：`1.977 s/mail`

粗略相对改善约：
- `1 - 1.977 / 5.831 ≈ 66.1%`

### Larger prototype run: page 12 -> 36 / target 400

随后做了更大范围的 direct-fetch prototype：
- `start_page=12`
- `page_limit=25`
- `max_targets=400`

结果：
- 总 run 耗时：`166.801 s`
- `collected_targets=18`
- `success=18`
- `failures=0`
- `avg_seconds_per_success=1.963`

关键观察：
- page 12: `mapped_rows=18`
- page 13-36: `mapped_rows=0`

### 结论

1. **当 `read_mid` 可用时，ID-first direct fetch 非常快。**
   - 当前实测速率约 `~1.96-1.98 s/mail`
   - 明显快于当前最优的列表定位型抓取

2. **当前瓶颈已从“direct fetch 是否可行”转移为“`read_mid` 覆盖率是否足够高”。**

3. 当前 `read_mid` capture 显示出明显的 **page-local / cache-dependent** 特征：
   - 某一页能拿到一批 `mid`
   - 但继续翻到后续页时，源码中不自动暴露该页的 `mid`
   - 因此 larger prototype run 无法自然扩展到预期的 20 分钟规模

4. 这说明第二阶段的下一刀不应该直接是“全面切到 ID 驱动”，而应先解决：
   - 如何在每个新页上稳定 prewarm / 暴露该页 rows 对应的 `mid`
   - 或如何从更深的前端数据结构中直接抽到 page-local `mid`

### 当前最合理的下一步

优先尝试一个 **page-prewarm probe**：
- 在新页上先点击 1 封（或极少数）邮件，触发该页的 read module / iframe 缓存注入
- 然后再次抓 page source 的 `mid`
- 观察该页 `mapped_rows` 是否从 `0` 提升到接近 page 12 的水平

如果这一步成立，就可以进入真正的 hybrid 方案：
- 每页做一次极小 prewarm
- 然后对该页大部分有 `read_mid` 的目标走 direct fetch
- 只把残余少量样本留给列表定位 fallback

---

## 当前固化结论

1. **163 Windows-local body sweep 已经不是“能不能接库”的问题了。** 这个问题已经被 20 封 mixed smoke test 和 1878 封 full early-ingest 同时回答为“能”。
2. 当前真正需要优化的是 **正文抓取阶段的 UI 导航成本**。
3. 现有证据最支持的根因是：
   - `goto(inbox_url)` 不能保留分页
   - `_ensure_list_page()` 对深页使用线性 next/prev 恢复
   - 该成本在页内每封邮件上重复支付
4. **最佳近端动作是先试 A+B：保留当前页返回列表态。**
5. **最佳中期动作是补抓稳定 read-id，从列表定位型抓取升级为 ID 驱动型抓取。**

---

## 相关产物

- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_10h.jsonl`
- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_sweep_10h_smoke20.jsonl`
- `data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing_sweep10h_smoke20.json`
- `data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing_sweep10h_full.json`
- `runbooks/163-local-mail-modular-pipeline-2026-04-23.md`
- `runbooks/163-local-body-ingest-smoketest-2026-04-23.md`
- `runbooks/163-local-body-multisample-smoketest-2026-04-23.md`
