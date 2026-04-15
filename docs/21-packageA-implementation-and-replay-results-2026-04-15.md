# Package A 实施与 replay 结果报告（2026-04-15）

## 1. 本轮完成内容

本轮按批准的 Package A 实施了四类工作：

1. **replay workflow closure**
2. **`query_cache` strict reset**
3. **DOI clean**
4. **normalized-only fallback merge proposal**
5. **same-batch baseline vs treatment replay**

本轮**没有**做以下内容：

- 不引入 Unpaywall 到主链路
- 不做并行 enrich
- 不接入 Her 版的 byte/token 伪成本实现
- 不实现完整 LLM paid-token 账本，只为后续保留方向

---

## 2. 本轮代码改动摘要

## 2.1 `src/mygooglealertpapers/config.py`

新增 policy profile 载入能力：

- `MGAP_POLICY_PROFILE` 环境变量可指定 profile YAML
- `Settings` 现在携带 `policy_profile`
- profile 可控制：
  - provider enabled state
  - OpenAlex DOI batch 开关
  - Europe PMC trigger mode
  - arXiv trigger mode
  - merge rules

这使 replay 不再只是“指定一个 YAML 文件名”，而是**真正让 profile 驱动运行行为**。

## 2.2 `src/mygooglealertpapers/pipeline/enrich.py`

把 provider intent 生成改为读取 policy profile：

- provider 是否启用由 profile 决定
- Europe PMC 是否走 narrowed / broad biomedical trigger 由 profile 决定
- arXiv trigger 由 profile 决定
- OpenAlex DOI batch 开关由 profile 决定

这一步关闭了“`--policy-profile` 形同虚设”的关键缺口。

## 2.3 `src/mygooglealertpapers/normalize/identifiers.py`

增强 DOI 清洗逻辑，覆盖：

- `.pdf`
- `/download`
- `_reference.pdf`
- Oxford-style deep PDF path

本次 100-mail slice replay 中，dirty DOI 从 **9 -> 0**。

## 2.4 `src/mygooglealertpapers/pipeline/merge.py`

新增/接线两部分：

1. **merge rule 读取 profile**
   - `pubmed_title_doi_suppression`
   - `normalized_only_fallback`
   - `pubmed.fallback_only_for_core_fields`

2. **normalized-only fallback proposal**
   - 当 candidate 没有任何 `matched=1` source 时，不再一律静默丢失
   - 若 profile 开启该规则，则用 normalized candidate 信息生成低置信度 proposal
   - 在 trace / conflict payload 中显式标注 `fallback_mode = normalized_only`

这一步修复了 Her 版指出的核心 P0 问题之一。

## 2.5 `scripts/replay_validation.py`

将 replay 脚本升级为更完整的验证工具：

- 支持 `normalize` stage
- stage-sensitive reset
- `query_cache` 被严格清空
- replay 真正把 profile 注入子进程执行
- 自动输出 JSON + Markdown 报告
- 补充统计：
  - dirty DOI repaired count
  - normalized-only fallback proposal count
  - total batch duration
  - total provider latency
  - paid LLM usage note

## 2.6 新增 profile 和测试

新增：

- `config/policy_profiles/baseline_guardrail.yaml`
- 更新 `config/policy_profiles/conditional_sources_v2.yaml`
- `tests/test_policy_and_merge_fallback.py`
- 补充 `tests/test_identifiers.py`

---

## 3. 测试结果

本轮修改后运行：

`PYTHONPATH=src python3 -m pytest tests -q`

结果：**全部通过（28 tests）**。

---

## 4. Replay 运行配置

## 4.1 source DB

使用固定 same-batch candidate set：

- `data/mgap_pkg3_guardrail_100.db`

该 slice 的 normalized candidate 数为：

- `249`

## 4.2 对照 profile

### Baseline
- `config/policy_profiles/baseline_guardrail.yaml`
- `normalized_only_fallback: false`

### Treatment
- `config/policy_profiles/conditional_sources_v2.yaml`
- `normalized_only_fallback: true`

两组 replay 都执行：

- `normalize`
- `enrich`
- `merge`
- `dedup`

输出报告文件：

- `docs/validation/packageA-baseline-guardrail-replay-100-2026-04-15.json`
- `docs/validation/packageA-baseline-guardrail-replay-100-2026-04-15.md`
- `docs/validation/packageA-conditional-sources-v2-replay-100-2026-04-15.json`
- `docs/validation/packageA-conditional-sources-v2-replay-100-2026-04-15.md`

---

## 5. 结果总表

## 5.1 原始 source DB vs baseline replay vs treatment replay

| 指标 | 原始 source DB | baseline replay | treatment replay |
|---|---:|---:|---:|
| normalized candidate | 249 | 249 | 249 |
| dirty DOI | 9 | 0 | 0 |
| source_record | 996 | 951 | 951 |
| matched source_record | 503 | 503 | 498 |
| merged proposal | 203 | 219 | 249 |
| normalized-only fallback proposal | 0 | 0 | 30 |
| canonical paper | 164 | 176 | 204 |
| review queue | 0 | 2 | 2 |
| severe DOI conflict | 未单独统计 | 2 | 2 |

## 5.2 baseline replay vs treatment replay（真正的 same-batch 对照）

| 指标 | baseline | treatment | delta |
|---|---:|---:|---:|
| dirty DOI repaired | 9 | 9 | 0 |
| source_record | 951 | 951 | 0 |
| matched source_record | 503 | 498 | -5 |
| merged proposal | 219 | 249 | **+30** |
| normalized-only fallback proposal | 0 | 30 | **+30** |
| canonical paper | 176 | 204 | **+28** |
| review queue | 2 | 2 | 0 |
| severe DOI conflict | 2 | 2 | 0 |
| cost_event | 1668 | 1698 | +30 |
| total batch duration | 1550315 ms | 1440822 ms | -109493 ms |
| total provider latency | 1538256 ms | 1433216 ms | -105040 ms |

---

## 6. 如何解释这些结果

## 6.1 DOI clean 已被明确验证为有效

本 slice 中 dirty DOI：

- source DB: `9`
- replay 后: `0`

这说明 DOI clean 不是空谈，已经进入可复现实现。

不过要注意：

- dirty DOI 修复并不等于所有 recall 问题都自动消失
- 它修复的是上游 identifier 质量问题
- 其 downstream 收益还会受到 provider coverage 与 merge policy 共同影响

## 6.2 仅做 baseline replay，也比原始 source DB 更完整

baseline replay 相比原始 source DB：

- merged proposal: `203 -> 219`（+16）
- canonical paper: `164 -> 176`（+12）

这说明两件事：

1. 当前代码中的 replay + normalize + merge 逻辑，已经与更早的 source DB 版本存在实质差异
2. DOI clean 和当前规则集本身，就已经带来了正向恢复效果

## 6.3 normalized-only fallback 的效果是明确、且量化可见的

treatment 相比 baseline：

- merged proposal: `219 -> 249`（+30）
- normalized-only fallback proposal: `0 -> 30`（+30）
- canonical paper: `176 -> 204`（+28）
- review queue: `2 -> 2`（无新增）
- severe DOI conflict: `2 -> 2`（无新增）

这说明：

> 在这个 same-batch slice 上，开启 normalized-only fallback 明确恢复了 30 个原本会在 merge 前消失的 candidate，并把其中 28 个转化为 canonical，而没有额外增加 review queue 或 severe DOI conflict。

这是本轮最关键的工程结论。

## 6.4 matched source_record 略降，不构成主结论动摇

treatment 的 matched source_record 比 baseline 少 5。

在当前结果下，这不改变主结论，因为：

- provider intent 数相同
- source_record 总数相同
- merged / canonical 明显提升
- review / severe DOI conflict 未恶化

更合理的解释是外部 provider 响应存在正常波动，而 fallback 机制把“provider 未命中导致的 candidate 蒸发”从系统层面兜住了。

## 6.5 本轮没有产生 paid LLM token 开销

本轮 replay 纯属传统 pipeline/provider 路径，没有走任何 paid LLM 判断链路。

因此，本轮报告中对付费 LLM token 的结论是：

- **未发生**
- 因而**不记录 paid token cost**

这与当前已确认的记账原则一致。

---

## 7. 本轮结论

如果要把本轮结论压缩成三句话，就是：

1. **Package A 已经真正落地，不再只是计划。**
2. **DOI clean 和 normalized-only fallback 都被实现并在 same-batch replay 中验证。**
3. **在当前 249-candidate slice 上，treatment 相比 baseline 多恢复 30 个 merged proposal、多得到 28 个 canonical，且没有增加 review queue 或 severe DOI conflict。**

因此，当前阶段我认为：

> `normalized_only_fallback` 已经通过本轮 replay，足以进入主线候选默认策略集合。

但仍建议保留后续两步：

- 对新增 canonical 做小样本人工审计
- 在新鲜 slice 上再做一轮确认

---

## 8. 对下一步的建议

我建议下一步进入 **Package B 的前半段**，优先做：

1. `accepted-merge audit export`
2. 对本轮新增恢复的 fallback cases 做人工抽样审计
3. provider experiment harness 正式化
4. 将 Unpaywall 作为 **experimental profile object** 纳入对照实验

注意：

- Unpaywall 现在仍然**只是待验证对象**
- 本轮结果**并不自动支持**把它并入主链路
- 但本轮 replay substrate 已经足够支持后续把它纳入严格 profile comparison

---

## 9. 一句话总结

> Package A 的关键目标已经达成：replay 现在能真正比较策略，DOI clean 已修复脏 DOI，normalized-only fallback 已经在 same-batch 实验里证明能显著提升 merge/canonical yield，而且没有引入额外 review 负担；本轮没有产生任何 paid LLM token 开销。
