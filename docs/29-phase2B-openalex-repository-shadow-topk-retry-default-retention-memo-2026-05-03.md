# Phase 2B default-retention memo: OpenAlex repository-shadow topk retry (2026-05-03)

## Short answer
**Yes — keep it in the current default code path.**

But this is **not** a YAML-profile promotion in the narrow sense.
The patch lives in:
- `src/mygooglealertpapers/enrich/openalex.py`

So the real decision is:
> should the current mainline default runtime keep the narrow repository-shadow `top1 -> retry top5 -> pick accepted journal result` repair enabled in the shared OpenAlex title path?

My answer is **yes**.

---

## What is being retained
When an OpenAlex title query runs at `per_page=1`, and the returned top1 record has the following narrow shape:
- exact / near-exact title match
- first-author agreement
- provider result is a **repository** record
- work type is `article`
- not a preprint / posted-content case
- venue hint and returned venue are in **explicit mismatch**
- no year conflict

then the runtime does **one** additional OpenAlex retry at `per_page=5`, and if a later result passes the existing accepted-result check, it replaces the repository-shadow top1.

This is intentionally narrower than:
- broad `top1 -> top5` default promotion
- blanket repository result distrust
- generic title-threshold loosening

---

## Where the default actually binds
Current promoted default profile remains:
- builtin runtime default in `src/mygooglealertpapers/config.py`
- canonical combined profile:
  `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`

Important detail:
- the repository-shadow retry is **below** the YAML-profile layer
- it lives inside the OpenAlex title fetch path itself
- therefore “固化” here means:
  - **retain this code-level repair in the default runtime**,
  - not create yet another profile fork

The environment variable:
- `MGAP_OPENALEX_REPO_SHADOW_TOPK_RETRY`

should now be interpreted as an **operator-side emergency rollback switch**, not as the normal way to opt into the feature.

---

## Evidence base

### 1. Mechanism diagnosis was real and narrow
The motivating case was not a hypothetical pattern.
Representative evidence showed that a repository-hosted OpenAlex top1 could look superficially aligned on title/author while still carrying the **wrong DOI / wrong venue surface**.

Key representative case:
- `cand_e6e0961ddf95e426`
- repository top1 DOI: `10.5167/uzh-433681`
- correct journal DOI: `10.1016/j.ejrad.2026.112801`

Interpretation:
- directly relaxing repository top1 acceptance would be unsafe
- but a **narrow local retry** is mechanistically justified

### 2. Medium60 clean on/off gate passed
Artifacts:
- `docs/validation/day14-openalex-repo-shadow-medium60-baseline-off-20260502.md`
- `docs/validation/day14-openalex-repo-shadow-medium60-20260502.md`

Headline result:
- `matched_source_record_count 84 -> 84`
- `canonical_paper_count 48 -> 48`
- `merge_review_queue_count 2 -> 2`
- `severe_doi_conflict_count 2 -> 2`
- `dispatch_request_count 74 -> 73`
- `title_lane_request_count 55 -> 54`

Interpretation:
- no semantic regression
- 1 expected residual Crossref title request removed
- changed set stayed concentrated where expected

### 3. Large-fixed clean control vs treatment confirmed promotion-grade value
Control basis:
- use the **clean rerun control**, not the incomplete original baseline-off and not the forensic recovered copy

Artifacts:
- control report: `docs/validation/day14-openalex-repo-shadow-large-fixed-baseline-off-rerun-20260503.json`
- treatment report: `docs/validation/day14-openalex-repo-shadow-large-fixed-20260503.json`
- root-cause + comparison memo: `docs/validation/day14-large-fixed-baseline-off-root-cause-and-rerun-comparison-20260503.md`

Top-line deltas (treatment minus clean control):
- `provider_intent_count 702 -> 675` `(-27)`
- `source_record_count 702 -> 675` `(-27)`
- `matched_source_record_count 532 -> 533` `(+1)`
- `merged_metadata_proposal_count 356 -> 357` `(+1)`
- `canonical_paper_count 281 -> 282` `(+1)`
- `merge_review_queue_count 2 -> 2` `(0)`
- `severe_doi_conflict_count 2 -> 2` `(0)`
- `dispatch_request_count 434 -> 408` `(-26)`
- `title_lane_request_count 287 -> 261` `(-26)`
- `total_provider_latency_ms 3459062 -> 634458`

Mechanism counters moved in the expected direction:
- `post_openalex_suppressed_group_count 53 -> 79` `(+26)`
- `post_openalex_unsuppressed_targeted_group_count 73 -> 47` `(-26)`

Interpretation:
- this is not just runtime noise
- the patch is doing the intended thing: convert a narrow residual subgroup from “OpenAlex top1 miss + Crossref cleanup” into “OpenAlex local rescue + Crossref suppression”

### 4. Review / conflict burden did not worsen
Review members stayed unchanged:
- `cand_380600011de29f8b` → `severe_conflict:doi`
- `cand_3a6f282d35458d76` → `severe_conflict:doi`

So the retained default does **not** buy efficiency by hiding conflict cases.

### 5. The semantic gain was small but real
Only treatment gained one extra canonical candidate relative to the clean control:
- `cand_f3f78ee6a4d53c12`

Treatment resolved it to:
- DOI: `10.15496/publikation-117956`
- venue: `Open MIND`
- year: `2026`

And importantly:
- there were **no** control-only canonical candidates lost under treatment

---

## What this decision does **not** mean

### It does not reopen broad Phase 2B top5 promotion
The earlier broad result still stands:
- **do not** promote general non-arXiv `url_canonical_only` `top1 -> top5 + best-accepted`

This repository-shadow repair is acceptable only because its activation scope is much narrower and explicitly conditioned on a bad top1 shape.

### It does not justify blanket distrust of repository records
Some repository-hosted records are legitimate and should remain usable.
This patch is not saying “repository == reject”.
It is saying:
- in one narrow mismatch shape,
- do one local retry before falling through to the rest of the pipeline.

### It should not be sold as a universal wall-time promise
The safe promotion claim is:
- fewer residual title requests
- lower request burden in the touched subgroup
- no observed review/conflict regression
- slight semantic improvement on the validated large-fixed gate

Not:
- guaranteed fixed latency multiplier on every future live run.

---

## Operational consequence
### Recommended default posture
- keep repository-shadow topk retry **enabled in the default runtime path**
- do **not** fork a new profile for it
- treat `MGAP_OPENALEX_REPO_SHADOW_TOPK_RETRY=0` only as rollback / debugging escape hatch

### Why this is the correct “固化” action
Because the patch is:
1. **narrowly triggered**
2. **mechanistically justified**
3. **clean on medium60**
4. **positive on large-fixed**
5. **non-regressive on review/conflict burden**
6. **implemented below profile level**, so code-level retention is the correct integration layer

---

## Final posture
### Known
- repository-shadow top1 drift is a real failure mode
- broad top5 promotion remains rejected
- narrow repository-shadow retry passed medium60 safety gate
- narrow repository-shadow retry beat the clean large-fixed control on both request shape and top-line output
- no new review/conflict burden was introduced

### Inferred
- this patch is strong enough to remain part of the current promoted default runtime
- the correct justification is **precision-preserving residual routing repair plus request suppression**, not “free speedup” rhetoric

### Speculative
- if a future runtime materially changes OpenAlex ranking behavior or venue-signal availability, this activation rule may deserve re-audit
- for now, current evidence supports retaining it as part of the default mainline path

---

## Bottom line
The correct project-level conclusion is now:

> **OpenAlex repository-shadow topk retry should be retained in the current builtin default runtime as a narrow code-level repair.**
> It is not a broad residual-path upgrade, not a new profile fork, and not a blanket repository distrust rule. It is a validated local fix for a specific top1 failure mode that reduces residual Crossref title work while preserving safety.
