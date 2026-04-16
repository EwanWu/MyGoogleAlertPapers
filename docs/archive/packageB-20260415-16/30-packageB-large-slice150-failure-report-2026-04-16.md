# Package B large-slice150 validation failure report（2026-04-16）

## 结论
本轮 `larger-slice150` 验证**未完成**。流程只完成了 seed 构建，随后在 **v2 replay 的 enrich 阶段** 即失败，因此 **v2 / v4 对比、provider latency/hit-rate 稳定性验证、v4 相对 v2 的整体收益判断**，本轮都**不能下结论**。

## 已完成到哪一步
### 1) seed 构建完成
运行脚本：`scripts/run_packageB_large_slice_replay_20260416.sh`

已成功完成：
- `init-db`
- `scan-mailbox --limit 150`
- `parse-mails --limit 500`
- `normalize-candidates --limit 800`
- `report-batch`
- `report-normalization`

seed 产物：`data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`

seed 统计（Known）
- scanned mails: `150`
- detected Scholar mails: `92`
- extracted candidates: `368`
- normalized candidates: `368`
- DOI extracted: `161`
- PMID extracted: `5`
- PMCID extracted: `4`
- arXiv extracted: `9`
- enrich 前 planned provider intents: `1405`

seed DB 中 replay 前状态（Known）
- `paper_candidate`: `368`
- `paper_candidate_normalized`: `368`
- `candidate_enrichment_status`: `0`
- `source_record`: `0`
- `merged_metadata_proposal`: `0`
- `canonical_paper`: `0`
- `merge_review_queue`: `0`
- `cost_event`: `610`（均来自 seed 构建阶段；provider 为空）
- `batch_run`: `3`（`scan / extract_candidates / normalize_candidates`）

### 2) v2 replay 未完成
v2 输出 DB：`data/mgap_pkgB_large_slice150_replay_v2_20260416_slice150.db`

该 DB 是从 seed 拷贝后、在 replay 开始时被 reset 过的中间态（Known）：
- `paper_candidate`: `368`
- `paper_candidate_normalized`: `368`
- `candidate_enrichment_status`: `0`
- `source_record`: `0`
- `merged_metadata_proposal`: `0`
- `canonical_paper`: `0`
- `merge_review_queue`: `0`
- `cost_event`: `0`
- `batch_run`: `0`

说明失败发生在 replay 真正写出 enrich 结果之前。

### 3) v4 replay 完全未开始
`data/mgap_pkgB_large_slice150_replay_v4_20260416_slice150.db` 未生成。

### 4) validation 报告未生成
以下计划产物均不存在：
- `docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.{json,md}`
- `docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.{json,md}`
- `docs/validation/packageB-large-slice150-summary-20260416_slice150.{json,md}`

## 失败阶段与原因
### 失败阶段（Known）
- 阶段：`v2 replay -> enrich-candidates`
- 触发点：`scripts/replay_validation.py` 调用 `python3 -m mygooglealertpapers.cli enrich-candidates --limit 1000000`

### 直接错误（Known）
日志：`data/logs/packageB_large_slice150_20260416_slice150.nohup`

关键栈：
```python
File "/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/src/mygooglealertpapers/pipeline/enrich.py", line 227, in enrich_candidates
    venue = (item.get('primary_location') or {}).get('source', {}).get('display_name')
AttributeError: 'NoneType' object has no attribute 'get'
```

### 根因判断（Inferred）
OpenAlex DOI batch 返回的某个 `item` 中：
- `primary_location` 不是缺失，而是存在但其中 `source = null`
- 当前代码写法只防住了 `primary_location is None`，**没有防住 `primary_location['source'] is None`**

因此这行：
```python
(item.get('primary_location') or {}).get('source', {}).get('display_name')
```
在 `source` 为 `None` 时仍会变成：
```python
None.get('display_name')
```
从而触发异常。

### 最小修复方向（Inferred）
至少改成二级空值防护，例如：
```python
primary_location = item.get('primary_location') or {}
source = primary_location.get('source') or {}
venue = source.get('display_name')
url = primary_location.get('landing_page_url')
```
并检查同一批 payload 的其它链式 `.get()` 是否存在同类风险。

## 对 larger-slice 现象的实际观察
### provider latency / hit-rate 稳定性
**本轮无法判断**（Known）。

原因：replay enrich 在第一阶段即崩溃，没有生成任何 provider 级 replay 统计，也没有生成 v2/v4 validation report。

### v4 相对 v2 的整体收益
**本轮无法判断**（Known）。

原因：v2 都没有跑完，v4 未启动，因此不能用本轮数据讨论 `review / canonical / matched_source_record / provider latency` 的增减。

### larger slice 暴露出的真实信号
#### 1. larger slice 更容易触发“之前小样本没踩到的 payload 形态”
这次 150-mail slice 一共形成了 `1405` 个 provider intents，明显高于此前较小样本。虽然这不代表 bug 只会在大样本出现，但 **larger slice 的价值之一就是更快暴露 provider payload 边缘形态**，这次已经体现出来了（Known + Inferred）。

#### 2. 当前瓶颈不是策略优劣，而是 enrich orchestration 的鲁棒性
这次失败完全发生在 policy 比较之前，说明在进入“讨论 v4 是否优于 v2”之前，系统还需要先保证 replay 能稳定吃下更杂的 provider payload（Known）。

## 本轮暴露出的 orchestration 问题
### 1) 上下文压缩风险（Known + Inferred）
这次 run 失败得很早，导致计划中的 `docs/validation/*.json|md` 一个都没生成。若只靠对话上下文而不及时落文档，很容易丢失：
- seed 的实际规模
- 失败发生在哪个 stage
- v2 DB 是“copy 后 reset 的空 replay 态”而不是“跑了一半”
- 具体异常来自 OpenAlex batch payload 的空值链

这说明 larger-slice / 长流程任务里，**中间状态必须尽量外化到日志、DB、文档**，不能只依赖会话记忆。

### 2) 过频繁轮询风险（Inferred）
本次跟踪中已经刻意使用低频等待，没有因为轮询本身打断任务；但 larger-slice replay 本身更长、更容易产生大日志和多阶段状态。若频繁轮询：
- 会增加无效上下文噪音
- 会放大“盯进度而不是沉淀产物”的倾向
- 对长流程调试帮助有限，反而更容易把关键异常埋在大量重复进度里

因此这次 run plan 里“长间隔检查 + 先保留中间产物”是对的，后续仍应坚持。

### 3) 失败后缺少自动 failure summary
当前脚本在 replay 失败后直接退出，导致不会生成一个最小 failure artifact。这样后续分析只能回日志和 DB 反推，增加了恢复成本（Known）。

## 建议的下一步
### 必做
1. 修复 `src/mygooglealertpapers/pipeline/enrich.py` 中 OpenAlex batch 对 `primary_location.source` 的空值处理。
2. 重新运行 `scripts/run_packageB_large_slice_replay_20260416.sh`。
3. 这次完成后再看：
   - provider latency / hit-rate 是否稳定
   - v4 相对 v2 是否仍保持“小收益但克制”的模式
   - larger slice 上是否出现新的 merge/review 结构变化

### 很值得顺手补上的工程增强
1. 在 `replay_validation.py` / run script 里增加 failure summary 输出，至少落一个 markdown/json，记录：
   - 失败 stage
   - 异常摘要
   - 已生成产物
   - 未生成产物
2. 对 enrich 的 batch provider payload 做更系统的 defensive parsing，避免再次因单个字段为 null 整轮崩溃。

## Known / Inferred / Speculative
### Known
- seed 已完成，规模为 `150 mails / 92 Scholar mails / 368 normalized candidates`
- replay 前 planned provider intents 为 `1405`
- v2 在 `enrich-candidates` 阶段失败
- 直接异常是 `primary_location.source` 相关的空值链访问
- v4 未开始，validation docs 未生成

### Inferred
- 触发源大概率是 OpenAlex DOI batch 某条返回里 `primary_location.source = null`
- 当前 larger-slice 暴露的是 payload 鲁棒性问题，不是 policy 优劣问题
- 缺少 failure artifact 会放大上下文压缩和恢复成本

### Speculative
- 修复空值链后，larger-slice 的 provider hit-rate / latency 模式大概率才能开始有可解释性；目前任何关于 v2 vs v4 的收益判断都不应提前外推。
