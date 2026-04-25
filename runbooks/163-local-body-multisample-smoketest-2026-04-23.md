# 163 本机正文多样本 smoke test（2026-04-23）

## 目标

在已经验证“单封 body fetch → import → parse → normalize”可行之后，继续用 **19 封代表性样本** 做第二阶段 smoke test，确认：

1. iframe 正文抓取对不同 alert 类型都稳定
2. 产物可稳定导入现有 SQLite schema
3. `parse-mails` / `normalize-candidates` 对 mixed sample 不出现结构性失败
4. 可以据此进入全量 `277` 封正文抓取

## 样本设计

本轮选 **19 封**，覆盖：
- page 1 / page 2 / page 3
- `新的相关研究工作`（related_work）
- `文章新增了 X 次引用`（citation）
- `新文章`（new_article）

批次设计：

| Batch | StartOffset | Limit | Coverage |
|---|---:|---:|---|
| page1-mixed | 0 | 6 | page 1 mixed related/citation |
| page1-new-article | 38 | 1 | page 1 `新文章` |
| page2-mixed | 100 | 5 | page 2 mixed related/citation |
| page3-mixed-plus-new | 190 | 7 | page 3 mixed related/citation + `新文章` |

总目标数：`19`

## 前提

- Windows Chrome 保持打开
- Chrome 已启用 CDP：`http://127.0.0.1:9222`
- 163 邮箱已登录并停留在未读 / 收件箱上下文
- 输入 roster：`data/raw_mail_exports/163_scholar_local/scholar_index.jsonl`
- 当前可信 index baseline：`277` 行

## Step 1. Windows 侧抓取 19 封样本正文

### 方式 A（推荐，直接用新 wrapper）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_multisample.ps1 -ResetOutput
```

默认输出：
- success JSONL: `data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl`
- failure JSONL: `data\raw_mail_exports\163_scholar_local\scholar_body_fetch_failures.jsonl`
- timing JSON: `data\raw_mail_exports\163_scholar_local\timing\body_fetch_multisample_timing.json`

计时说明：
- `run_163_body_fetch_sample.ps1` 会打印单批 `Wrapper timing`
- Python body-fetch 本身会输出 `elapsed_seconds`, `avg_seconds_per_success`, `avg_seconds_per_target`
- multi-sample wrapper 会为每个 batch 记录 `elapsed_seconds`，并汇总到 timing JSON

### 方式 B（手动逐批执行）

```powershell
Remove-Item data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl -Force -ErrorAction SilentlyContinue
Remove-Item data\raw_mail_exports\163_scholar_local\scholar_body_fetch_failures.jsonl -Force -ErrorAction SilentlyContinue

powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl -StartOffset 0 -Limit 6
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl -StartOffset 38 -Limit 1
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl -StartOffset 100 -Limit 5
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -OutputJsonl data\raw_mail_exports\163_scholar_local\scholar_body_fetch_multisample19.jsonl -StartOffset 190 -Limit 7
```

## Step 2. WSL 侧做 fresh DB smoke test

```bash
cd ~/NewCareer/Openclaw/proj/MyGoogleAlertPapers

./scripts/run_163_local_pipeline_timed.sh \
  data/raw_mail_exports/163_scholar_local/scholar_body_fetch_multisample19.jsonl \
  /tmp/mgap_163_local_multisample.db \
  data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing.json
```

默认会依次运行：
- `init-db`
- `import-local-bodies`
- `parse-mails`
- `normalize-candidates`
- `report-batch`
- `report-normalization`

并输出：
- `data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing.json`

## Step 3. 快速验收点

### 抓取层验收
至少检查：
- JSONL 行数接近目标 19（允许少量失败，但不应系统性掉样）
- 记录中的 `body_source` 应以 `iframe` 为主，理想上全为 `iframe`
- `body_text` 不是 163 chrome 导航文字，而是 Scholar alert 论文列表
- `body_html` 中链接应主要是 `https://scholar.google.com/scholar_url?url=...`

### 入库层验收
最少要求：
- `import-local-bodies`: `no_body=0`
- `parse-mails`: 能找到并处理导入邮件
- `normalize-candidates`: 产出真实 normalized candidate，而不是 0
- `report-normalization`: top canonical URL domains 以真实 publisher 域名为主，不应被 `void(0)`、`r.mail.163.com` 等垃圾链接主导

### 推荐通过标准
- 成功抓取 `>= 16 / 19`
- `imported == fetched_success`
- `normalized candidates > 0`
- 至少出现多个真实 publisher 域名
- 无统一结构性失败（例如所有样本都抓成外层 chrome、所有链接都变成 `void(0)`、所有邮件都 parse 失败）

## 时间/开销估算方法

### 1. 正文抓取阶段
从：
- `data/raw_mail_exports/163_scholar_local/timing/body_fetch_multisample_timing.json`

读取：
- `elapsed_seconds`
- `expected_target_count`
- 若有失败，再结合 success JSONL 实际成功行数做修正

粗略估算：
- `avg_seconds_per_mail ≈ multisample_elapsed_seconds / multisample_success_count`
- `full_body_fetch_seconds ≈ avg_seconds_per_mail * 277`

### 2. 入库阶段
从：
- `data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing.json`

读取各 stage：
- `import-local-bodies`
- `parse-mails`
- `normalize-candidates`

粗略估算：
- `avg_seconds_per_mail_pipeline ≈ pipeline_elapsed_seconds / imported_mail_count`
- `full_pipeline_seconds ≈ avg_seconds_per_mail_pipeline * 277`

### 3. 当前最有用的两个数字
建议先记：
- `body fetch avg seconds / mail`
- `import+parse+normalize avg seconds / mail`

这样可以先给出 full run 的数量级估算，即使后段 enrich 暂时还没纳入。

### 4. 自动汇总命令
可直接运行：

```bash
python3 scripts/summarize_163_local_timing.py \
  --fetch-timing data/raw_mail_exports/163_scholar_local/timing/body_fetch_multisample_timing.json \
  --fetch-jsonl data/raw_mail_exports/163_scholar_local/scholar_body_fetch_multisample19.jsonl \
  --pipeline-timing data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing.json \
  --full-mail-count 277
```

它会输出：
- 样本抓取耗时
- 样本接库耗时
- 每封平均秒数
- 外推到 `277` 封的粗略总耗时

## 通过后下一步

若 19 封 mixed smoke test 通过，则进入：

1. **全量正文抓取**（277 封）
2. 以 raw archive 为输入，单独跑：
   - `parse-mails`
   - `normalize-candidates`
   - 后续 enrich / merge / dedup / OA

注意：全量抓取仍然与 enrich 解耦，不要重新绑定成长流程。
