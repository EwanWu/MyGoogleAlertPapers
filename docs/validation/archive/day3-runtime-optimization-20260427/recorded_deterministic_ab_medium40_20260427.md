# Deterministic recorded-payload A/B 报告 (limit=40, 2026-04-27)

## 实验设计

1. **live_baseline** — 真实网络请求，同时把每个 HTTP 响应写入 fixture

2. **baseline_replay** — 用同一 fixture 重放，验证 replay 自身是否正确

3. **experiment_replay** — 用同一 fixture 重放，但开启 `title_payload_reuse_enabled`


如果 experiment_replay 与 baseline_replay 的最终输出一致，说明 title payload reuse
的优化没有引入语义变化，因为两者用的是完全相同的 provider 响应。

## 核心对比表

| 指标 | live_baseline | baseline_replay | experiment_replay | replay vs baseline |

|---|---:|---:|---:|---:|

| matched_src_rec | 100 | 100 | 100 |  |
| canonical | 33 | 33 | 33 |  |
| review_queue | 1 | 1 | 1 |  |
| norm_fallback | 4 | 4 | 4 |  |

## Dispatch 统计

| 指标 | live_baseline | baseline_replay | experiment_replay |

|---|---:|---:|---:|

| planned_intents | 160 | 160 | 160 |
| runnable_intents | 160 | 160 | 160 |
| dispatch_groups | 138 | 138 | 138 |
| dispatch_requests | 127 | 127 | 127 |
| request_savings | 33 | 33 | 33 |
| reuse_groups | 0 | 0 | 6 |
| reuse_intents | 0 | 0 | 12 |
| reuse_requests | 0 | 0 | 6 |
| reuse_savings | 0 | 0 | 6 |
| fanout_candidates | 22 | 22 | 22 |

## Fixture 信息

- fixture 路径: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_medium40_20260427.jsonl`
- fixture 行数: `91`

## 结论

**在 deterministic recorded-payload 条件下：**

- `matched_source_record_count`、`canonical_paper_count`、`merge_review_queue_count`
  在 baseline_replay 和 experiment_replay 中**完全一致**（100 / 33 / 1）

- experiment_replay 中 `shared_title_reuse_request_savings = 6`，
  说明优化确实被触发并节省了 6 个 provider title 请求

- **语义稳定性判定：PASS** — title payload reuse 没有导致任何最终输出变化


**对 live A/B 漂移的解释：**
  之前 smoke12 live 实验中 `matched_source_record_count` 在 28-37 间漂移，
  原因是 live provider 对同标题查询返回的排序不稳定（provider 侧行为），
  不是 title payload reuse 优化引入的语义问题。deterministic fixture 消除该噪声后，
  证明优化本身没有改变 merge/dedup 结果。

**建议：** title payload reuse 可以解除 feature-flag 并升为默认行为。