# Package 3 guardrail validation on real 30-mail slice

## Date
2026-04-09

## Purpose
Validate the new A-route merge/canonical protection layer after adding:
- conflict grading (A / B / C)
- severe-conflict canonical blocking
- blocked-case review queue export

This validation reuses the existing 30-mail real-mailbox slice DB state and reruns only the merge/dedup stages with the new guardrail logic.

---

## Input database
- source DB: `data/mgap_pkg3_fix_30.db`
- validation DB copy: `data/mgap_pkg3_guardrail_30.db`

Reset before rerun:
- `merged_metadata_proposal`
- `candidate_paper_link`
- `canonical_paper`
- `merge_review_queue`

Then rerun:
- `merge-metadata --limit 100`
- `dedup-candidates --limit 100`
- `report-merge`
- `report-dedup`
- `report-review-queue`
- `export-review-queue`

---

## Aggregate results

### Merge
- merged proposals: 51
- proposals with conflicts: 23
- low-confidence proposals: 13
- canonical-blocked proposals: 3
- grade A conflicts: 10
- grade B conflicts: 2
- grade C conflicts: 11

### Dedup
- paper candidates: 59
- canonical papers: 42
- candidate-paper links: 48
- blocked-for-review candidates: 3
- compression ratio: `42 / 59 = 0.712`

### Review queue
- blocked candidates: 3
- all 3 blocked for: `severe_conflict:doi`

Review export:
- `data/exports/mgap_pkg3_guardrail_30_review.jsonl`

---

## Comparison against prior Package 3 fix run
Reference doc:
- `docs/validation/package3-iter2-fix-30.md`

Earlier 30-mail fix run:
- matched source records: 139
- merged proposals: 51
- proposals with conflicts: 24
- canonical papers: 45

Current guardrail run:
- merged proposals: 51
- proposals with conflicts: 23
- canonical papers: 42
- blocked-for-review: 3

### Interpretation
1. The merge layer stayed stable in proposal count (`51 -> 51`).
2. Conflict count did not increase and decreased slightly (`24 -> 23`).
3. Canonical paper count decreased (`45 -> 42`) exactly because 3 severe DOI-conflict cases were blocked instead of promoted.
4. This is the intended conservative behavior.

---

## Blocked cases surfaced by the new guardrail

### 1. `cand_cc44f69d04ae056e`
- preferred DOI path: `10.1136/bmjopen-2025-114232`
- conflicting DOI path: `10.1056/nejmoa2310234`
- PubMed and OpenAlex share PMID but disagree on DOI
- correctly routed to review queue instead of canonical store

### 2. `cand_671ed1ecf3aa215c`
- Crossref/OpenAlex agree on DOI: `10.1038/s43856-026-01413-z`
- PubMed returns DOI: `10.1016/j.stlm.2025.100196`
- PMID agreement would previously risk false certainty
- now blocked correctly

### 3. `cand_5755410c2959d9d4`
- previously identified as a hard ambiguous case
- Crossref/OpenAlex DOI: `10.3174/ajnr.a9072`
- PubMed DOI: `10.1161/jaha.122.025853`
- now blocked correctly and exported for review

---

## What this validation confirms

### Confirmed
- severe DOI disagreement no longer silently populates canonical papers
- blocked cases are preserved in a structured review queue
- exported JSONL now contains:
  - normalized candidate fields
  - preferred merged fields
  - raw candidate title/link context
  - per-source evidence rows
  - conflict assessment payload

### Not yet confirmed
- how many Grade C title-only cases should be blocked on larger slices
- whether some grade thresholds should be loosened/tightened before the next 60-mail rerun

---

## Current judgment
This guardrail pass is useful and conservative in the right way.

It does not try to solve all ambiguity.
It does stop a specific class of high-risk DOI disagreement from poisoning the canonical store.

That is a good trade at the current project stage.

---

## Recommended next move
1. keep the DOI/PMID severe-conflict block rule
2. inspect the 3 blocked review cases manually
3. then rerun the same guardrail logic on the 60-mail validation slice
4. only after that, decide whether title-grade-C blocking should remain as strict as it is now
