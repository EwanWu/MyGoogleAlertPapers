# 163 本机正文抓取三种方案技术解析、利弊分析、获取与操作指南（2026-04-28）

## 目标

分析 163 本机 Google Scholar 邮件正文抓取提速的三种主方案：

- 方案 A：`history.back()` / UI back 保页返回
- 方案 B：按页驻留（page-resident sweep）
- 方案 C：基于稳定 `read_mid` / `read URL` 的 ID-first direct fetch

> 说明：原始验证文档还提到方案 D（双标签页 / worker-tab），但它更像方案 C 的扩展，不作为本报告的三种核心方案。

---

## 一、问题背景

当前 163 Windows-local 抓取链路已经证明：
1. **正文能抓到**；
2. **正文能接库**；
3. 当前主要瓶颈不在 ingest 边界，而在 **UI 导航成本**。

核心慢点来自：
- 打开一封邮件后，如果用 `goto(inbox_url)` 回列表，会丢失当前分页；
- 然后 `_ensure_list_page()` 需要从浅页重新 next/prev 恢复深页；
- 这个恢复成本在页内每封邮件上重复支付。

所以，本质问题不是“能不能抓”，而是：

**如何把“每封邮件都重复支付分页恢复成本”的结构，改成“每页支付一次，甚至完全绕开列表定位”的结构。**

---

## 二、三种方案的技术机制

## 方案 A：`history.back()` / UI back 保页返回

### 技术机制

打开正文后，不再 `goto(inbox_url)` 回收件箱，而是：
- 优先 `page.go_back()`；
- 如果回退后列表态不可用，再 fallback 到 `goto()` reload。

在当前实现里，对应逻辑是：
- `_return_to_inbox(...)`
- 优先返回 `method=history_back`
- 失败时 fallback 到 `history_back+goto_reload` 或 `goto`

### 它解决了什么

它解决的是 **“单封结束后如何回到刚才那一页”**。

也就是把“回列表”从一个**破坏上下文的重进 inbox**，变成**尽量保留同页上下文的历史回退**。

### 已有证据

已做 live benchmark：
- page 1 / 5 mails：`6.45 s/mail`
- page 12 / 20 mails，且 `--start-page 12`：`6.478 s/mail`
- wrapper page 12 / 10 mails：`5.831 s/mail`
- `return_method_counts` 均显示 `history_back=100%`

### 优点

- 改动最小；
- 不改 index schema；
- 风险最低；
- 对现有流程侵入小；
- 一旦有效，立刻降低深页重复恢复开销。

### 缺点 / 风险

- 依赖 163 当前前端 history 语义；
- 如果 SPA 路由、iframe、列表渲染状态不稳定，可能出现“回去了但列表不可操作”；
- 仍然属于**列表定位型抓取**，没有从结构上摆脱 UI 导航。

### 适用条件

- 想快速验证收益；
- 不想动数据模型；
- 需要一个近端、低风险 patch。

### 结论

**这是最好的第一刀。**

---

## 方案 B：按页驻留（page-resident sweep）

### 技术机制

让 sweep 的执行单元从“单封邮件”改为“单个 inbox page”：
1. 到 page N；
2. 收集 page N 的 rows；
3. 逐封处理；
4. 每封结束后回到 page N；
5. page N 完成后再翻到 page N+1。

当前代码里的关键状态是：
- `current_page_preserved`
- 仅在丢页时才调用 `_ensure_list_page()`

### 它解决了什么

它解决的是 **“恢复分页”的调用频率**。

即便仍然需要列表定位，B 也把成本从：
- **每封一恢复**
尽量变成：
- **每页最多少量恢复**。

所以 B 不是替代 A，而是 **A 的流程级放大器**。

### 已有证据

在验证文档中，A+B 是一起落地的最小 patch：
- 抓完单封优先 `history.back()`
- 页内引入 `current_page_preserved`
- 避免每封都 `_ensure_list_page()`

page 12 benchmark：
- 若还要从 page 1 traversal 到 page 12：`9.054 s/mail`
- 若直接 `--start-page 12`：`6.478 s/mail`

这说明：
- **页内保页是有用的**；
- **起始 traversal 仍会污染观测值**；
- 所以“页级工作流 + 直接深页起跑”才是合理使用方式。

### 优点

- 与当前 sweep 语义天然一致；
- 能显著减少 `_ensure_list_page()` 重复调用；
- 与 A 强兼容；
- 不需要立刻引入新 ID 体系。

### 缺点 / 风险

- 本质上仍然是列表驱动；
- 如果 163 打开/返回后重绘列表模块，仍可能需要校正；
- 对非常深页或长跑，仍无法达到 ID-first 那种量级的效率。

### 适用条件

- 当前主线路线上应默认启用；
- 适合作为 sweep 的标准执行形态，而不是实验分支。

### 结论

**B 本身不是终局，但它应成为当前默认工作流。**

---

## 方案 C：稳定 `read_mid` / read URL 驱动的 ID-first direct fetch

### 技术机制

核心思路是：
- 不再依赖“回到列表 -> 找到那一行 -> 点击打开正文”；
- 而是在 index 阶段或 live page source 中拿到稳定的邮件 read identifier；
- 直接构造 `readhtml3.jsp?mid=...` 打开正文。

当前代码已实现：
- `_node_id_mid_token()`
- `_page_visible_mid_map()`
- `_attach_read_mid_fields()`

当前 join 关系是：
- `row.node_id` 提取 `read_mid_token`
- page source regex 提取 `readhtml3.jsp?mid=...`
- 两者 token join 后得到 `read_mid`

### 它解决了什么

它解决的是 **“列表定位本身”**。

也就是说，它不是在优化“怎么回列表”，而是在尝试让正文抓取 **不再需要回列表**。

这是结构性优化，不是局部 patch。

### 已有证据

live probe：
- `row_count=86`
- `mid_map_count=25`
- `mapped_count=18`

ID-first smoke test（page 12 / 5 mapped mails）：
- `success=5`
- `avg_seconds_per_success=1.977`

larger prototype（page 12 -> 36）：
- `success=18`
- `avg_seconds_per_success=1.963`
- 但 page 13-36 `mapped_rows=0`

### 优点

- 性能潜力最高；
- 当 `read_mid` 可用时，当前实测速率约 `1.96-1.98 s/mail`；
- 相对 page 12 wrapper benchmark `5.831 s/mail`，粗略改善约 66%；
- 更适合断点续跑、重放、后续并行化；
- 从结构上摆脱深页线性恢复成本。

### 缺点 / 风险

- 当前 `read_mid` 覆盖率不足；
- 暴露明显受 page-local / cache-dependent 影响；
- 某页可抓到一批 mid，但翻到后续页不自动暴露；
- 需要继续 reverse engineer 163 前端数据结构 / prewarm 机制；
- 复杂度明显高于 A/B。

### 适用条件

- 适合作为中期主攻方向；
- 当前不适合“一刀切全量替换列表型抓取”；
- 更适合先做 hybrid：有 `read_mid` 走 direct fetch，缺失则 fallback 到 A+B 列表流程。

### 结论

**C 是性能上限最高的方向，但当前尚未具备全量独立落地条件。**

---

## 三、三种方案横向比较

| 维度 | 方案 A | 方案 B | 方案 C |
|---|---|---|---|
| 目标层级 | 单封返回列表 | 页级执行模型 | 去列表化正文抓取 |
| 技术本质 | 保住历史上下文 | 降低页恢复频次 | 用稳定 ID 直接读正文 |
| 改动复杂度 | 低 | 低到中 | 中到高 |
| 风险 | 低 | 低到中 | 中到高 |
| 当前证据强度 | 高 | 高 | 中 |
| 性能提升潜力 | 中 | 中 | 高 |
| 是否已适合默认 | 是 | 是 | 否（适合 hybrid） |
| 是否依赖 reverse engineering | 基本不依赖 | 基本不依赖 | 明显依赖 |
| 最适合角色 | 近端 patch | 当前主流程骨架 | 中期结构性升级 |

---

## 四、推荐路线

## 推荐结论（直接版）

### 现在就该做的

- **默认采用 A+B 作为生产主路径**
- 即：
  - `history.back()` 优先返回
  - 按页驻留处理
  - 使用 `--start-page` / `--start-from-current-page`，避免从 page 1 重建 traversal

### 接下来该攻的

- **继续推进 C，但以 hybrid 方式落地**
- 即：
  - 每页先探测 / prewarm `read_mid`
  - 有 `read_mid` 的行直接抓正文
  - 没有的少量残余样本走 A+B fallback

### 不建议的做法

- 不建议当前直接全面切换到纯 C；
- 不建议继续使用旧式 `goto(inbox_url)` + 每封 `_ensure_list_page()`；
- 不建议深页调试时还从 page 1 起跑。

---

## 五、获取与操作指南

这里把“获取”分成两层：
1. **获取运行环境 / 浏览器上下文**
2. **获取三种方案所需关键对象**（分页上下文、当前页、`read_mid`）

## 5.1 运行环境获取

### Step 1. 启动 Windows 真 Chrome

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\launch_163_chrome.ps1
```

### Step 2. 人工登录 163 邮箱并完成验证

要求：
- 保持 Chrome 打开；
- 最好停在 inbox；
- 若有验证码，先人工过验证。

### Step 3. 如需先做索引

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_index.ps1
```

### Step 4. 查看状态

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\check_163_index_status.ps1
```

---

## 5.2 方案 A+B 的操作指南

### 用法 1：小样本正文抓取

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sample.ps1 -Limit 10
```

适合：
- 接库验证；
- 小范围 smoke test；
- 不强调深页精确恢复的场景。

### 用法 2：从指定深页开始 sweep（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartPage 12 -PageLimit 1 -MaxTargets 20
```

适合：
- 深页 targeted benchmark；
- 避免从 page 1 重建 traversal；
- 验证 A+B 在某个目标页的稳态性能。

### 用法 3：从当前可见页恢复（推荐恢复语义）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_local\run_163_body_fetch_sweep.ps1 -StartFromCurrentPage -PageLimit 1 -MaxTargets 20
```

适合：
- Chrome 已手动停在目标页；
- 调试中断后续跑；
- 不想再自动翻页恢复。

### 方案 A+B 的成功判据

观察输出 summary：
- `return_method_counts.history_back` 是否接近 100%
- `avg_seconds_per_success` 是否落在 `~5-7 s/mail`
- 是否无 `page drift`
- 是否不再频繁触发 `_ensure_list_page()` 式恢复

---

## 5.3 方案 C 的获取与操作指南

### 当前可获取的关键对象

C 方案要先“获取 `read_mid`”。当前已有两条路径：

1. **从 row.node_id 派生 token**
2. **从 page source regex 抓 `readhtml3.jsp?mid=...`**

然后做 exact token join，得到：
- `read_mid_token`
- `read_mid`
- `read_route_id`
- `read_mid_source`

### 当前建议的操作方式

#### 方式 1：先让 index / sweep 持续产出 `read_mid` 字段

这是当前最稳的“获取”方式。先积累覆盖率，而不是直接全切到 direct fetch。

#### 方式 2：做 page-prewarm probe

建议实验：
1. 到新页；
2. 先点击 1 封邮件触发 read module / iframe 缓存；
3. 回页后重新抓 page source `mid`；
4. 观察 `mapped_rows` 是否提升。

如果有效，再考虑该页多数样本走 direct fetch。

#### 方式 3：只对 mapped rows 走 direct fetch

即：
- `read_mid` 已拿到 -> direct fetch
- `read_mid` 缺失 -> A+B fallback

这就是当前最合理的 hybrid 落地方式。

### 方案 C 的成功判据

- `mapped_rows / row_count` 覆盖率持续提高；
- direct fetch 保持 `~2 s/mail` 左右；
- 新页不再出现大面积 `mapped_rows=0`；
- 不依赖偶然缓存状态。

---

## 六、我对这三种方案的判断

## Known（已有证据支持）

- A+B 已经在 live benchmark 中显著优于旧式 `goto + ensure_list_page`。
- 在 page 12 这类深页场景，正确使用 `--start-page` 后，A+B 已能稳定落在 `~6 s/mail`。
- C 在 `read_mid` 可用时速度非常强，约 `~2 s/mail`。
- 当前 C 的主问题不是“能不能直读”，而是“能不能稳定拿到足够多的 `read_mid`”。

## Inferred（基于当前证据的合理推断）

- A 和 B 应被视为一个组合，而不是彼此替代的竞争方案。
- 真正的长期最优架构大概率是 **B 作为工作流骨架 + C 作为正文读取主通道 + A 作为 fallback 返回机制**。
- 如果 `read_mid` 覆盖率问题被解决，C 会成为吞吐主路径。

## Speculative（仍需验证）

- 163 某些更深层前端数据结构里，可能存在可稳定提取 page-local `mid` 的对象，不必完全依赖已缓存 page source。
- page-prewarm 很可能能把 `mapped_rows` 从 0 拉起来，但这一点还需要针对新页做实证。

---

## 七、最终建议

### 如果目标是“现在就稳定推进全量正文抓取”

选：**A+B**

### 如果目标是“把正文抓取速度再砍到当前的 1/3 左右”

攻：**C（先 hybrid，不要纯切）**

### 最合理的组合路线

1. **短期生产：A+B 默认化**
2. **中期优化：C 做 page-prewarm + mapped-row hybrid**
3. **远期再考虑 D（worker-tab）作为 C 的增强，而不是替代 A/B/C 的当前主线**

---

## 相关文件

- `docs/validation/163-local-body-sweep-and-ingest-validation-20260424.md`
- `runbooks/163-local-mail-modular-pipeline-2026-04-23.md`
- `runbooks/163-local-mail-read-runbook-2026-04-22.md`
- `scripts/windows_local/read_163_scholar_with_manual_pause.py`
- `scripts/windows_local/run_163_body_fetch_sweep.ps1`
- `scripts/windows_local/run_163_body_fetch_sample.ps1`
