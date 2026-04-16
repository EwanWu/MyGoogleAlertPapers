# Package B 前半段：fallback 全 30 条审计总结（2026-04-15）

## 1. 本轮结论

对 Package A treatment 中新增的 30 条 `normalized-only fallback` case 做首轮 LLM 辅助审计后，结论为：

- **accept**: 18
- **review**: 10
- **reject**: 2

这说明：

> `normalized-only fallback` 不是整体错误，**大约 60%（18/30）看起来是可接受的新 canonical**，但仍有约 **40% 需要额外 guardrail（review + reject）**。

---

## 2. 结构化理解

### 2.1 明确收益
当前 fallback 确实恢复了一批合理的论文条目，尤其是：
- candidate 自带 DOI
- 标题、作者、venue 结构完整
- provider 虽未提供 title，但 DOI 足以支持存在性
- 或 provider title 与 candidate 高相似

这部分说明 fallback 的总体方向是对的，不应整体回滚。

### 2.2 明确风险
风险主要集中在三类：

1. **parser / normalize 污染**
   - 作者串误入标题
   - 标题后拼作者
   - 截断标题/模板残片

2. **provider 全跑偏但仍 direct fallback**
   - candidate 可能真实，但证据不足，不应直接 canonicalize
   - 更适合进入 review

3. **本地语言/本地来源论文**
   - 中文、俄文 case 本身可能是真的
   - 但当前 provider 覆盖弱，不能直接 accept，也不应直接 reject
   - 适合人工 review 路径

---

## 3. 我建议的规则变化

### Rule A：fallback direct accept 条件
允许 direct fallback 的 case 应至少满足以下之一：
- candidate 自带 DOI / PMID / PMCID
- 或有 provider title 与 candidate 高相似（建议阈值 > 0.75）

### Rule B：fallback -> review 条件
以下情况不应 direct new canonical，而应转 review：
- 无 DOI / PMID / PMCID
- `max_source_title_similarity < 0.45`
- provider 返回结果整体跑偏
- 中文/俄文标题本身合理，但无外部强证据

### Rule C：fallback reject 条件
以下情况应直接拦截：
- 标题明显是作者串/脚注串
- 标题严重截断且不像完整题目
- 标题后半混入作者/学位信息，且无外部强证据

---

## 4. 最值得优先加的 guardrail

### Guardrail 1：标题合法性检查
在 normalized-only fallback 前增加：
- 作者串检测
- 脚注编号模式检测
- 标题截断/非句式标题检测

### Guardrail 2：provider mismatch 降级
若：
- 无 DOI/PMID/PMCID
- 且 `max_source_title_similarity < 0.45`

则：
- **不 direct canonicalize**
- **进入 review queue**

### Guardrail 3：标题污染检测
若标题尾部明显混入：
- 作者姓名序列
- 学位后缀
- 会议模板残片

则优先转 review。

---

## 5. 当前最合理的下一步

我认为现在不该直接扩大 fallback，而应进入：

### Package B 后续建议
1. 把这 30 条 verdict 回写成一份正式 audit artifact
2. 先实现最小 guardrail（标题合法性 + provider mismatch 降级）
3. 在同一 249-candidate slice 上重跑一次 treatment replay
4. 观察：
   - canonical 是否略降但质量更稳
   - review 是否适度上升但可接受
   - reject 是否只拦住明显坏例

目标不是“保住 30/30 新增”，而是：

> **保住大部分真实增益，同时把明显 parser 污染和证据不足 case 从 direct canonical 路径里拿出去。**
