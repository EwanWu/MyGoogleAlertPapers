# 163 本机读取 runbook (2026-04-22)

## 目标

在 **Windows 本机真实 Chrome** 中完成人工登录/验证，然后在同一台机器上运行可暂停、可恢复的读取控制器，优先建立 163 中 Google Scholar 邮件的列表索引。

## 为什么采用本机方案

- 当前 WSL/服务器出口 IP 为美国 IP，163 IMAP 被风控拒绝
- 当前代理出口与直连是同一美国 IP，不能解除 IMAP 风控
- WSL 内浏览器能打开登录页，但验证码和会话复用不稳定
- 最稳路径是：**Windows 真 Chrome + 人工验证 + 本机批量读取**

## 核心文件

- 启动 Chrome: `scripts/windows_local/launch_163_chrome.ps1`
- 运行索引: `scripts/windows_local/run_163_index.ps1`
- 运行正文样本抓取: `scripts/windows_local/run_163_body_fetch_sample.ps1`
- 检查状态: `scripts/windows_local/check_163_index_status.ps1`
- 单页计数诊断: `scripts/windows_local/count_163_scholar_page.ps1`
- 主控制器: `scripts/windows_local/read_163_scholar_with_manual_pause.py`
- 状态文件: `data/task_state/163_mail_read_local_state.json`
- 输出索引: `data/raw_mail_exports/163_scholar_local/scholar_index.jsonl`
- 诊断目录: `data/raw_mail_exports/163_scholar_local/diagnostics/`
- 验证记录: `docs/validation/163-local-scholar-index-validation-20260423.md`
- 解耦方案: `runbooks/163-local-mail-modular-pipeline-2026-04-23.md`

## 当前验证结论（2026-04-23）

当前 163 本机 Scholar 索引链路已完成一轮有效校准。

- 三页未读列表索引结果：`277` 封
- 分页分布：`94 / 96 / 87`
- 当前每页展示设置：`100` 封
- 页面 1 单页计数验证：`total_letter_nodes_visible=100`，`scholar_sender_visible=94`，`unique_scholar_sequence_dedup_across_scan=94`
- 跨页去重检查：`mail_key` 与 `sequence_key` 在 `1-2 / 1-3 / 2-3` 间重叠均为 `0`

当前判断：`277` 是可信的 3 页索引结果，不是明显的重复放大，也不是先前那种漏抓到 `135` 的回归结果。

## 已确认并修复的两类根因

### 1. 视口过滤导致页内严重漏抓

之前脚本把候选行限制为“当前视口内可见”，导致每页只保留约 `45` 条左右。

修复后改为：
- 接受 `non-hidden + non-zero-size` 的信件行节点
- 不再要求节点必须和当前 viewport 相交

### 2. Scholar 主题词过滤过窄

之前脚本只稳定接受以下子类型：
- `新增了 X 次引用`
- `新文章`
- `相关文章`

但漏掉了大量：
- `新的相关研究工作`

修复后改为：
- 先确认 sender 是 `Google 学术搜索快讯`
- 再确认该行是 `[收件箱]` 邮件行
- 不再依赖过窄的子类型关键词白名单

### 3. 去重策略已升级为局部序列去重

当前去重不再只靠单条标题，而是使用“中心邮件 + 前 3 封 + 后 3 封”的局部序列 `sequence_key` 做跨滚动快照去重，以降低：
- 同名不同邮件被误合并
- 同一段列表被重复扫描时重复计数

## 最小执行步骤（给人）

### Step 1. 启动专用 Chrome

在 Windows PowerShell 中：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\launch_163_chrome.ps1
```

### Step 2. 人工完成登录/验证

在打开的 Chrome 中：
- 登录 163 邮箱
- 完成滑动验证或其他安全验证
- 保持浏览器窗口打开
- 最好停留在邮箱主界面或收件箱

### Step 3. 跑第一轮索引

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1
```

### Step 4. 如果提示等待人工验证

- 回到 Chrome 完成验证
- 然后再次执行相同命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1
```

### Step 5. 查看当前状态

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\check_163_index_status.ps1
```

### Step 6. 如果怀疑页内重复或漏抓，先做单页计数诊断

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\count_163_scholar_page.ps1 -ScrollSteps 12
```

推荐先看这几个字段：
- `total_letter_nodes_visible`
- `scholar_sender_visible`
- `dedup_within_snapshot`
- `unique_scholar_sequence_dedup_across_scan`

在当前已验证布局上，如果页面展示 100 封，而单页 Scholar 占多数，`unique_scholar_sequence_dedup_across_scan` 应接近真实单页 Scholar 数，而不应像早期回归那样卡在 `45` 左右。

## 暂停 / 恢复机制

### 触发暂停的条件

- 仍在登录页
- 检测到验证码/安全验证
- 页面报错
- 找不到可继续处理的 inbox/list 页面

### 暂停时会发生什么

控制器会：
- 写状态到 `data/task_state/163_mail_read_local_state.json`
- 保存截图/HTML 到 diagnostics 目录
- 输出 `waiting_manual_verification` 或其他状态

### 如何恢复

人工解决问题后，**不要 reset**，直接重跑：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1
```

## 上下文已满 / 硬重置预案

这个 runbook 的目的就是让任务不依赖当前聊天上下文。

即使聊天被 compaction 或硬重置，恢复时只需要看：

1. `runbooks/163-local-mail-read-runbook-2026-04-22.md`
2. `data/task_state/163_mail_read_local_state.json`
3. `data/raw_mail_exports/163_scholar_local/diagnostics/`
4. `data/raw_mail_exports/163_scholar_local/scholar_index.jsonl`

### 恢复原则

- 如果 state 文件显示 `waiting_manual_verification`：先去 Chrome 完成人工验证，再重跑 `run_163_index.ps1`
- 如果 state 文件显示 `indexing` 或 `completed`：检查 index 文件是否持续增长
- 如果 diagnostics 里有最新截图/HTML：优先用它判断页面卡在哪

## 当前阶段边界

当前控制器首先解决的是：
- 人工验证暂停
- 状态持久化
- 可恢复执行
- 首轮列表索引
- 当前这套 163 布局上的 Scholar 列表校准

当前还没有承诺：
- 8000+ 正文一次性全抓
- 每个 163 布局都自动精准识别
- 正文抓取阶段的正文去重与断点续跑策略

下一阶段应基于当前已验证的 `277` 行 index，扩展为**解耦的两步**：
1. 先做 `10-20` 封小样本正文抓取，并验证可接入现有 SQLite 资料库
2. 再独立推进全量正文抓取

不要把正文抓取与后续 `enrich / merge / dedup / enrich-paper-oa` 长流程耦合在一起。该部分单独作为离线建库阶段处理。详见：`runbooks/163-local-mail-modular-pipeline-2026-04-23.md`

当前已补第一版小样本正文抓取命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -Limit 10
```

该命令会把成功结果写到：
- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch.jsonl`

失败与诊断写到：
- `data/raw_mail_exports/163_scholar_local/scholar_body_fetch_failures.jsonl`
