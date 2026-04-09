# Package 3 remaining hard-case profile

## Date
2026-04-09

## Scope
Summarize what remains after three successive correctness/guardrail improvements:
1. conflict grading + canonical blocking
2. PubMed title-fallback DOI suppression under non-PubMed DOI consensus
3. PubMed title-fallback DOI suppression when candidate-side URL / venue / PMCID supports Crossref-side evidence

---

## Current validation state

### 30-mail slice (`data/mgap_pkg3_guardrail_pubmedfix2_30.db`)
- blocked-for-review candidates: 1
- canonical papers: 44
- candidate-paper links: 50

### 60-mail slice (`data/mgap_pkg3_guardrail_pubmedfix2_60.db`)
- blocked-for-review candidates: 0
- canonical papers: 101
- candidate-paper links: 114

---

## Net effect across iterations

### 60-mail slice progression
- guardrail only: blocked `12`, canonical `92`
- + PubMed DOI consensus suppression: blocked `3`, canonical `99`
- + candidate-side support refinement: blocked `0`, canonical `101`

### 30-mail slice progression
- guardrail only: blocked `3`, canonical `42`
- + PubMed DOI consensus suppression: blocked `1`, canonical `44`
- + candidate-side support refinement: blocked `1`, canonical `44`

Interpretation:
- the broad error class has already been removed
- 60-mail slice is now fully clear under current rules
- only one 30-mail residual case remains

---

## Residual case profile

### Remaining blocked case
- candidate: `cand_cc44f69d04ae056e`
- candidate URL: `https://bmjopen.bmj.com/content/bmjopen/16/3/e114232.full.pdf`
- venue guess: `BMJ open`
- OpenAlex DOI: `10.1136/bmjopen-2025-114232`
- PubMed DOI: `10.1056/nejmoa2310234`
- shared PMID: `41840741`

### Why it remains blocked
Current suppression rules require either:
- stronger non-PubMed DOI consensus, or
- candidate-side support for a Crossref-backed DOI path, or
- candidate PMCID conflict against PubMed PMCID

This case has:
- strong candidate-side publisher URL support
- OpenAlex support
- no Crossref support on this slice
- no candidate PMCID support

So it sits in the narrow zone:
- likely wrong PubMed DOI
- but only one non-PubMed DOI provider explicitly supports the alternative DOI

---

## Judgment
This is now a very small residual class.
It does **not** justify broad new threshold changes.

The system is already in a much better state, and the residual ambiguity is narrow enough that overfitting more merge rules may be riskier than simply reviewing the small remainder.

---

## Recommended policy

### Keep as current default
- retain the current guardrail and suppression logic
- accept the remaining single residual blocked case as a review item

### Optional future extension (not urgent)
A next rule could be considered only if this residual pattern becomes common on larger runs:
- allow OpenAlex DOI + strong candidate publisher URL / venue support to suppress conflicting PubMed title DOI even without Crossref confirmation

### Why not do that immediately
- it would rely on a single non-PubMed provider
- current evidence shows the remaining residual class is already tiny
- review cost is now low enough that conservative manual handling is acceptable

---

## Bottom line
The big systematic error was PubMed title-fallback DOI noise.
That problem is now largely controlled.

What remains is small enough to review rather than rush into another automatic rule.
