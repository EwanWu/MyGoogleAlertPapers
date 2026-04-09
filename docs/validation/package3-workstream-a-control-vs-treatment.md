# Package 3 Workstream A control vs treatment validation

## Date
2026-04-04

## Objective
Evaluate whether a stricter first-pass title-fallback acceptance rule improves enrichment correctness behavior on a larger real-mailbox slice.

This validation uses a larger experimental group than earlier 10-mail smoke slices and follows a control-vs-treatment design.

---

## Experimental design

### Control
- repo state: `ecf781c`
- meaning: after Package 2 first-pass cache hardening, before Package 3 acceptance tightening
- working copy used: `~/NewCareer/Openclaw/proj/MyGoogleAlertPapers_ctrl_pkg3`
- DB: `data/mgap_pkg3_ctrl_30.db`

### Treatment
- repo state: current working tree with stricter `accept_result` / `accept_title_match`
- DB: `data/mgap_pkg3_treat_30.db`

### Shared slice
- mailbox: `issac`
- scan size: 30 unread mails
- Scholar mails detected: 16
- normalized candidates: 59

---

## Metrics

### Control
- candidates: 59
- source records: 177
- matched source records: 132
- merged proposals: 53
- proposals with conflicts: 33
- canonical papers: 47
- provider matched breakdown:
  - Crossref: 51 / 59
  - OpenAlex: 48 / 59
  - PubMed: 33 / 59

### Treatment
- candidates: 59
- source records: 177
- matched source records: 133
- merged proposals: 52
- proposals with conflicts: 34
- canonical papers: 46
- provider matched breakdown:
  - Crossref: 51 / 59
  - OpenAlex: 47 / 59
  - PubMed: 35 / 59

---

## Immediate interpretation

### What changed
- matched source records changed only slightly (`132 -> 133`)
- merged proposals decreased slightly (`53 -> 52`)
- canonical papers decreased slightly (`47 -> 46`)
- overall conflict count did **not** improve (`33 -> 34`)

### What this suggests
The first stricter acceptance pass did **not** deliver a clear improvement on this slice.
The rule change altered provider composition slightly, but not in a way that materially reduced suspicious merged outcomes.

---

## Representative persistent suspicious examples
The following classes of suspicious examples remained present in both control and treatment outputs:

1. DOI disagreement between a plausible 2026 target paper and an older or semantically different paper
2. PubMed-derived PMID attachment that appears overly confident relative to the candidate title context
3. title-formatting conflicts caused by residual markup or Unicode/style differences
4. venue-label variation that is likely benign but still inflates conflict exposure

Examples seen in both runs include candidates such as:
- `cand_b098eb3ba9e5dd46`
- `cand_b1967575531ec006`
- `cand_7b97f8abac8fb730`
- `cand_2901cc65f3f3a280`
- `cand_5755410c2959d9d4`

---

## Conclusion from first control-vs-treatment pass
The first-pass tightening in `enrich.base.accept_result()` is **not yet sufficient**.

It is likely too coarse because:
- it changes acceptance thresholds globally without enough field-specific rejection logic
- it does not explicitly reject severe identifier contradictions
- it does not distinguish provider-specific failure modes strongly enough

---

## Recommended next refinement
Package 3 should continue, but the next iteration should be more targeted:

1. Add explicit severe rejection logic for DOI contradiction when candidate-side DOI exists.
2. Add provider-specific caution, especially for PubMed title fallback.
3. Move beyond a single tightened similarity threshold and incorporate structured conflict signals earlier.
4. Combine this with merge-side conflict grading rather than expecting title-threshold tuning alone to solve the problem.

---

## Status
Package 3 Workstream A has started, but this first treatment pass should be treated as an exploratory negative/neutral result rather than a final improvement.
