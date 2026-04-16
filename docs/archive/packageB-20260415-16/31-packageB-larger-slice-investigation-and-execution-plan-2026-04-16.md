# Package B larger-slice 调查与执行计划（2026-04-16）

## 1. 这次先回答三个问题
### Q1. 为什么之前没有出现这个问题？
### Q2. 是哪一个改动引起了它？
### Q3. 如果短期不能彻底解决，能否规避？

## 2. 当前调查结论

### 2.1 为什么之前没出现
**Known**
- 之前稳定跑通的是：
  - 100-mail live slice (`data/mgap_pkg3_guardrail_100.db`)
  - 249-candidate same-batch replay（v2/v3/v4 相关 replay）
- 这次 larger-slice150 的 seed 规模明显更大：
  - `150 mails / 92 Scholar mails / 368 normalized candidates / 1405 provider intents`
- 之前 100-mail 详细验证文档里的 scan 命令是：
  - `scan-mailbox --limit 100 --unseen-only`
- 这次 large-slice 脚本里用的是：
  - `scan-mailbox --limit 150`
  - **没有 `--unseen-only`**

**Inferred**
- 这次问题没有在 earlier runs 暴露，不代表它不存在，更可能是：
  1. **样本更大**，provider 调用数从 ~`951/996` 级别上升到 `1405`
  2. **seed 组成变了**，因为没有 `--unseen-only`，更可能纳入更旧、更杂的历史邮件和 metadata pattern
  3. 先前较小 slice 没踩到这个 provider/network 边缘条件

换句话说，**larger slice 暴露的是 latent orchestration weakness，不一定是新引入 bug。**

### 2.2 哪个改动引起了它
#### 先说 payload parsing bug
**Known**
- 第一个 larger-slice 失败是 OpenAlex payload 空值链：
  - `primary_location.source = null`
- 这个问题已经修掉。

#### 再说当前 stall
**Known**
- 当前 stall 发生在 `enrich-candidates`
- 发生位置在 enrich 阶段，**早于 merge / v3 / v4 fallback guardrail 逻辑**
- 因此它**不是**最近 fallback/v4 规则改动直接导致的

**Inferred**
- 目前没有证据表明“最近某一条策略改动”直接引入了 stall
- 更像是这几个因素叠加触发：
  1. **workload change**: 100 → 150 mails，249 → 368 normalized candidates，951 → 1405 intents
  2. **seed composition change**: 去掉 `--unseen-only`
  3. **orchestration weakness already existed**: provider 调用一旦挂住，当前 replay 缺少足够强的 timeout / watchdog / checkpoint / failure artifact

因此当前最合理的归因是：

> **触发它的不是 v4 策略改动，而是 larger-slice + 不同 seed 组成，把一个原本潜伏的 enrich orchestration 鲁棒性问题暴露出来了。**

### 2.3 如果不能立即彻底解决，能否规避
可以，至少有三层规避：

#### Layer A. 运行层规避
- 给 replay stage 加 wall-clock timeout
- 超时后强制写 failure artifact
- 避免“挂死但什么都没产出”的黑盒状态

#### Layer B. 可观测性规避
- enrich 增加 progress logging
- enrich 增加阶段性 commit/checkpoint
- 这样即使挂住，也能知道卡在大概哪个 provider / 进度段

#### Layer C. workload 规避
如果短期仍不稳定，可以先：
- 固定使用当前已建好的 150-mail seed，不重新 scan mailbox
- 必要时回退到更保守的 smoke 子集或 provider 子集，先定位卡点，再恢复全量 replay

## 3. 执行原则
这次不直接盲重跑 full larger-slice。先做最小必要 hardening，再重跑。

## 4. 计划中的最小执行包
### P0. 已完成
- 修复 OpenAlex `primary_location.source = null` 空值链
- replay_validation 现在已经能在普通失败时落 failure artifact

### P1. 现在开始做
1. 给 `replay_validation.py` 增加 **stage timeout**
2. 给 `pipeline/enrich.py` 增加 **progress logging + checkpoint commit**
3. 这样下次就算再 stall，也能知道：
   - 卡在什么阶段
   - 大致推进到哪里
   - DB 至少留下部分可解释状态

### P2. 然后再执行
1. 用现有 `seed DB` 重新做 `v2 smoke enrich`
2. 如果 smoke 通过：
   - 完成 `v2 merge + dedup`
   - 再跑 `v4 enrich + merge + dedup`
3. 如果 smoke 仍失败：
   - 用新的 failure artifact 定位具体 provider / 进度段
   - 再决定是修 provider call、降 batch、还是暂时规避某个 provider

## 5. 如何控制上下文 overflow
这次执行按下面方式做，避免对话上下文被长跑和轮询吃掉：
1. 先写调查/计划文档（本文件）
2. 长流程尽量把状态写入：
   - `docs/validation/*.md|json`
   - `data/logs/*.log`
   - DB checkpoint
3. 不做高频轮询，只在关键阶段后检查
4. 让失败本身也产出结构化 artifact，避免再次只能靠聊天记忆复盘

## 6. 当前结论（一句话版）
当前 larger-slice 的主要问题**不是策略过拟合，也不是 v4 规则本身**，而是 **larger workload 暴露了 enrich orchestration 的 latent robustness gap**；因此下一步应先补 timeout / checkpoint / failure-artifact，再恢复策略对照运行。
