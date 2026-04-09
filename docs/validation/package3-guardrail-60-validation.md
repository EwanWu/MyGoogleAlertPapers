# Package 3 guardrail validation on real 60-mail slice

## Date
2026-04-09

## Purpose
Validate the new merge/canonical guardrail logic on the larger 60-mail real-mailbox slice after the successful 30-mail guardrail check.

This rerun focuses on the post-enrichment merge/dedup behavior only.

---

## Input database
- source DB: `data/mgap_pkg3_fix_60.db`
- validation DB copy: `data/mgap_pkg3_guardrail_60.db`

Reset before rerun:
- `merged_metadata_proposal`
- `candidate_paper_link`
- `canonical_paper`
- `merge_review_queue`

Then rerun:
- `merge-metadata --limit 200`
- `dedup-candidates --limit 200`
- `report-merge`
- `report-dedup`
- `report-review-queue`
- `export-review-queue`

---

## Aggregate results

### Merge
- merged proposals: 114
- proposals with conflicts: 43
- low-confidence proposals: 24
- canonical-blocked proposals: 12
- grade A conflicts: 19
- grade B conflicts: 2
- grade C conflicts: 22

### Dedup
- paper candidates: 135
- canonical papers: 92
- candidate-paper links: 102
- blocked-for-review candidates: 12
- compression ratio: `92 / 135 = 0.681`

### Review queue
- blocked candidates: 12
- all 12 blocked for: `severe_conflict:doi`

Review export:
- `data/exports/mgap_pkg3_guardrail_60_review.jsonl`

---

## Comparison against prior 60-mail fix summary
Reference doc:
- `docs/validation/package3-fix-60-summary.md`

Earlier 60-mail fix summary:
- matched source records: 288
- merged proposals: 114
- proposals with conflicts: 46
- canonical papers: 101

Current guardrail run:
- merged proposals: 114
- proposals with conflicts: 43
- canonical papers: 92
- blocked-for-review: 12

### Interpretation
1. Proposal count stayed fixed (`114 -> 114`), so the merge stage remained stable structurally.
2. Conflict count decreased slightly (`46 -> 43`).
3. Canonical paper count dropped (`101 -> 92`) because 12 severe DOI-conflict cases were kept out of the canonical store.
4. This indicates the guardrail is doing real filtering, not just reporting.

---

## What this suggests

### Positive signal
The same pattern seen on the 30-mail slice reproduces on the 60-mail slice:
- stable proposal count
- slightly improved conflict count
- materially lower canonical promotion under severe DOI disagreement

### Important implication
The current prototype was still allowing a meaningful number of high-risk DOI-conflict cases into canonical papers on the larger slice.
The new guardrail prevents that.

### Cost of conservatism
The system now produces fewer canonical papers in this run.
That is expected and acceptable at the current stage because the project goal is a conservative main store, not maximum automatic promotion.

---

## Current judgment
The A-route guardrail work is now validated on both:
- 30-mail slice
- 60-mail slice

The strongest confirmed rule is:
- **severe DOI disagreement should block canonical promotion and route the case to review**

That rule appears high-value and low-regret.

---

## Recommended next move
1. keep the DOI severe-conflict block rule as default
2. inspect the 12 blocked 60-mail cases for recurring provider failure patterns
3. decide whether PMID-linked DOI contradiction should be treated even more explicitly earlier in merge preference logic
4. only then consider whether title-grade-C blocking should be widened, narrowed, or left unchanged
