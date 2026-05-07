# 163 本地已抓取 8000 邮件：递增建库执行方案（2026-05-06）

## 目标

对约 8000 封已抓取的 163 Google Scholar 邮件执行：

1. 稳定导入现有 MGAP SQLite 资料库；
2. 让资料库按轮次递增；
3. 新批次优先命中既有 canonical paper，而不是重复新建；
4. 暂不做 preprint -> journal 自动 version-upgrade；该问题后续通过扫库/版本重建单独处理。

---

## 冻结决策

### 本轮明确采用
- `library_prelink` 作为第一层短路
- `same_batch_clustering` 作为第二层短路
- 默认同步主线 profile（当前 true default）
- preprint / journal 暂不自动升级 canonical 主记录

### 本轮明确不做
- 不把 8000 封一次性绑成单个超长 end-to-end run
- 不在这一轮引入新的 match heuristic
- 不在这一轮解决 preprint -> journal 自动升级

---

## 关键量化先验

来自已验证的 163 full early-ingest：

- 1878 mails -> 15284 normalized candidates
- 平均约 `8.14 candidates / mail`

因此对 8000 mails 的粗估：

- normalized candidates 约 `8000 * 8.14 ~= 65120`

这只是 ingest 规模估计，不是最终 canonical 规模估计。

---

## 总体执行策略

分两层：

### 层 A：一次性完成早期层导入
目标：把 8000 封都稳定落入数据库早期层。

顺序：
1. `init-db`
2. `validate-local-bodies`
3. `import-local-bodies`
4. `parse-mails`
5. `normalize-candidates`

### 层 B：按 chunk 递增建库
目标：利用上一批形成的 canonical 库，为下一批做 `library_prelink`，降低 provider fanout。

每个 chunk 顺序：
1. `resolve-candidates`
2. `enrich-candidates`
3. `merge-metadata`
4. `dedup-candidates`
5. `report-*`

---

## 推荐 chunk 设计

### 启动策略
先做一个 pilot chunk：
- **500 mails 等价规模**
- 按当前经验约等于 **4000-4500 candidates**

但 CLI 当前最直接按 **candidate 数** 分批，所以推荐：

- **Pilot chunk = 4000 normalized candidates**
- 若稳定，再切到 **Regular chunk = 5000 normalized candidates**

### 为什么不用更大
- 便于观察 prelink 命中率是否随库增长而上升
- 便于在 provider 慢/超时时快速止损
- 便于 review queue 与异常样本抽查

### 为什么不用更小
- 太小会让固定开销和人工监控负担过高

---

## 建议路径与输入

假设：

- 项目根目录：`/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers`
- 8000 封正文 JSONL：
  `data/raw_mail_exports/163_scholar_local/<YOUR_8000_JSONL>.jsonl`
- 本轮 DB：
  `~/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db`

如需替换文件名，只改下面变量即可。

---

## 一次性初始化与早期层导入

```bash
cd /home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers

export MGAP_DB="$HOME/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"
export SQLITE_PATH="$MGAP_DB"
export INPUT_JSONL="data/raw_mail_exports/163_scholar_local/<YOUR_8000_JSONL>.jsonl"

# MGAP CLI 当前从环境变量 SQLITE_PATH 读取 sqlite_path。
# 若 shell 中未显式 export SQLITE_PATH，则会回退到默认 data/mgap.db。

python3 -m mygooglealertpapers.cli validate-local-bodies --input "$INPUT_JSONL"
python3 -m mygooglealertpapers.cli init-db
python3 -m mygooglealertpapers.cli import-local-bodies --input "$INPUT_JSONL" --limit 20000
python3 -m mygooglealertpapers.cli parse-mails --limit 10000
python3 -m mygooglealertpapers.cli normalize-candidates --limit 100000
python3 -m mygooglealertpapers.cli report-batch
python3 -m mygooglealertpapers.cli report-normalization
```

---

## 递增建库：pilot -> regular chunks

### Pilot chunk（先跑一次）

```bash
python3 -m mygooglealertpapers.cli resolve-candidates --limit 4000
python3 -m mygooglealertpapers.cli enrich-candidates --limit 4000
python3 -m mygooglealertpapers.cli merge-metadata --limit 4000
python3 -m mygooglealertpapers.cli dedup-candidates --limit 4000

python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
```

### 如果 pilot 正常，再进入 regular chunks

```bash
python3 -m mygooglealertpapers.cli resolve-candidates --limit 5000
python3 -m mygooglealertpapers.cli enrich-candidates --limit 5000
python3 -m mygooglealertpapers.cli merge-metadata --limit 5000
python3 -m mygooglealertpapers.cli dedup-candidates --limit 5000
```

重复直到：
- unresolved normalized candidates 逼近 0
- 或剩余量已小到适合单独处理

---

## 每个 chunk 后必须记录的监控指标

### A. ingest / normalization 规模指标
来自：
- `report-batch`
- `report-normalization`

看：
- total scanned mails
- detected Scholar mails
- extracted candidates
- normalized candidates
- DOI / PMID / PMCID / arXiv 抽取量

### B. library-prelink 效率指标
来自：
- `report-enrichment`

重点看：
- `library prelinked candidates`
- `library prelink rule counts`
- `prelink-skipped provider intents`
- `post-prelink residual title requests`

推荐计算：

- **prelink hit ratio** = `library_prelinked_candidates / candidate_count`
- **provider short-circuit ratio** = `prelink_skipped_provider_intents / (prelink_skipped_provider_intents + dispatch_request_count)`

### C. provider 吞吐指标
来自：
- `report-enrichment`
- `report-cost`

重点看：
- `dispatch_request_count`
- `processed_runnable_intents / runnable_provider_intents`
- provider breakdown
- lane stop reasons
- lane elapsed ms

### D. canonical 增长与压缩指标
来自：
- `report-dedup`

重点看：
- `canonical papers`
- `candidate-paper links`
- `compression ratio`
- 按 `rule` 的 link 构成

### E. 风险指标
来自：
- `report-review-queue`
- `export-review-queue`

重点看：
- blocked candidates 总量
- reason 分布
- 是否出现某一 reason 突然暴增

---

## chunk 通过 / 降速 / 暂停规则

### Pilot 通过标准
满足以下大多数即可进入 regular chunk：

1. `processed_runnable_intents / runnable_provider_intents >= 0.90`
2. `review queue` 没有异常暴增
3. `dispatch_request_count` 没有明显失控
4. enrichment 无系统性 provider failure
5. dedup 后 canonical 增长合理，未见明显错误合并信号

### 降速条件（5000 -> 2500）
满足任一条就降速：

1. `processed_runnable_intents / runnable_provider_intents < 0.75`
2. provider timeout / stop reason 明显增多
3. review queue 单批新增 > `chunk_size * 0.05`
4. 人工 spot-check 发现错误合并风险

### 暂停并诊断条件
满足任一条就暂停：

1. 某 provider 出现持续性失败/429/超时
2. `report-dedup` 中 canonical 增长模式异常
3. `review queue` 中 severe conflict 类原因突然成片出现
4. 同一 chunk 的 `dispatch_request_count` 相比前一 chunk 异常上升且无法解释

---

## 推荐监控节奏

### 每个 chunk 后
立即跑：

```bash
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
```

### 真实 current-session cron 监测（已验证 CLI 路径）
如果当前聊天工具没有直接暴露 `cron` tool，不要伪造 state-file 里的 cron 字段；改用 OpenClaw CLI 的真实 cron：

```bash
openclaw cron add \
  --name "mgap-regular-chunk-followup" \
  --description "Follow up the current long-running MGAP chunk" \
  --at "20m" \
  --keep-after-run \
  --session current \
  --session-key agent:deepblue:main \
  --message "MGAP long-run follow-up: first re-read the task state file, then inspect log/db/process state, update the state file, and report the smallest useful progress or blocker to Ewan." \
  --no-deliver \
  --expect-final
```

本机已验证：
- `openclaw cron add` / `openclaw cron list` / `openclaw cron show` / `openclaw cron status` 可用；
- `--session current --session-key agent:deepblue:main` 会落成真实 job，并解析为 `sessionTarget = session:agent:deepblue:main`；
- `--at` 需要写成 `3m` / `20m`，不要写 `+3m`。

### 每 2-3 个 chunk 后
补跑：

```bash
python3 -m mygooglealertpapers.cli report-batch
python3 -m mygooglealertpapers.cli report-normalization
python3 -m mygooglealertpapers.cli report-merge
```

### 每日收尾
导出一次 review queue：

```bash
python3 -m mygooglealertpapers.cli export-review-queue \
  --output data/exports/review_queue_20260506.jsonl
```

---

## 建议人工记录表（最少）

每个 chunk 记录一行：

| chunk_id | candidate_limit | prelinked | dispatch_requests | processed/runnable | canonical_total | review_blocked_total | notes |
|---|---:|---:|---:|---|---:|---:|---|

其中最关键的是：
- `prelinked`
- `dispatch_requests`
- `processed/runnable`
- `canonical_total`
- `review_blocked_total`

---

## 预期走势（正确时应该看到什么）

如果“递增资料库 + library_prelink”发挥作用，随着 chunk 前进，应该看到：

1. `canonical_paper` 总量上升，但增速逐渐变缓；
2. `library_prelinked_candidate_count` 或其占比逐步上升；
3. 单位 candidate 的 `dispatch_request_count` 逐步下降；
4. `post-prelink residual title requests` 逐步下降；
5. review queue 保持低位或缓慢增长，而不是爆炸式增长。

如果看不到这些趋势，就说明：
- chunk 划分方式不对；
- 现有库与当前 8000 封重叠没有想象中高；
- 或 provider 侧吞吐成了主瓶颈。

---

## 对 preprint -> journal 的临时规则

本轮固定策略：

- **不做自动 version-upgrade**
- 若新出现 journal 版，但旧库已有 preprint：
  - 允许后续通过扫库重建关系
  - 这一轮先保证不因为激进升级而污染 canonical 主记录

也就是说：
- 本轮优先目标是 **节省重复 enrich 成本 + 保持 canonical 稳定**
- 不是在本轮解决版本演化

---

## 最终建议

最推荐的实际落地顺序：

1. 一次性完成 8000 mails 的 `validate/import/parse/normalize`
2. 先跑 `4000 candidates` 的 pilot chunk
3. 通过后改用 `5000 candidates` regular chunk
4. 每 chunk 后固定跑 `report-enrichment + report-dedup + report-review-queue + report-cost`
5. 一旦出现异常，就降到 `2500 candidates` 或暂停

这是当前最稳、最可监控、也最符合 MGAP 现有能力边界的执行方案。
