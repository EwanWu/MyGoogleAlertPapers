# Package B 前半段：normalized-only fallback 审计摘要

- baseline DB: `data/mgap_pkg3_guardrail_100_replay_baseline_guardrail_20260415.db`
- treatment DB: `data/mgap_pkg3_guardrail_100_replay_conditional_sources_v3_fallback_guardrail_full_20260416.db`
- fallback proposals: **36**
- unique new canonicals: **25**
- duplicate paper groups among fallback rows: **5**

## Duplicate groups
- `paper_2ec899546f5d4153` (2 rows): Risk prediction in patients with heart failure with preserved ejection fraction: the LIFE-Preserved model
  - `cand_0149b7304f1c8c06`
  - `cand_a51e8701d064dfc7`
- `None` (8 rows): LB-525395-03 SAFETY AND EFFICACY OF A NOVEL ICD LEAD FOR LEFT BUNDLE BRANCH AREA PACING: RESULTS FROM THE ASCEND CSP TRIAL
  - `cand_7237121835e51fe0`
  - `cand_3c0daf67a3c4f756`
  - `cand_505b2326b7b8f0e5`
  - `cand_e4783c70fe9603a2`
  - `cand_cc340e92866d3360`
  - `cand_8c0fcffbabdce4e6`
  - `cand_054270b0fef2b17a`
  - `cand_1d53b41d67c6e37e`
- `paper_5add76e208b04c70` (2 rows): Finerenone and quality of life in heart failure: component-level analyses and clinical relevance of the Kansas city cardiomyopathy questionnaire
  - `cand_4d5588be2fa7ee5f`
  - `cand_b49a741281a5aa8b`
- `paper_f7a7c2da7be24de8` (2 rows): CT Angiography–Derived Plaque and Perivascular Fat Radiomics for Predicting Ipsilateral Stroke Recurrence in Patients with Carotid Atherosclerosis
  - `cand_7696ad0277fbf5f0`
  - `cand_a9479ded72395f30`
- `paper_87a894df84fd466a` (2 rows): Visceral adiposity assessment to enhance risk stratification in heart failure with preserved ejection fraction
  - `cand_c2cf756168f1d04f`
  - `cand_fd420a25ab62ada2`

## Recommended first-pass audit set (top 10 by suspicion heuristic)

| candidate_id | suspicion | max_title_sim | doi | year | venue | providers | title |
|---|---:|---:|---|---|---|---|---|
| cand_7237121835e51fe0 | 5 | 0.379 |  |  | Heart Rhythm | crossref, openalex, semanticscholar | LB-525395-03 SAFETY AND EFFICACY OF A NOVEL ICD LEAD FOR LEFT BUNDLE BRANCH AREA PACING: R |
| cand_3c0daf67a3c4f756 | 5 | 0.415 |  | 2026 |  | crossref, europepmc, openalex, pubmed, s | Domain-Guided Machine Learning for High-Dimensional Multi-Modal Neuroimaging and Biomarker |
| cand_505b2326b7b8f0e5 | 5 | 0.450 |  |  |  | crossref, europepmc, openalex, pubmed, s | Measuring blood flow and pulsatility with MRI: optimisation, validation and application in |
| cand_e4783c70fe9603a2 | 4 | 0.246 |  | 2026 | 上海交通大学学报(医学版) | crossref, openalex, semanticscholar | 基于血管内超声分析载脂蛋白B 控制水平对冠状动脉斑块进展影响的队列研究 |
| cand_cc340e92866d3360 | 4 | 0.381 |  | 2026 | 实用医学杂志 | crossref, openalex, semanticscholar | 食管鳞癌免疫微环境异质性及免疫治疗联合策略 |
| cand_8c0fcffbabdce4e6 | 4 | 0.408 |  | 2026 | Ultrasonography | crossref, europepmc, openalex, pubmed, s | Perivascular space (PVS) volume on cranial ultrasonography in neonates: a feasible glympha |
| cand_054270b0fef2b17a | 4 | 0.443 |  | 2026 | Сибирский научный … | crossref, openalex, semanticscholar | Современные возможности бесконтрастной МР-перфузии: от научных исследований до клинической |
| cand_1d53b41d67c6e37e | 4 | 0.817 |  |  |  | crossref, europepmc, openalex, pubmed, s | PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel |
| cand_58d8bc3944e29fbf | 3 | 0.000 | 10.3389/fcvm.2026.1774091 |  | Frontiers in Cardiovascular  | crossref, openalex, semanticscholar | Multi-chamber three-dimensional myocardial strain assessment by computed tomography: compa |
| cand_7696ad0277fbf5f0 | 3 | 0.000 | 10.3389/fneur.2026.1821860 |  | Frontiers in Neurology | crossref, openalex, semanticscholar | CT Angiography–Derived Plaque and Perivascular Fat Radiomics for Predicting Ipsilateral St |

## LLM 审核建议字段
建议将 CSV 中以下列喂给 LLM 做逐条判断：
- norm_title, authors_short, venue_guess, year_guess
- doi_extracted / pmid_extracted / pmcid_extracted / arxiv_id_extracted
- source_title_summary
- max_source_title_similarity, suspicion_score
- duplicate_group_size

CSV: `docs/validation/packageB-v3-fallback-audit-full-2026-04-16.csv`
JSON summary: `docs/validation/packageB-v3-fallback-audit-full-2026-04-16.json`
