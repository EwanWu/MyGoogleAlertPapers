# 163 本机邮件抓取与建库解耦方案（2026-04-23）

## 决策

163 本机链路后续按 **解耦的两大阶段** 运行，而不是把“抓取邮件正文”和“enrich/建库”绑在同一次长流程里。

核心原则：

1. **先验证接库边界，再扩大抓取规模**
2. **先把正文抓稳、抓全、可重放，再做长耗时 enrich**
3. **抓取产物必须能脱离 enrich 独立保存和复用**

## 为什么必须解耦

当前项目里，真正耗时且易中断的是：
- `enrich-candidates`
- 后续 `merge-metadata`
- `dedup-candidates`
- `enrich-paper-oa`

而从现有代码看，邮件进入资料库的最小稳定接缝其实更早：

- `mail_ingestion_record`
- `raw_mail_snapshot`
- `paper_candidate`

也就是说，**只要正文能稳定落到 `raw_mail_snapshot`，就已经可以接到现有数据库模型**，不需要等 enrich 跑完才算“接库成功”。

## 推荐模块边界

### 模块 A. 列表索引（已校准）

目标：先可靠拿到 mail list，而不是正文。

输入：
- 163 Web Inbox 当前页面

输出：
- `data/raw_mail_exports/163_scholar_local/scholar_index.jsonl`

状态：
- 已验证 3 页 `277` 行可信
- 作用是提供后续正文抓取的 mail roster / worklist

### 模块 B. 正文抓取与原始归档（下一步重点）

目标：把每封目标邮件的正文抓下来，并作为**可重放原始资产**保存。

输入：
- `scholar_index.jsonl`

当前第一版输出：
- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch.jsonl`
- 失败记录：`data/raw_mail_exports/163_scholar_local/scholar_body_fetch_failures.jsonl`

当前默认 Windows wrapper：
- `scripts/windows_local/run_163_body_fetch_sweep.ps1`

该 wrapper 现已支持两类更适合深页续跑的起始语义：
- `-StartPage N`：从指定 inbox page 开始 sweep
- `-StartFromCurrentPage`：从当前 Chrome 可见 inbox page 继续

每条成功记录至少包含：
- `mail_key` / `subject`
- `body_text`
- `body_html`
- 关键 header
- 抓取时间
- 原始索引定位信息（`page_no`, `row_index`, `source_index_path`）

边界要求：
- **只负责抓取与归档，不做 enrich**
- 可断点续跑
- 可重复执行而不覆盖已成功抓取结果
- 能区分：未抓取 / 已抓取 / 失败待重试

### 模块 C. 接库验证（先做小样本）

目标：先证明“当前抓下来的正文”可以稳定接入已有 SQLite 资料库。

建议样本量：
- 先做 `10-20` 封正文样本

当前已补两条桥接入口：
- Windows 本机正文抓取：
  - `python scripts/windows_local/read_163_scholar_with_manual_pause.py run-body-fetch --limit 10`
  - 或 `powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -Limit 10`
- SQLite 导入 bridge：
  - `python3 -m mygooglealertpapers.cli import-local-bodies --input <path>`

具体输入格式与 smoke test 命令见：
- `runbooks/163-local-body-ingest-smoketest-2026-04-23.md`

验证动作：
1. 初始化一个 fresh SQLite DB
2. 将样本邮件正文写入：
   - `mail_ingestion_record`
   - `raw_mail_snapshot`
3. 运行：
   - `parse-mails`
   - `normalize-candidates`
4. 检查：
   - 是否成功生成 `paper_candidate`
   - 是否能进入 `paper_candidate_normalized`
   - `report-batch` / `report-normalization` 是否正常

接库成功的判据不是 enrich 完成，而是：
- 正文能稳定导入现有 schema
- parse / normalize 能正常产出 candidate
- 样本中没有结构性字段缺失导致全局失败

### 模块 D. 全量正文抓取

前提：模块 C 小样本接库验证通过。

目标：
- 按索引把所有目标邮件正文都抓下来
- 形成完整 raw archive

这一步仍然：
- **不和 enrich 耦合**
- 只追求抓全、抓稳、可恢复、可重放

### 模块 E. 离线建库 / enrich

输入：
- 已冻结的 raw archive
- 或由 raw archive 导入生成的 fresh SQLite DB

运行顺序：
1. `parse-mails`
2. `normalize-candidates`
3. `enrich-candidates`
4. `merge-metadata`
5. `dedup-candidates`
6. `enrich-paper-oa`

要求：
- 在**独立于抓取**的上下文里运行
- 中断后只影响建库阶段，不影响已抓下来的正文资产
- 必要时可以换 fresh DB 重跑，而不需要重新打开 163 邮箱重抓正文

## 当前推荐执行顺序

### Phase 1. 先做“小样本正文 -> 接库验证”

这是当前最值得优先完成的一步。

最小目标：
- 从当前 `277` 行 index 中选 `10-20` 封
- 成功抓取正文
- 成功导入 SQLite
- 成功跑通 `parse-mails` + `normalize-candidates`

只要这一步成立，就说明：
- 163 本机抓取链路已经能给现有资料库提供有效输入
- 后续全量抓取可以放心单独推进

### Phase 2. 再做“全量正文抓取”

在接库边界已验证后，再回头把全部邮件抓下来。

这样做的好处是：
- 不会因为 enrich 太慢、太容易中断，而反过来污染抓取设计
- 不会把“抓取失败”和“建库失败”混成一个问题
- 出问题时，定位边界更清楚

当前建议的 sweep 用法不再默认为“永远从 page 1 重跑”，而是：

- 从头抓：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartPage 1 -PageLimit 12 -MaxTargets 500
```

- 深页续跑：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartPage 12 -PageLimit 1 -MaxTargets 20
```

- 从当前页恢复：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartFromCurrentPage -PageLimit 1 -MaxTargets 20
```

对于已经明确停在深页的调试或恢复场景，应优先使用 `-StartPage` 或 `-StartFromCurrentPage`，避免退回到“从 page 1 重建 traversal”的旧习惯。

### Phase 3. 最后做“独立离线建库”

等 raw archive 足够完整，再把 enrich 当成单独的长期任务处理。

## 对当前项目的具体解释

对于 MyGoogleAlertPapers 当前代码，推荐把“接库成功”定义为：

- 原始邮件内容已经进入现有 SQLite schema 的早期层：
  - `mail_ingestion_record`
  - `raw_mail_snapshot`
- 且可以继续生成：
  - `paper_candidate`
  - `paper_candidate_normalized`

不要把“接库成功”定义成：
- `canonical_paper` 已生成
- 或 `enrich-paper-oa` 已完成

那会把一个本来清晰的 ingest 边界，错误地拖到最慢、最不稳定的后段。

## 结论

后续 163 本机方案按下面的产品边界执行：

1. **索引列表**
2. **抓正文并归档 raw assets**
3. **用小样本验证可接入现有资料库**
4. **全量抓正文**
5. **独立离线 enrich / merge / dedup / OA**

这是当前最稳、最可恢复、也最符合现有工程边界的拆法。
