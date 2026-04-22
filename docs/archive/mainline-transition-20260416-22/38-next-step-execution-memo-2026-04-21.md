# Next-step execution memo (2026-04-21)

## 1. Current project position

As of 2026-04-21, the project's mainline policy decision remains:
- default merge policy: `conditional_sources_v2`
- do **not** promote `v2_narrow_antigarbage`
- do **not** promote `v2_author_blob_only` as a live matching-time patch

Track A has now answered two negative questions clearly:
1. the combined narrow anti-garbage patch is too destructive as a default
2. the standalone `author_blob` rule is directionally useful but still too disruptive when applied early enough to perturb provider matching

So the project should stop asking:
> "Should current Track A variants replace `v2`?"

That answer is already **no**.

---

## 2. What problem should be solved next

### Primary next problem

The next problem is:

> Can we keep the useful part of `author_blob` while preventing it from changing provider match selection globally?

This is now the sharpest unresolved issue on the main correctness path.

### Why this is the right next problem

Observed evidence from the completed author-blob-only replay:
- it catches one obviously bad author-blob fallback case
- but it also perturbs provider matching broadly
- and that broad churn causes real metadata regressions (including lost DOI coverage)

Therefore the problem is no longer "whether the idea has value".
The problem is **where in the pipeline the rule should live**.

---

## 3. Recommended next move

## Recommendation

Do **one more Track A refinement**, but only in this much narrower form:

> Move `author_blob` from a live matching-time rule to a final `normalized_only` fallback acceptance filter.

This should be treated as the last high-value Track A correctness experiment before broader attention shifts to Track B.

---

## 4. Exact hypothesis

### Hypothesis

If `author_blob` is applied **only** at the final `normalized_only` fallback acceptance stage, then:
- the obvious garbage case should still be blocked
- provider matching should remain much more stable
- DOI / source-match regressions should be reduced or disappear
- the patch may become small enough to keep as a narrow fallback garbage filter

This is the most causally grounded next test, because it directly targets the mechanism that likely caused the unwanted churn.

---

## 5. Scope of the next coding step

### New experimental profile

Create a new experimental profile, for example:
- `conditional_sources_v2_author_blob_fallback_only`

### Intended behavior

- inherit `conditional_sources_v2`
- do **not** alter provider matching / enrich-side source selection
- do **not** alter early merge matching decisions
- only block a proposal when it is about to be accepted as a weak `normalized_only` fallback and still matches the author-blob bad-shape pattern

### Design rule

This patch must behave like a **late garbage filter**, not like a match-routing policy.

---

## 6. Coding tasks

### A. Locate the acceptance point

In `src/mygooglealertpapers/pipeline/merge.py`:
- identify the exact place where `normalized_only` fallback proposals are accepted into merged output
- separate that acceptance gate from earlier provider-match selection logic if needed

### B. Restrict the rule to late fallback only

Apply author-blob rejection only when all are true:
- proposal is entering via weak `normalized_only` fallback
- title matches the author-blob bad-shape rule
- metadata evidence remains weak (for example no DOI / PMID and weak bibliographic support)

### C. Add traceability

The trace should make it explicit that the block reason is:
- `fallback_only_author_blob_reject`
- not a generic match-time or source-match failure

### D. Tests

Add tests for:
1. obvious author-blob fallback gets blocked at final fallback acceptance
2. normal provider-supported paper is not perturbed earlier in matching
3. provider-matched DOI-carrying cases remain untouched
4. a weak fallback case without author-blob shape still behaves like `v2`

---

## 7. Replay / validation plan

### Control
- `conditional_sources_v2`

### Treatment
- `conditional_sources_v2_author_blob_fallback_only`

### Fixed seed
- same large-slice150 fixed seed used for Track A formal comparisons

### Success criteria

This refined patch is only worth keeping if all are approximately true:
1. obvious garbage author-blob case is still removed
2. canonical count does not materially decline
3. DOI regressions disappear or reduce sharply
4. internal matched-source churn is much lower than the current `author_blob_only` profile
5. review queue does not inflate

### Failure criteria

If the patch still causes visible provider-match churn or metadata regressions, Track A should be considered exhausted for now and priority should move to Track B.

---

## 8. What not to do next

Do **not** spend another cycle on:
- broader anti-garbage rules
- non-English blanket rejection
- author-tail broad review heuristics
- another matching-time patch that perturbs provider selection globally

Those directions already have enough negative evidence.

---

## 9. Sequencing after this step

### If the late-fallback author-blob patch works
- keep it as a narrow fallback garbage filter candidate
- then move to Track B

### If it still fails
- freeze Track A
- keep `conditional_sources_v2` as default
- move project attention to Track B (Unpaywall as optional OA-enhancement provider experiment)

---

## 10. Bottom line

### Recommended immediate next action

Implement and test:
- **`author_blob` as a final `normalized_only` fallback garbage filter only**

This is the smallest remaining Track A experiment that is still mechanistically justified by the current evidence.
