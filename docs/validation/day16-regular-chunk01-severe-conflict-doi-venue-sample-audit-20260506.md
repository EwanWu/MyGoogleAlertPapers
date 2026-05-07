# regular chunk01 review-queue 抽查：`severe_conflict:doi,venue`（2026-05-06）

## 目标
判断 regular chunk01 中大量 `severe_conflict:doi,venue` 是否代表真实高风险合并冲突，还是系统性伪冲突。

## 样本与范围
- review queue 总量：`725`
- 其中 `severe_conflict:doi,venue`：`706`
- 抽查方式：
  - 先看前 12 个样本
  - 再做全量模式计数

## 观察到的稳定模式
### 1. 这 706 条全部来自 PubMed URL 候选
- `url_canonical` 域名：`pubmed.ncbi.nlm.nih.gov` 占 `706/706`
- `doi_extracted`：`706/706` 都是 `NULL`
- `pmid_extracted`：样本中均存在，且走了 `pubmed pmid` / `europepmc pmid` 生物医学链路

### 2. 主冲突不是标题，也不是“两个近似不同论文”
样本的标题在各 provider 间高度一致；冲突集中在：
- `pubmed(query_type=pmid)` 给出一个 DOI
- `europepmc(query_type=pmid)` 给出另一个 DOI
- 少量样本还会有 `openalex/crossref(title)`，且它们支持 EuropePMC 那个 DOI

### 3. 706/706 都符合同一个伪冲突形态
全量计数结果：
- `has_pubmed_pmid = 706`
- `has_europepmc_pmid = 706`
- `pubmed_doi_disagrees_with_3way_consensus = 706`
- 其中纯 `pubmed+europepmc` 双源形态就有 `692`

也就是：
- PubMed PMID 记录中的 DOI 与其他来源稳定冲突
- EuropePMC / OpenAlex / Crossref 更像是共识侧

## 代表性样本
### sample A
- title: `Neural responses to error in youth: the impact of social context, anxiety, and worry`
- PubMed DOI: `10.1089/cap.2017.0142`
- EuropePMC / Crossref / OpenAlex DOI: `10.1007/s00787-025-02957-6`
- venue 一致指向 `European Child & Adolescent Psychiatry`

### sample B
- title: `Quantitative susceptibility mapping in pediatric neuroimaging: a systematic review of applications and advancements`
- PubMed DOI: `10.1111/acer.14928`
- EuropePMC / Crossref / OpenAlex DOI: `10.1007/s00247-026-06565-7`
- venue 一致指向 `Pediatric Radiology`

### sample C
- title: `α-synuclein positivity is associated with decline in brain microstructure in the Alzheimer's disease spectrum`
- PubMed DOI: `10.1186/s13195-014-0087-9`
- EuropePMC / Crossref / OpenAlex DOI: `10.1186/s13195-026-01995-9`
- venue 一致指向 `Alzheimer's Research & Therapy`

## 关键反事实检查
对这 706 条做了一个最小反事实：
- 仅把 `source_name='pubmed' AND query_type='pmid'` 的 DOI 置空
- 重新跑同一套 merge 冲突评估

结果：
- 原始 blocked：`706`
- 仅去掉 PubMed PMID DOI 后仍 blocked：`0`

## 结论
### Known
- 这 `706` 条几乎可以确定不是“真实需要人工审稿的 doi+venue 双重冲突主带”。
- 它们是一个高度一致的系统性伪冲突：**PubMed PMID DOI 污染 / 错 DOI 信号**。

### Inferred
- 现有 `merge._apply_pubmed_doi_suppression(...)` 只抑制 `pubmed + title query` 的 DOI 冲突；
- 但这批问题来自 `pubmed + pmid query`，所以没有被拦住。

### Speculative
- 这些 DOI 很可能来自 PubMed 记录中的历史/关联/错误 DOI 字段，不适合作为当前 canonical merge 的强冲突证据。

## 建议
### 最小修复优先级：高
把 PubMed DOI suppression 从：
- `source_name='pubmed' and query_type='title'`
扩到至少覆盖：
- `source_name='pubmed' and query_type='pmid'`
当其 DOI 与 EuropePMC / Crossref / OpenAlex 共识 DOI 冲突时，抑制 PubMed DOI，仅保留 PubMed 的：
- PMID
- PMCID
- title / abstract / venue / year

### 已实现的窄修复（2026-05-06 15:xx）
实际 patch 采用了两层窄条件：
1. 现有路径保留：`pubmed + title` DOI 与非 PubMed 共识 DOI 冲突时 suppress；
2. 新增路径：`pubmed + pmid` DOI 冲突时，允许 **EuropePMC PMID 单独作为这类 NCBI/PMID chain 的 DOI 共识源**，条件包括：
   - PubMed / EuropePMC 共享同一个 PMID；
   - DOI 不一致；
   - 标题近似变体（或 venue rough match）；
   - 候选仍处于 NCBI PMID/PMCID 链路语境。

### 补丁后最小验证
- 单测：`PYTHONPATH=src pytest -q tests/test_merge_conflict_grading.py` → `13 passed`
- DB 级 bucket 模拟：
  - `bucket_total = 706`
  - `collapsed_after_patch = 706`
  - `still_blocked_after_patch = 0`
  - `estimated_review_total_after_patch = 19`

### 实际刷新结果（已执行）
针对 regular chunk01 当前正式库，已先对 `706` 条 `severe_conflict:doi,venue` 候选做定向 merge refresh，并在正式库上重新跑 dedup：
- refreshed severe-conflict bucket: `706`
- dedup scaffold picked up after refresh: `703`
- `candidate_paper_links`: `8651 -> 9354`（`+703`）
- `canonical_papers`: `3879 -> 3894`（`+15`）
- `review_blocked_total`: `725 -> 19`
- `severe_conflict:doi,venue`: `706 -> 0`

随后又对剩余 `8` 条 `severe_conflict:doi` 做了同类定向 refresh，并在正式库上重跑 dedup：
- refreshed severe-conflict:doi bucket: `8`
- dedup scaffold picked up after refresh: `8`
- `candidate_paper_links`: `9354 -> 9362`（`+8`）
- `canonical_papers`: `3894 -> 3902`（`+8`）
- `review_blocked_total`: `19 -> 11`
- `severe_conflict:doi`: `8 -> 0`

- 当前 review 残留构成为：
  - `fallback_guardrail:targeted_post_openalex_url_only_non_arxiv_low_source_title_similarity = 7`
  - `severe_conflict:doi,title,venue = 4`

### 预期收益
模拟结果和实际刷新结果一致：regular chunk01 中此前虚高的 `severe_conflict:doi,venue` 主桶已被**整体塌缩**，当前 review backlog 已更接近真实需要人工介入的残留。
