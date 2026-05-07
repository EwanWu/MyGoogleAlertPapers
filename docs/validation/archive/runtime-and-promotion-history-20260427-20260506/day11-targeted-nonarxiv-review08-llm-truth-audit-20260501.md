# Day11 targeted non-arXiv review08: LLM truth audit

## Objective
Judge whether the `12` unique candidates (`16` slice-occurrences) newly routed from canonical to review by the subgroup-aware non-arXiv residual guardrail are mostly:

1. **desirable false-positive removals**; or
2. true matches that the new rule is incorrectly blocking.

This audit uses LLM reasoning as an **operator-side review aid**, not as a new default fact chain inside the pipeline.

## Inputs
- Audit pack: `docs/validation/day11-targeted-nonarxiv-review08-llm-audit-pack-20260501.json`
- Baseline/treatment audit CSVs:
  - `docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-audit-20260501.csv`
  - `docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-targeted-nonarxiv-review08-audit-20260501.csv`
  - `docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-audit-20260501.csv`
  - `docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-targeted-nonarxiv-review08-audit-20260501.csv`
- Treatment DBs:
  - `data/benchmark/day11_residual_decomposition_large_fixed_arxiv_gate_targeted_nonarxiv_review08_20260501.db`
  - `data/benchmark/day11_residual_decomposition_fresh30_arxiv_gate_targeted_nonarxiv_review08_20260501.db`
- External evidence used selectively:
  - Crossref API metadata for the candidate Crossref DOI
  - direct fetch / PDF text extraction for ambiguous source URLs when reachable

## Known
- The new guardrail touched `12` unique candidates / `16` slice-occurrences.
- All touched rows belong to `heuristic_bucket = source_title_noise_or_crossref_cleanup`.
- No `likely_openalex_recall_gap` rows were touched.
- No `mixed_or_unclear` rows were touched.
- All touched rows are normalized-only fallback cases with `title_lane_subreason = url_canonical_only`, no DOI/PMID/PMCID extracted, and no arXiv id.
- Crossref title similarity for all touched rows is low: roughly `0.29` to `0.70`.

## Case-by-case judgment

| candidate_id | slice count | judgment | confidence | rationale |
|---|---:|---|---|---|
| `cand_d64f1ad2ee228fa9` | 1 | desirable review block | high | URL/source title is a 2026 Russian IVUS peri-procedural-complication paper; Crossref candidate is a 2022 carotid-stenting case report. Same broad modality only, not same paper. |
| `cand_8c0fcffbabdce4e6` | 1 | desirable review block | medium-high | Candidate title is about neonatal PVS/glymphatic biomarker; Crossref is a different neonatal cranial-ultrasound paper; fetched URL resolves to an unrelated breast-ultrasound page, which is additional evidence that this path is noisy and not safe to canonicalize automatically. |
| `cand_3c0daf67a3c4f756` | 1 | desirable review block | high | Candidate is an eScholarship PDF with title `Domain-Guided Machine Learning... Alzheimer's Disease`; Crossref candidate is a 2024 posted-content item with a different title on structural neuroimaging visualization. Related field, different work. |
| `cand_f3f78ee6a4d53c12` | 1 | desirable review block | medium | Direct PDF extraction shows the source URL is a 2026 dissertation: `Studies on Continuous Pre- to Post-Reperfusion Intra-Carotid Artery Cold Infusion...`; Crossref candidate is a 2021 journal article `A System for Continuous Pre- to Post-reperfusion...`. Likely related precursor work, but not the same document. |
| `cand_505b2326b7b8f0e5` | 1 | desirable review block | high | Direct PDF extraction shows the source URL is a University of Edinburgh PhD thesis `Measuring blood flow and pulsatility with MRI... cerebral small vessel disease`; Crossref candidate is a 2021 Journal of Hypertension item on hemodialysis reducing cerebral pulsatility. Clearly not same paper. |
| `cand_054270b0fef2b17a` | 1 | desirable review block | high | Candidate is a 2026 Russian review on non-contrast MR perfusion; Crossref candidate is a 2015 oncology-practice article. Clear topic and year mismatch. |
| `cand_8994637b2b637b39` | 2 | desirable review block | high | Direct PDF extraction shows the source URL itself is a 2026 review article `Permanent weakness and myopathy in hypokalemic periodic paralysis` with DOI `10.36185/2532-1900-1999`; Crossref candidate is a 1967 article `Familial Hypokalemic Periodic Paralysis with Permanent Myopathy`. Same disease family, not same paper. |
| `cand_e4783c70fe9603a2` | 2 | desirable review block | high | Candidate is a Chinese IVUS/apolipoprotein-B coronary plaque progression cohort study; Crossref candidate is a 2024 review on blood-flow-restriction training and endothelial function. Clear mismatch. |
| `cand_03bde6287d0d1683` | 2 | desirable review block | high | Candidate is the English-title counterpart of the Shanghai Jiao Tong / IVUS apolipoprotein-B study; Crossref candidate is a 2012 Springer book chapter `Coronary Atherosclerotic Plaque Characterization By Intravascular Ultrasound`. Related technique only, not same paper. |
| `cand_cc340e92866d3360` | 2 | desirable review block | high | Candidate is about esophageal squamous-cell-carcinoma immune microenvironment / combined immunotherapy strategy; Crossref candidate is a TNBC immune-microenvironment review. Same broad cancer-immunology vocabulary only. |
| `cand_a9bfd54eb53be57b` | 1 | desirable review block | high | Direct PDF extraction shows the source URL is a 2025 Cornell PhD dissertation `Advanced Methods For Magnetic Resonance Image Reconstruction...`; Crossref candidate is a 2016 conference-series paper on accelerated parameter mapping / MRA. Same technical family, different document. |
| `cand_693adeec78169f65` | 1 | desirable review block | high | Candidate is about hybrid AF ablation and post-hybrid cardiac mechanics; Crossref candidate is the 2023 INDUCE-AF study on pulmonary-vein AF cycle length predicting ablation success. Same disease area only, not same paper. |

## External evidence excerpts for the most ambiguous cases

### `cand_f3f78ee6a4d53c12`
Direct PDF extraction from source URL:
> `Studies on Continuous Pre- to Post-Reperfusion Intra-Carotid Artery Cold Infusion for Neuroprotection in a Rodent Model of Acute Ischemic Stroke`  
> `Dissertation ... Eberhard-Karls-Universität Tübingen ... 2026`

Crossref DOI metadata:
- DOI: `10.1007/s12975-020-00848-3`
- type: `journal-article`
- year: `2021`
- title: `A System for Continuous Pre- to Post-reperfusion Intra-carotid Cold Infusion for Selective Brain Hypothermia in Rodent StrokeModels`

### `cand_505b2326b7b8f0e5`
Direct PDF extraction from source URL:
> `Measuring blood flow and pulsatility with MRI: optimisation, validation and application in cerebral small vessel disease`  
> `Doctor of Philosophy ... University of Edinburgh 2022`

Crossref DOI metadata:
- DOI: `10.1097/01.hjh.0000746456.48072.9d`
- type: `journal-article`
- year: `2021`
- title: `HEMODIALYSIS REDUCES CEREBRAL BLOOD FLOW PULSATILITY AND SMALL VESSEL STIFFNESS`

### `cand_8994637b2b637b39`
Direct PDF extraction from source URL:
> `Permanent weakness and myopathy in hypokalemic periodic paralysis`  
> `Acta Myol 2026;45:19-24`  
> DOI `10.36185/2532-1900-1999`

Crossref DOI metadata:
- DOI: `10.1097/00005072-196701000-00008`
- type: `journal-article`
- year: `1967`
- title: `Familial Hypokalemic Periodic Paralysis with Permanent Myopathy`

### `cand_a9bfd54eb53be57b`
Direct PDF extraction from source URL:
> `ADVANCED METHODS FOR MAGNETIC RESONANCE IMAGE RECONSTRUCTION, MOTION ARTIFACT CORRECTION AND QUANTITATIVE SUSCEPTIBILITY MAPPING`  
> `A Dissertation Presented ... Cornell University ... 2025`

Crossref DOI metadata:
- DOI: `10.1088/1742-6596/677/1/012002`
- type: `journal-article`
- year: `2016`
- title: `New Image Reconstruction Methods for Accelerated Quantitative Parameter Mapping and Magnetic Resonance Angiography`

## Aggregate judgment

### Known
- `12/12` unique candidates have clear low-similarity or document-type mismatch evidence.
- For several ambiguous-looking technical-domain matches, direct source-URL evidence shows the source is actually a **dissertation or a newer review/article**, while Crossref points to an older or different document.
- No touched row currently looks like a strong true-positive exact match that the new rule is obviously suppressing by mistake.

### Inferred
- The subgroup-aware review08 rule is mostly catching **real false-positive canonicalizations** rather than harming a high-quality exact-match subgroup.
- This strongly supports the earlier interpretation that the rule is isolating the intended noisy residual mechanism.

### Speculative
- If the project wants to reduce operator review burden after this audit, the next step may be to convert parts of this subgroup from `review` into a still narrower deterministic cleanup rule, e.g. using combinations of:
  - large title mismatch + older Crossref year gap
  - thesis/dissertation source URL signals
  - book-chapter / conference / unrelated-domain Crossref type mismatch
  - obvious cross-language semantic mismatch

## Recommendation
1. **Treat this LLM truth audit as positive evidence for the patch direction.**
2. Do **not** yet claim zero-regression default promotion purely from LLM review, because this is still operator-side judgment rather than deterministic replay evidence.
3. Use this audit to justify one of two next moves:
   - **preferred**: implement a narrower deterministic cleanup micro-patch for the clearly bad subtypes found above;
   - or keep the current rule as a review-only safeguard if minimizing false positive canonicals is more important than review volume.

## Bottom line
My operator judgment is:

> the `targeted_nonarxiv_review08` rule appears to be removing **desirable false-positive canonicals** in essentially all touched cases.

So the rule now has both:
- **good targeting evidence** from replay, and
- **good semantic-direction evidence** from case-level LLM truth audit.

What it still lacks is a deterministic way to recover those gains **without** paying the review-queue cost.
