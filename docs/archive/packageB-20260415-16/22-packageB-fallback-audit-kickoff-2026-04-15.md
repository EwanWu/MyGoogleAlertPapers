# Package B 前半段启动：normalized-only fallback 小样本审计（2026-04-15）

## 1. 本轮已完成内容

已从 Package A 的 baseline / treatment replay DB 中抽取 treatment 新增的 `normalized-only fallback` 案例，并生成可供人工/LLM 审核的审计表。

### 数据源
- baseline: `data/mgap_pkg3_guardrail_100_replay_baseline_guardrail_20260415.db`
- treatment: `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v2_20260415.db`

### 导出产物
- `data/exports/packageB-fallback-audit-2026-04-15.csv`
- `data/exports/packageB-fallback-audit-2026-04-15.json`
- `data/exports/packageB-fallback-audit-2026-04-15.md`
- `data/exports/packageB-fallback-audit-top10-llm-prompt-2026-04-15.md`

## 2. 当前审计对象统计

- fallback proposals: **30**
- unique new canonicals: **28**
- duplicate paper groups among fallback rows: **2**

说明：30 条 fallback proposal 中，有 2 组候选各自并到了同一个新 canonical，因此最终 canonical 净新增为 28，而不是 30。

### duplicate groups
1. `paper_8fc55e8601ef4d00`
   - `cand_7696ad0277fbf5f0`
   - `cand_a9479ded72395f30`
   - 标题：`CT Angiography-Derived Plaque and Perivascular Fat Radiomics for Predicting Ipsilateral Stroke Recurrence in Patients with Carotid Atherosclerosis`

2. `paper_a5d6c320a95c450e`
   - `cand_c2cf756168f1d04f`
   - `cand_fd420a25ab62ada2`
   - 标题：`Visceral adiposity assessment to enhance risk stratification in heart failure with preserved ejection fraction`

## 3. 当前启发式怀疑分布

按启发式 `suspicion_score` 分布：
- score 6: 1 条
- score 5: 3 条
- score 4: 5 条
- score 3: 7 条
- score 2: 14 条

这说明 30 条 fallback 中，至少前 9 条应优先做人工/LLM 审核，因为其 candidate 自身字段和 provider 返回结果之间存在明显不一致，或 candidate 本身就像解析残片。

## 4. 当前已能直接观察到的风险信号

### 明显可疑 case A：疑似“作者串误当标题”
- `cand_400e144162689110`
- `norm_title`: `Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3`
- 当前看起来更像作者名单残片，而不像真实论文标题。
- 这是一个很强的 reject / parser bug 信号。

### 明显可疑 case B：标题后拼接作者串
- `cand_1d53b41d67c6e37e`
- `norm_title`: `PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease Hugh S Markus, FMed Sci, Marco Egle MSc`
- 标题后面混入作者信息，说明 parse / normalize 端可能仍有模板污染。
- 更像应进入 review，而不是直接 canonicalize。

### 其他可疑模式
- candidate 本身像真实标题，但 provider 返回标题全部明显跑偏
- DOI/PMID 缺失，且 provider title similarity 很低（<0.45）
- venue/year 缺失较多

## 5. 建议下一步

### Step 1（立即执行）
先用 `packageB-fallback-audit-top10-llm-prompt-2026-04-15.md` 对 top-10 suspicious cases 做 LLM 辅助初审。

目标不是让 LLM 直接替代人工，而是快速给出三类标签：
- `accept`
- `review`
- `reject`

### Step 2
对 top-10 的判断结果做人工 spot-check，确认：
- LLM 是否能稳定识别明显 parser 残片
- 哪些 case 属于“真实论文但 provider 全跑偏”
- 哪些 case 属于“根本不应 fallback 进入 canonical”

### Step 3
根据结果决定是否需要新增 guardrail，例如：
- candidate 标题形态异常拦截
- 作者串污染检测
- fallback 前的最低标题合法性检查
- provider 全跑偏时转 review 而非直接 new canonical
