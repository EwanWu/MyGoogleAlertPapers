# Package B context handoff（2026-04-16）

## 当前任务目标
在 `MyGoogleAlertPapers` 中完成 Package B 的最小 fallback guardrail 验证，判断 `conditional_sources_v3_fallback_guardrail` 是否可以作为新的主 treatment 候选。

## 关键约束（不要丢）
1. 计费/资源记录优先关注未来真实付费 LLM 调用；若某次 replay 没有付费 LLM 路径，要明确写出 none occurred。
2. `Unpaywall` 是否引入，必须靠受控对比实验决定，不能预设保留。
3. 任何 git 状态变更都要先向 Ewan 报告目标仓库和计划动作，再等批准。

## 已完成的实现
### 代码
- `src/mygooglealertpapers/pipeline/merge.py`
  - 新增 normalized-only fallback guardrail:
    - `fallback_reject_author_blob`
    - `fallback_review_author_pollution`
    - `fallback_review_similarity_threshold`
    - `fallback_review_sparse_metadata_similarity_threshold`
  - 对 fallback case 新增 `review` / `reject` 分流，不再全部 direct canonicalize。
- `tests/test_policy_and_merge_fallback.py`
  - 已补 guardrail 相关单测。
- `config/policy_profiles/conditional_sources_v3_fallback_guardrail.yaml`
  - 已落新 profile。
- `scripts/export_fallback_audit.py`
  - 已补 fallback audit 导出脚本。

### 文档 / 结果
- `docs/22-packageB-fallback-audit-kickoff-2026-04-15.md`
- `docs/23-packageB-fallback-audit-full30-summary-2026-04-15.md`
- `docs/24-packageB-guardrail-experiment-results-2026-04-16.md`
- `docs/validation/packageB-conditional-sources-v3-fallback-guardrail-replay-100-2026-04-15.{md,json}`

## 当前最可信的实验结论
固定 249-candidate slice 上：
- baseline: `baseline_guardrail`
- v2: `conditional_sources_v2`
- v3: `conditional_sources_v3_fallback_guardrail`

### v3 vs v2 结果
- merged: `249 -> 248`（仅少 1）
- fallback direct canonical: `30 -> 29`（少 1）
- fallback guardrail review: `0 -> 8`（新增 8）
- canonical: `204 -> 195`（少 9）
- review queue: `2 -> 10`（多 8）

### 解释
v3 的净效果是：
- 只损失 1 条 direct fallback accept
- 把 8 条高风险 case 从 direct canonical 路径挪到 review
- 另拦掉 1 条明显作者脚注/残片型污染

这和首轮 full-30 fallback LLM 审计是对齐的，方向正确，而且足够克制。

## 当前 authoritative artifact
### 主要 DB
- v2 replay DB:
  - `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v2_20260415.db`
- v3 manual replay DB（当前最重要的可恢复锚点）:
  - `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_manual_20260416.db`

### v3 manual replay DB 当前状态
- `paper_candidate_normalized = 249`
- `source_record = 951`
- `matched_source_record = 498`
- `merged_metadata_proposal = 248`
- `merge_review_queue = 10`
- `canonical_paper = 195`
- `cost_event = 497`
- `batch_run = 2`（仅 merge + dedup）

注意：这个 manual DB 是当前最稳的“上下文锚点”，因为它已经保留了 v2 的 `source_record`，只重跑了 v3 的 `merge + dedup`，适合做 guardrail 结论判断，不受 provider 波动影响。

## 昨晚中断点（非常重要）
- 曾尝试对 base 100 DB 做一次更完整的 v3 replay（包含 `enrich`）
- 现场日志关键信息：
  - `Planned 951 provider intent(s); 951 need work`
- 中断原因是 OpenClaw exec 会话被 `SIGTERM` 终止，不是已确认的 pipeline 逻辑失败
- 因此这次中断应视为“会话/执行环境中断”，不是“项目实验失败”

## 已验证
- `pytest -q tests/test_policy_and_merge_fallback.py` 已通过

## 下一步优先级（建议直接按这个顺序继续）
1. **先做完整 v3 replay 复现**
   - 目的：确认从 `mgap_pkg3_guardrail_100.db` 重新走 `enrich + merge + dedup` 后，结论仍与 manual replay 一致或接近
2. **再审新增的 8 条 review case**
   - 目的：判断这些 case 是否确实应被挡在 canonical 之外
3. **若 8 条多数最终仍是 review/reject**
   - 则可以把 v3 视为新的主 treatment 候选

## 推荐恢复命令
在项目根目录执行：

```bash
python3 scripts/replay_validation.py \
  --source-db data/mgap_pkg3_guardrail_100.db \
  --output-db data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_full_20260416.db \
  --policy-profile config/policy_profiles/conditional_sources_v3_fallback_guardrail.yaml \
  --report-out docs/validation/packageB-conditional-sources-v3-fallback-guardrail-replay-100-full-2026-04-16.json \
  --stages enrich merge dedup
```

## 如果又发生上下文压缩，至少保留这些事实
- 项目：`~/NewCareer/Openclaw/proj/MyGoogleAlertPapers`
- 当前阶段：Package B，验证 v3 fallback guardrail
- 当前最可信结果：v3 以极小 recall 代价挡下 8 个高风险 direct canonical case
- 当前 authoritative DB：`data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_manual_20260416.db`
- 下一步：跑 full replay，然后审核新增 8 条 review case
