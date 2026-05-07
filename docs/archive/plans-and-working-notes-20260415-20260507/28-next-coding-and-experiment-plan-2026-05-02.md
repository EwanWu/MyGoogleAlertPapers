# Next coding and experiment plan (2026-05-02)

## Objective
After:
- retaining URL-identity DOI recovery
- rejecting broad non-arXiv top5 expansion
- retaining narrow truncated-title salvage in the default acceptance layer

set the **next programming and experiment plan** for the current default workflow.

This plan should optimize for:
1. narrow semantic wins
2. low regression risk
3. replayable validation
4. minimal reopening of already-closed policy questions

---

## Current state summary
### Already closed / should be treated as fixed for now
- exact `library_prelink` is promoted
- exact same-batch clustering is promoted
- post-openalex conditional suppression for `crossref:url_canonical_only` is promoted
- arXiv-gated residual `top5 + best-accepted` exception is promoted
- non-arXiv `targeted_nonarxiv_reject71_review08` is promoted
- deterministic URL-identity DOI recovery is retained/promoted
- narrow truncated-title salvage is retained in the shared default acceptance layer

### Therefore, the next phase should **not** focus on
- broad provider payload tuning
- broad HTML fetch / DOI scraping
- generic ScienceDirect PII lane
- broad non-arXiv top5 reopening
- generic similarity-threshold relaxation

---

## Recommended next-step thesis
The next worthwhile workstream should be:

> **narrow title-core acceptance repair and residual review-band decomposition, in that order**

Concretely, this means:
1. first target **repository / alternate-location exact-title acceptance-boundary failures**
2. then target **remaining deterministic title-noise cleanup**
3. only after that, revisit whether the surviving non-arXiv review band `(0.71, 0.80]` should be partially collapsed further

---

## Why this order is best
### 1. Acceptance-boundary salvage is the highest-value narrow coding target
Evidence already points to cases like:
- `cand_e6e0961ddf95e426`

Observed structure:
- exact title / effectively exact title
- first-author agreement
- OpenAlex result is likely the right work
- blocked mainly because venue hint conflicts with repository-hosted location metadata

Mechanistic implication:
- this is **not** a broad retrieval problem anymore
- it is a **post-match acceptance-boundary problem**
- it is narrower and lower-risk than reopening top5 policy or global venue relaxation

### 2. Title-noise cleanup still has narrow residue
The truncated-title salvage patch already proved that some residual misses are not provider failures but source-title extraction artifacts.

What remains plausible:
- selected deterministic cleanup for malformed/trailing extraction noise
- possibly exact-title recovery after very narrow normalization

This is still narrower than changing general match standards.

### 3. Review-band collapse is real, but should come after the above two
The phase map correctly identifies the surviving `(0.71, 0.80]` review band as the next open policy question.

But that is a **default-policy** question, not the best immediate coding target.

Reason:
- it changes precision/recall posture more directly
- it is easier to overreach
- the currently observed acceptance-boundary and title-noise cases are more concrete, more local, and more implementation-ready

So the right sequencing is:
- code narrow semantic repairs first
- re-measure residual tail
- only then ask whether the remaining review band should shrink further

---

## Workstream A — OpenAlex repository / alternate-location exact-title salvage (**priority 1**)

### Goal
Recover a very small set of OpenAlex title results that are already strong semantic matches but currently fail because repository-hosted venue metadata vetoes acceptance.

### Recommended implementation posture
Do **not** widen generic `accept_result(...)` first.

Instead, prefer an **OpenAlex-specific salvage path** in:
- `src/mygooglealertpapers/enrich/openalex.py`

Why:
- current `accept_result(...)` does not know provider-specific location/source-type context
- repository/alternate-location behavior is especially OpenAlex-shaped
- keeping the rule provider-local reduces collateral widening

### Proposed coding tasks
1. Extend OpenAlex metadata extraction to expose richer acceptance context:
   - `primary_location.source.type`
   - whether the matched DOI is present in `ids.doi`
   - whether title similarity is exact / near-exact after current normalization
2. Add a narrow OpenAlex-only salvage branch for cases satisfying something like:
   - exact or near-exact title
   - first-author match true
   - provider DOI present and non-conflicting
   - result source type indicates repository / alternate host / non-journal container
   - venue mismatch is the only blocking feature
3. Keep this rule below broad profile policy and above final fallback logic

### Likely code touch points
- `src/mygooglealertpapers/enrich/openalex.py`
- possibly a small helper in `src/mygooglealertpapers/enrich/base.py` only if reusable and still narrow
- tests:
  - extend `tests/test_title_normalization.py` or add a new OpenAlex-focused acceptance test file

### Candidate-driven target set
Seed with confirmed or suspected acceptance-boundary cases:
- `cand_e6e0961ddf95e426`
- any other exact-title / family-true / venue-false repository-hosted large-fixed residuals found in the earlier audit

### Stop rule
Abort this route if medium60 evidence shows:
- review queue increase
- DOI-conflict increase
- more than a tiny changed-set footprint relative to the expected candidates

---

## Workstream B — deterministic title-noise cleanup (**priority 2**)

### Goal
Recover residual cases where the source title is malformed by extraction noise, but the provider result is already semantically correct.

### Scope discipline
Only pursue **deterministic**, visibly interpretable cleanup.

Good targets:
- trailing `. .` / `...` / `…`
- obvious extraction tail truncation already adjacent to the current salvage rule
- narrow normalization helpers that do not alter normal clean titles

Avoid:
- broad fuzzy cleanup
- broad token deletion
- language-agnostic aggressive normalization

### Recommended coding tasks
1. Re-audit the remaining large-fixed unmatched title cases after the retained truncation patch
2. Bucket residual title-noise failures into:
   - still-truncated but missed by current detector
   - malformed punctuation / extraction tail
   - not-noise (true provider mismatch)
3. Only implement a second cleanup rule if at least `2-3` stable candidates share the same deterministic shape

### Likely code touch points
- `src/mygooglealertpapers/enrich/base.py`
- `tests/test_title_normalization.py`

### Stop rule
Do not add a second title-noise patch for singletons.
If the residue is only one-off malformed strings, document them and stop.

---

## Workstream C — review-band decomposition and possible collapse (**priority 3**)

### Goal
After A and B are measured, decide whether part of the remaining non-arXiv review band `(0.71, 0.80]` can be safely collapsed without reopening broad residual risk.

### Important framing
This is a **policy question first**, implementation question second.

### Required precondition
Do not start this before A/B reruns finish.

Reason:
- A/B will change the remaining tail composition
- collapsing review before those repairs land risks solving the wrong residual distribution

### Recommended experiment shape
1. Freeze the then-current default (including retained A/B wins if any)
2. Export the surviving review-band candidates only
3. Perform a candidate-level truth audit on that review slice
4. Only if the band is still coherent, test a very narrow collapse rule

### Likely artifact first, code second
This workstream should probably begin with:
- audit CSV
- short decision memo

not a code patch

---

## Concrete execution order

### Step 1 — residual dataset refresh
Produce one fresh residual audit from the **current true default** (with URL-identity DOI recovery + retained truncated-title salvage).

Needed outputs:
- large-fixed residual CSV
- bucket counts for:
  - exact-title / fam-true / venue-false
  - `0.84 <= sim < 0.90` with visible title noise
  - current review-band survivors `(0.71, 0.80]`

### Step 2 — implement Workstream A only
- add the narrow OpenAlex repository / alternate-location salvage rule
- write targeted tests first
- run targeted tests

### Step 3 — medium60 live gate for A
Minimum required checks vs current default:
- `matched_source_record_count`
- `canonical_paper_count`
- `merge_review_queue_count`
- `severe_doi_conflict_count`
- `dispatch_request_count`
- `title_lane_request_count`
- candidate-level changed set

Promotion gate for A:
- allow small positive semantic delta
- require no review/conflict regression
- require changed-set concentration in expected candidates

### Step 4 — large-fixed validation for A
Only if medium60 is clean.

### Step 5 — decide whether B is still worth coding
If A already removes most of the plausible acceptance-boundary residue, re-audit before touching title-noise again.

### Step 6 — only then start review-band audit
Treat this as a separate decision gate.

---

## Proposed artifact sequence
1. `docs/validation/day14-current-default-residual-refresh-*.csv`
2. `docs/validation/day14-openalex-acceptance-boundary-plan-*.md`
3. targeted code patch + tests
4. `docs/validation/day14-openalex-acceptance-boundary-medium60-*.md`
5. if clean, `docs/validation/day14-openalex-acceptance-boundary-large-fixed-*.md`
6. only afterward: review-band audit memo

---

## Minimal coding checklist
### Before coding
- [ ] export fresh residual buckets from current default
- [ ] confirm candidate list for exact-title/fam-true/venue-false repository-hosted cases
- [ ] confirm whether OpenAlex payload exposes stable source-type signal for the target cases

### Coding A
- [ ] add provider-local OpenAlex acceptance salvage helper
- [ ] keep generic `accept_result(...)` unchanged unless absolutely necessary
- [ ] add positive and negative tests

### Validation A
- [ ] run targeted tests
- [ ] run medium60
- [ ] inspect changed candidates manually
- [ ] run large-fixed only if medium60 is clean

### Coding B only if justified
- [ ] prove repeated deterministic title-noise shape exists
- [ ] add one narrow rule
- [ ] repeat medium60 -> large-fixed gate

### Review-band audit later
- [ ] export surviving `(0.71, 0.80]` review set
- [ ] do candidate-level truth audit before proposing code

---

## Recommendation
If we start the next round now, the best immediate move is:

> **Code and test a provider-local OpenAlex acceptance-boundary salvage for exact-title / first-author-matching repository-hosted residuals, then gate it through medium60 and large-fixed before touching the review band.**

That is the narrowest next step with the best ratio of:
- semantic upside
- implementation clarity
- regression containment
- reproducible validation
