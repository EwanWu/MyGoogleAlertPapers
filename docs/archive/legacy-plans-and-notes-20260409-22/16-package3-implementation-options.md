# Package 3 Implementation Options

## Objective
Finish the next correctness phase after resumability and cache hardening, with emphasis on:
- merge conflict grading
- conservative canonical protection
- keeping the main store trustworthy

---

## Option A: rule-based conflict grading on top of the current pipeline

### Core idea
Keep the existing pipeline shape intact and strengthen `merge.py` with explicit conflict classification and canonical guardrails.

### Main changes
1. add field-level conflict severity grading:
   - Grade A: benign formatting differences
   - Grade B: moderate metadata divergence
   - Grade C: severe identifier/content contradiction
2. compute a structured proposal summary, for example:
   - `conflict_grade_max`
   - `severe_conflict_fields`
   - `canonical_blocked`
   - `canonical_block_reason`
3. downgrade or block canonical promotion when Grade C signals appear
4. add a lightweight export for ambiguous proposals needing review

### Where it lands in code
- `src/mygooglealertpapers/pipeline/merge.py`
- likely small schema extension for `merged_metadata_proposal`
- small dedup/canonical gating changes
- a new reporting/export helper for blocked proposals

### Pros
- smallest change to current architecture
- fastest path to a materially safer main store
- easiest to validate against existing 30/60/100-mail artifacts
- aligns with the current docs and current code trajectory

### Risks
- rule logic may become patchy if expanded too far
- some ambiguous cases still need manual review or later structural redesign
- may reduce recall modestly in exchange for trustworthiness

### Best use case
If the goal is to improve correctness quickly without destabilizing the rest of the pipeline.

---

## Option B: evidence-ledger merge with staged canonical promotion

### Core idea
Treat merge as an evidence aggregation layer, not as a near-final truth picker. Canonical records are promoted only after a second-stage judgment pass.

### Main changes
1. keep all provider assertions as structured evidence votes by field
2. compute per-field support and contradiction explicitly
3. create a staged boundary:
   - `merged proposal`
   - `provisional canonical`
   - `trusted canonical`
4. only promote to trusted canonical when evidence passes stricter rules
5. route unresolved cases into a review queue/export set

### Where it lands in code
- larger refactor of `merge.py`
- likely schema additions for proposal state / promotion state
- likely changes in dedup and canonical write path
- probably a dedicated review/export/report module

### Pros
- cleaner long-term model
- better separation between evidence and canonical truth
- scales better as more providers or heuristics are added
- more naturally supports later human-in-the-loop review

### Risks
- materially larger refactor
- slower to deliver
- more moving pieces to validate before the next large mailbox run
- may be too much architecture before the current prototype fully stabilizes

### Best use case
If the goal is to make this project a longer-lived literature infrastructure layer rather than just harden the current prototype.

---

## My recommendation

### Recommended immediate path
Choose **Option A** now.

Reason:
- current pain is immediate false certainty in merge/canonical output
- the existing pipeline already has enough structure to support conflict grading
- Option A can be implemented, validated, and iterated quickly on current real-mailbox slices

### Recommended longer-term evolution
Keep **Option B** as the next architectural step only if:
- Option A still leaves too many hard ambiguous cases, or
- you want a more formal reviewable evidence model before scaling up to much larger mailboxes

---

## Suggested execution order if we choose Option A

1. normalize conflict comparison more aggressively for title / venue formatting noise
2. add Grade A / B / C conflict classification helpers
3. store structured merge assessment on each proposal
4. block severe-conflict proposals from confident canonicalization
5. export blocked/ambiguous cases for targeted review
6. rerun a 30-mail controlled slice before moving back to 60/100-mail validation

---

## Suggested execution order if we choose Option B

1. define evidence schema and proposal lifecycle
2. split merge aggregation from canonical promotion
3. create provisional vs trusted canonical states
4. add blocked-review export
5. migrate validation reports to reflect staged promotion outcomes
6. rerun 30-mail then 60-mail slices

---

## Decision shortcut

If you want:
- **faster, safer next iteration** -> Option A
- **cleaner long-term architecture** -> Option B
