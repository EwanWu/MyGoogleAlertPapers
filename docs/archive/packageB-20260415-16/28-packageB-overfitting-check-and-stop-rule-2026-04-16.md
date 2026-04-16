# Package B overfitting check and stop rule（2026-04-16）

## 1. 这份备忘录的目的
Ewan 明确要求：

> 不要过拟合，优先追求整体性能，少 1 到 2 篇并不重要。

因此这里专门检查：在 `v4 fallback guardrail salvage` 之后，是否还值得继续增加新的 salvage 规则。

## 2. 当前基线
当前最好候选是：
- `conditional_sources_v4_fallback_guardrail_salvage`

在固定 249-candidate slice 上结果为：
- `248 merged`
- `9 review`
- `196 canonical`

相对 v3：
- review `10 -> 9`
- canonical `195 -> 196`

且只恢复了 1 条高置信 case，没有额外放宽其它高风险 review。

## 3. 对剩余 fallback review 的结构分析
这里看的是 **v4 后仍留在 normalized-only fallback review 路径中的 case**。

### 3.1 数量
- 剩余 fallback review: **7**

### 3.2 guardrail 原因分布
- `low_source_title_similarity`: **6**
- `sparse_metadata_low_source_title_similarity`: **1**

### 3.3 结构特征
- `7/7` 都没有 candidate 自带 identifier（`doi_extracted / pmid_extracted / pmcid_extracted` 均空）
- `7/7` 都落在 `paper_id = None` 的未稳定 linking 区
- `7/7` 都属于“provider 没有给出足够强支撑”的 case
- 只有 `1/7` 带明显 ellipsis / truncation 痕迹（`cand_8c0fcffbabdce4e6`）

## 4. 关于继续做 truncation / ellipsis salvage 的证据
我对剩余 review 做了简单检查：
- 对唯一明显 truncation case `cand_8c0fcffbabdce4e6`
- 做截断尾巴后的 title similarity 重算

结果：
- raw similarity: `0.408`
- truncation-cleaned similarity: `0.414`

提升几乎为零，**不足以构成有效 salvage 证据**。

这意味着：
- “ellipsis / truncation cleanup” 在当前 slice 上 **没有显示出像 author-tail cleanup 那样清晰的收益信号**
- 如果继续为这类 case 写规则，当前更像是为个别坏例硬凑规则，而不是提炼通用模式

## 5. 当前最合理的工程判断
### established
- `v4` 已经把最明显、最可泛化的一类 parser 污染（author tail pollution）安全救回
- 剩余 fallback review 基本都属于“证据弱 / provider mismatch / 无 identifier”的 case
- 现阶段没有看到第二类同样清晰、同样高 precision 的 salvage 模式

### inference
- 继续加 salvage 规则的**边际收益已经明显下降**
- 继续加规则的**过拟合风险正在上升**
- 现在最优策略不是继续扩 heuristics，而是先把 `v4` 作为当前候选冻结下来，转去做更大样本或 live validation

## 6. Stop rule（建议后续照此执行）
在进入下一条 salvage 规则之前，至少满足以下条件之一：

### Rule A: 样本规模门槛
同一模式在当前 review 池里至少出现 **>= 2-3 条**，而不是只剩 1 条边缘个案。

### Rule B: 证据强度门槛
清理后 title 与 provider title 的相似度要有**明显提升**，且达到高阈值（例如 `>= 0.8`）。

### Rule C: 外部支撑门槛
最佳匹配 source row 必须自带强标识支撑（DOI / PMID / PMCID）。

### Rule D: 系统层收益门槛
新规则至少要在 replay 中带来下面之一，才值得保留：
- canonical `+2` 及以上，且 review / risk 不明显恶化
- 或在更大样本上稳定改善 precision/recall 结构

若达不到这些门槛，就**不要继续加规则**。

## 7. 结论
当前我建议：

> **先停在 v4。不要继续围绕剩余 7 条 review 写更多 salvage 规则。**

更合理的下一步是：
1. 把 `v4` 视为当前最佳候选
2. 在更大 slice 或 live batch 上验证整体表现
3. 只有当新模式在更大样本中重复出现时，再考虑补下一条规则

这更符合“整体性能优先，少 1 到 2 篇不重要”的目标。 
