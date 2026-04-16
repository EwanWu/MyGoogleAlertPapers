# Package B large-slice replay run plan（2026-04-16）

## 目标
在避免过拟合的前提下，用 **更大 real-mail slice** 验证 `v4` 是否仍保持整体收益，并观察更大规模运行时出现的现象。

## 设计
采用两段式：
1. 先构建一个新的固定 normalized seed
2. 再在同一 seed 上做 `v2` vs `v4` same-batch replay

这样可以把 live mailbox 漂移和 policy 差异分开。

## 当前决定
- mailbox account: `issac`
- larger slice size: `150 mails`
- 原因：
  - 明确大于既有 100-mail slice
  - 又不至于把 enrich 时间和上下文风险一下拉得过大
  - 更适合作为“更大 slice 的第一轮稳定验证”

## 运行产物
- seed DB:
  - `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- v2 replay DB:
  - `data/mgap_pkgB_large_slice150_replay_v2_20260416_slice150.db`
- v4 replay DB:
  - `data/mgap_pkgB_large_slice150_replay_v4_20260416_slice150.db`
- v2 report:
  - `docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.{json,md}`
- v4 report:
  - `docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.{json,md}`
- summary:
  - `docs/validation/packageB-large-slice150-summary-20260416_slice150.{json,md}`
- run log:
  - `data/logs/packageB_large_slice150_20260416_slice150.log`

## 运行脚本
- `scripts/run_packageB_large_slice_replay_20260416.sh`

## 过程约束
1. 避免过频繁轮询，只在关键阶段或较长间隔后检查进度。
2. 先保留运行日志和中间产物，再做分析，防止上下文压缩丢状态。
3. 重点观察：
   - larger slice 上 provider latency / hit-rate 是否稳定
   - v4 的 review/canonical 变化是否仍然克制
   - 是否出现新的重复错误模式
   - 是否出现上下文/运行 orchestration 层面的额外负担

## 结果解释目标
最终不只看 `+1/-1` 级别数字，而是总结：
- 哪些规律在更大 slice 上稳定复现
- 哪些现象只是小样本偶然
- 接下来应该改规则、改流程，还是改运行方式
