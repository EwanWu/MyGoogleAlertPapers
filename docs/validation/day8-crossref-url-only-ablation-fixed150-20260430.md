# Day8 fixed-slice150 单因素对照：skip crossref `url_canonical_only`
## Objective
- Control: `openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml`
- Treatment: `openalex_batching_identifier_plus_title_core_same_batch_cluster_skip_crossref_url_only.yaml`
- Method: 先跑 control 并录制 HTTP fixture，再用同一份 fixture 回放 treatment，隔离 live-network 噪声。

## Core result
**结论：该 treatment 在 fixed slice150 上出现明显语义回归，不能推广，且现阶段不值得进入 fresh-like promotion gate。**

## Known observations
- Experimental skip 命中 `crossref:url_canonical_only` **126 groups / 127 intents**。
- Dispatch groups: **611 → 485**（-126）
- Runnable provider intents: **755 → 628**（-127）
- Crossref events: **368 → 241**（-127）
- Crossref provider latency: **610,951 ms → 268,082 ms**（-342,869 ms, **-56.1%**）
- Total provider latency: **928,175 ms → 578,656 ms**（-349,519 ms, **-37.7%**）
- Matched source records: **608 → 503**（-105）
- Canonical papers: **292 → 293**（+1）
- Merge review queue: **1 → 0**（-1）
- Severe DOI conflicts: **1 → 0**（-1）
- Normalized-only fallback proposals: **38 → 68**（+30）

## Why this fails the semantic gate
- 有 **30 个 candidate** 在 control 中依赖 `crossref` title-lane 命中获得 DOI/高置信 metadata，但 treatment 跳过后退化为 `normalized_only` fallback。
- 这 30 个 case 的共同结构很一致：**control 中只有 crossref title 命中，openalex 没有匹配；treatment 跳过后直接丢 DOI，merge_confidence 从 0.9 降到 0.15。**
- 因此这不是“去掉冗余请求”，而是**真实 recall / metadata retention regression**。

## The one genuine improvement
- `cand_e7ece68ba869a802` — *Bridging Histology and Tractography: First In Vivo Visualization of Short‐Range Prefrontal Connections Informed by Primate Tract‐Tracing*
  - Control: `severe_conflict:doi`（crossref preprint DOI `10.1101/2025.10.22.683760` vs openalex journal DOI `10.1002/hbm.70520`）进入 review。
  - Treatment: 跳过 crossref 后保留 openalex journal article，成功 canonicalize。

## Regression examples (representative)
- `cand_3c2e407353cf4446` — *The Effect of Preoperative Epicardial Adipose Tissue Thickness on Postoperative Morbidity and Mortality in Patients Undergoing Isolated Coronary Artery Bypass …*
  - Control kept DOI: `10.3390/jcm15062207` (Journal of Clinical Medicine, 2026)
  - Matched source(s) in control: crossref:10.3390/jcm15062207
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_ef45f083c154b55c` — *Prevalence of heart failure with preserved ejection fraction in patients with ischemia and non-obstructive coronary arteries*
  - Control kept DOI: `10.1038/s41598-026-42032-x` (Scientific Reports, 2026)
  - Matched source(s) in control: crossref:10.1038/s41598-026-42032-x
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_e6e0961ddf95e426` — *Grayscale-inverted bright-blood late gadolinium enhancement improves reader confidence in ischemic scar Detection: A multivendor study*
  - Control kept DOI: `10.1016/j.ejrad.2026.112801` (European Journal of Radiology, 2026)
  - Matched source(s) in control: crossref:10.1016/j.ejrad.2026.112801
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_4940296152b16081` — *Periprocedural Stroke: Stroke Mechanisms, Risks, Outcomes, Prevention, and Treatment*
  - Control kept DOI: `10.3390/anesthres3010007` (Anesthesia Research, 2026)
  - Matched source(s) in control: crossref:10.3390/anesthres3010007
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_1c8d63b26d68bca3` — *Brain fluid dynamic characteristics in cerebral small vessel disease*
  - Control kept DOI: `10.4103/nrr.nrr-d-25-01310` (Neural Regeneration Research, 2026)
  - Matched source(s) in control: crossref:10.4103/nrr.nrr-d-25-01310
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_3b632c81aa6b162c` — *Non-invasive Evaluation of Myocardial Fibrosis Using T1 and T2 Mapping by Cardiac Magnetic Resonance Imaging*
  - Control kept DOI: `10.7759/cureus.105441` (Cureus, 2026)
  - Matched source(s) in control: crossref:10.7759/cureus.105441
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_29030ef4d0434fb2` — *Long-Term Outcomes and Safety of His-Purkinje Conduction System Pacing in China: The ChiCSP Study*
  - Control kept DOI: `10.1016/j.jacep.2026.01.037` (JACC: Clinical Electrophysiology, 2026)
  - Matched source(s) in control: crossref:10.1016/j.jacep.2026.01.037
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_bb4119638deea878` — *MRI and Endometrial Cancer After FIGO 2023—What's New? A Narrative Review*
  - Control kept DOI: `10.3390/cancers18061005` (Cancers, 2026)
  - Matched source(s) in control: crossref:10.3390/cancers18061005
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_78d7e8d2b587f125` — *Cardiac magnetic resonance assessment of left ventricular phenotypes and prognostic implications in hypertensive heart disease*
  - Control kept DOI: `10.5646/ch.2026.32.e14` (Clinical Hypertension, 2026)
  - Matched source(s) in control: crossref:10.5646/ch.2026.32.e14
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_29a12d68fc97f174` — *Role of intraoperative intravascular ultrasound in the prevention of periprocedural complications during internal carotid artery stenting. A case report*
  - Control kept DOI: `10.15829/1728-8800-2026-4671` (Cardiovascular Therapy and Prevention, 2026)
  - Matched source(s) in control: crossref:10.15829/1728-8800-2026-4671
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_fa48de520251f7ce` — *Automated Lung Disease Diagnosis Using Advanced Neural Networks*
  - Control kept DOI: `10.51220/jmr.v21-s2.35` (Journal of Mountain Research, 2026)
  - Matched source(s) in control: crossref:10.51220/jmr.v21-s2.35
  - Treatment: DOI lost, falls back to normalized-only proposal.
- `cand_60299604ebd701a3` — *Electrophysiological Predictors of Super-response to Left Bundle Branch Area Pacing in Non-ischemic Cardiomyopathy: The PRECISION LBBAP Study*
  - Control kept DOI: `10.1016/j.hrthm.2026.03.1908` (Heart Rhythm, 2026)
  - Matched source(s) in control: crossref:10.1016/j.hrthm.2026.03.1908
  - Treatment: DOI lost, falls back to normalized-only proposal.

## Mechanistic interpretation
- `url_canonical_only` 不是一个足够窄的“垃圾 proxy”。在这个 slice 上，它覆盖了两类混合群体：
  1. **坏 case**：crossref 命中 preprint / wrong version，确实会制造 DOI conflict；
  2. **好 case**：crossref 是该 candidate 唯一能补回 DOI 的 title-lane provider。
- 当前 provider+subreason 级 skip 规则把这两类一起砍掉，导致少量 precision gain 被大量 metadata/recall loss 淹没。

## Candidate-level decomposition of the 126 skipped groups

按 candidate-level 近似回看这 126 个 `crossref:url_canonical_only` 跳过组，可拆成 5 类：

1. **73 个：`crossref` + `openalex` 都命中，且 DOI 相同**
   - treatment 下 DOI 保持稳定
   - 这部分最像“真正冗余”的 `crossref` title 请求
2. **30 个：只有 `crossref` 命中**
   - treatment 全部 DOI 丢失
   - 这部分是 blanket skip 失败的主因
3. **19 个：`crossref` / `openalex` 都未形成有效 title 命中**
   - treatment 不改变语义，只是少打一发 `crossref`
4. **2 个：只有 `openalex` 命中**
   - treatment 语义稳定
5. **1 个：`crossref` 与 `openalex` 同时命中但 DOI 冲突**
   - 这是唯一明显 precision gain case（review → canonical）

因此，真正的结构不是“一个坏 subgroup”，而是：

- **30 个 crossref-only DOI rescue cases**
- **73 个 openalex 已足够的冗余 cases**
- **1 个 openalex-vs-crossref version conflict case**
- 加上一小部分双空跑 / openalex-only case

## Better next hypothesis

下一轮如果继续做 strict runtime hardening，更合理的假设不应是：

- “预先 blanket skip 全部 `crossref:url_canonical_only`”

而应是更窄的**后验条件抑制**（post-openalex suppression），例如：

- 对 `url_canonical_only` 子群，先跑 `openalex` title
- 如果 `openalex` 已给出 DOI-bearing matched article（或等价强标识结果），再抑制后续 `crossref` title
- 如果 `openalex` 未给出足够强的标识结果，则保留 `crossref`，以避免丢掉那 30 个 crossref-only DOI rescue cases

这个方向的好处是：

- 有机会优先吃到 **76 / 126 (60.3%)** 的更安全 suppressible 子群：
  - 73 个 `crossref + openalex same DOI`
  - 2 个 `openalex-only DOI-bearing`
  - 1 个 `crossref/openalex DOI conflict`
- 理论上还能避开那 **1 个 DOI conflict gain case** 里的 preprint 干扰
- 同时不再把 **30 个 crossref-only rescue cases** 一起砍掉

### Implementation implication

要实现这个更窄假设，当前 runtime 结构大概率需要两点同时成立：

1. 在相关 title-lane subgroup 内，`openalex` 必须先于 `crossref` 执行；
2. `crossref` 不能再是预先静态删掉，而应在 `openalex` 成功返回 DOI-bearing 强结果后做动态抑制。

也就是说，下一轮候选 patch 更像 **provider-order + post-result conditional suppression**，而不是单纯复用现有的 pre-dispatch `title_lane_skip_subreasons_by_provider` 机制。

## Decision
- **Reject for promotion.** 不进入默认策略。
- 由于 fixed-slice 已明确违反 promotion gate（30 个 DOI loss），**没有必要再为“promotion decision”补跑 fresh-like**。
- 如果还要继续 Phase 2A，只值得探索更窄的 rule，例如只拦截能被 version/venue/posted-content 机制单独识别的 preprint-conflict 子群，而不是 blanket skip 全部 `crossref:url_canonical_only`。
- 当前已补出代码级实验脚手架：`post-openalex conditional suppression`，但**尚未启动新的长跑 replay**。

## Reproducibility
- Control report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-crossref-url-only-control-150-20260430.json`
- Treatment report: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/docs/validation/day8-crossref-url-only-treatment-150-20260430.json`
- Control fixture: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/http_fixture_day8_crossref_url_only_control_150_20260430.jsonl`
- Control DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_crossref_url_only_control_150_20260430.db`
- Treatment DB: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/benchmark/day8_crossref_url_only_treatment_150_20260430.db`
- Next experimental profile scaffold: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml`
