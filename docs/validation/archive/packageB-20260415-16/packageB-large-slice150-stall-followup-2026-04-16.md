# Package B larger-slice150 stall follow-up（2026-04-16）

## 结论
本轮 `larger-slice150` 后半程验证仍**未完成**。OpenAlex 空值链 bug 修复后，`v2 smoke enrich` 不再立刻抛 `AttributeError`，但出现了新的失败形态：**enrich 挂起（stall）**。因此本轮没有进入正式的 `v2 merge+dedup` 和 `v4 enrich+merge+dedup` 对照。

## 本轮实际完成
- 确认 `src/mygooglealertpapers/enrich/openalex.py` 中 `_extract_primary_location_fields()` 已改为二级空值防护，原先 `primary_location.source = null` 的崩溃路径已消失。
- 跟踪正在运行的 smoke：
  - 命令：`python3 scripts/replay_validation.py --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db --output-db data/mgap_pkgB_large_slice150_replay_v2_smoke_20260416.db --policy-profile config/policy_profiles/conditional_sources_v2.yaml --report-out docs/validation/packageB-large-slice150-v2-smoke-20260416.json --stages enrich`
  - 采用长间隔检查，避免高频轮询。
- 最终判定该 smoke 没有完成，而是卡在 `enrich-candidates` 子进程，随后停止该 run，保留现场信息。

## 现场证据（Known）
### 进程状态
- 父进程：`replay_validation.py`
- 子进程：`python3 -m mygooglealertpapers.cli enrich-candidates --limit 1000000`
- 观察窗口内子进程长期处于 sleep，CPU 时间仅约 `4s`，明显不像正常持续计算。
- `/proc/8552/wchan = do_sys_poll`，说明子进程阻塞在 poll 等待。
- `ss -tpn` 显示子进程有一个持续存在的已建立 socket：
  - `172.18.253.105:56902 -> 172.18.240.1:62049`

### DB 状态
停止 run 后，`data/mgap_pkgB_large_slice150_replay_v2_smoke_20260416.db` 中仍是未写出 enrich 结果的状态：
- `paper_candidate`: `368`
- `paper_candidate_normalized`: `368`
- `candidate_enrichment_status`: `0`
- `source_record`: `0`
- `cost_event`: `0`
- `batch_run`: `1`

唯一 batch_run 记录：
- `stage = enrich_candidates`
- `status = running`
- `finished_at = null`
- `duration_ms = null`

### 缺失产物
以下 smoke 产物都**未生成**：
- `docs/validation/packageB-large-slice150-v2-smoke-2026-04-16.json`
- `docs/validation/packageB-large-slice150-v2-smoke-2026-04-16.md`

## 新的失败原因判断
### Known
- 这次不是之前的 OpenAlex payload 空值链崩溃。
- `enrich-candidates` 子进程在网络/IO 等待态长时间不返回。
- 按代码，OpenAlex/Crossref/PubMed/EuropePMC/arXiv/Semantic Scholar 均使用 `urllib.request.urlopen(..., timeout=20~30)`，但现场表现与“单次请求超时后及时返回”不一致。

### Inferred
- 更可能的根因是 **provider 请求链路上的 stall / timeout 未被上层 orchestration 正确收敛**，而不是纯 Python 计算或 SQLite 写锁问题。
- 由于 `enrich_candidates()` 在函数末尾才 `conn.commit()`，因此只要某个 provider 调用挂住，就会出现：
  - DB 里几乎看不到中间 enrich 结果
  - `batch_run` 永远停在 `running`
  - `replay_validation.py` 也不会写出 failure report

## larger slice 上目前能说什么
### provider latency / hit-rate
**仍不能下结论**。

原因：smoke 都没有完成，无法形成完整 provider 统计，更无法继续正式 v2/v4 对照。

### v4 相对 v2 的整体收益
**仍不能下结论**。

原因：v2 正式 replay 未启动，v4 完全未启动。

## 这轮暴露出的 orchestration 规律
1. **上下文压缩风险是真实的**
   - 如果不把现场外化到文档，很容易只记得“修过一个 bug”，却丢掉“修复后进入了另一种 stall failure mode”。
2. **过频繁轮询没有帮助**
   - 这类 stall 不是看进度条能解决的。长间隔检查足够，关键是保留 `/proc`、socket、DB、产物缺失这些 failure artifact。
3. **failure artifact 很重要**
   - 当前 `replay_validation.py` 只有在子命令正常返回或抛异常后，才会落 JSON/Markdown；一旦子命令挂死，就没有自动失败摘要。
   - 这会显著抬高恢复成本。

## 建议的下一步
### 必做
1. 为 provider 请求增加更强的超时/重试上界，确认不会出现无限挂起。
2. 在 `enrich_candidates()` 中增加更细粒度提交或至少阶段性 checkpoint，避免长时间完全不可见。
3. 在 `replay_validation.py` 中增加 watchdog / timeout 包装，并在超时退出时仍写 failure artifact。
4. 完成上述修复后，再重新跑：
   - `v2 smoke enrich`
   - 若通过，再做 `v2 merge+dedup`
   - 再做 `v4 enrich+merge+dedup`

### 最小工程建议
- 给 `run_mgap()` 增加可配置 wall-clock timeout。
- 给 `batch_run` 增加异常/中止回填，避免永久残留 `status=running`。

## Known / Inferred / Speculative
### Known
- OpenAlex 空值链 bug 已修。
- 新 smoke 未崩溃，但在 `enrich-candidates` 长时间挂起。
- 停止后 DB 中无 enrich 输出，只有一条 `running` 的 batch_run。
- 计划中的 smoke JSON/Markdown 未生成。

### Inferred
- 主要问题已从 payload parsing bug 转为 provider-call/orchestration stall。
- 单个挂起调用会让整轮 replay 既不提交中间结果，也不产出 failure summary。

### Speculative
- 修复 timeout/watchdog 与 checkpoint 机制后，larger-slice150 才有机会稳定进入真正的 v2 vs v4 收益比较阶段。
