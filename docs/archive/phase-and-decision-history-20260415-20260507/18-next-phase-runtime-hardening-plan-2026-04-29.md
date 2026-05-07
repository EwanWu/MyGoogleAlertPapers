# Next phase plan: runtime hardening after default promotion (2026-04-29)

## Phase goal

After promoting:

1. exact `library_prelink`
2. exact `same_batch_clustering`
3. same-batch-cluster-enabled `identifier_fastpath + title_core`

into the effective default runtime layer, the next phase should shift from promotion to **hardening the residual hot path**.

The main remaining bottleneck is now the **residual title lane**, especially `crossref` title latency.

---

## Phase objective

Reduce synchronous live runtime further **without changing match standards** and without reopening broad policy exploration.

Primary target:

> shrink the residual `crossref` / `openalex` title-core cost that remains after exact prelink + same-batch clustering have already removed the easiest duplicate work.

---

## Coding plan

### Track 1 — title-core observability refinement

Goal: make the residual title lane measurable at the right granularity.

Planned coding tasks:

1. add explicit title-lane reason accounting in enrich dispatch stats
   - how many title requests came from:
     - no identifier available
     - identifier present but not sufficient for provider path
     - cluster leader path
     - post-prelink residual unresolved path
2. add per-provider title-lane subgroup counters
   - `crossref_title_requests`
   - `openalex_title_requests`
   - `shared_title_reuse_request_savings` split by provider
3. surface these in replay validation markdown/json summaries

Why this first:
- current metrics show the bottleneck, but not yet the **residual-cause decomposition** needed to decide the next micro-patch safely.

### Track 2 — stronger exact same-batch leader propagation

Goal: reduce repeated residual title work further without fuzzy matching.

Planned coding tasks:

1. audit current cluster follower coverage
   - identify cases where followers still reach title lane even though the leader has stronger identifiers or resolved provider output
2. if needed, extend leader propagation so followers inherit:
   - stronger identifier intents
   - safe source-record fanout opportunities
   - richer candidate-resolution status evidence
3. add regression tests for mixed leader/follower patterns:
   - leader has DOI, follower only URL
   - leader has PMCID, follower only title+cluster hint
   - 3+ candidate components, not just pairs

### Track 3 — exact source-record / provider-result reuse above query cache

Goal: suppress repeated work when exact same-batch duplicates still survive clustering boundaries.

Planned coding tasks:

1. add a narrow, exact reuse pass before live dispatch:
   - if another candidate in the same run already produced an exact-matching source record, reuse it directly
2. keep this exact-only:
   - DOI
   - PMID
   - PMCID
   - arXiv
   - canonical URL / scholar cluster when already supported by exact cluster rules
3. do not introduce fuzzy title-only reuse here

### Track 4 — crossref title-core micro-optimizations

Goal: reduce remaining wall time after duplicate suppression layers are exhausted.

Candidate coding tasks:

1. tighten when `crossref` title fallback is actually necessary
2. compare provider order / fallback order inside `title_core`
3. evaluate whether `openalex` title should become the first title-core probe in some exact residual cases
4. evaluate narrower `crossref` trigger conditions only if replay evidence shows no semantic regression
5. prefer **conditional post-openalex suppression** over pre-dispatch blanket skipping when the target subgroup contains a mix of:
   - `crossref`-only DOI rescue cases
   - `openalex`-sufficient same-DOI redundant cases
   - preprint-vs-journal conflict cases

This track must stay replay-gated.

---

## Experiment plan

### Experiment A — residual title-lane decomposition baseline

Purpose:
- quantify what fraction of current default runtime is still spent in residual title-core after prelink + same-batch clustering

Design:
- run current promoted default on fixed slice150
- record enriched dispatch summary with new title-cause counters

Decision use:
- identifies which residual subgroup deserves the next micro-patch

### Experiment B — natural duplicate burden measurement

Purpose:
- move beyond the synthetic duplicate stress slice and estimate same-batch clustering benefit on more natural slices

Design:
- replay on at least two slices:
  1. fixed slice150
  2. a fresh-like / more recent ingest slice if available
- compare current promoted default vs same config with clustering disabled

Decision use:
- estimates how much of the synthetic gain transfers to realistic traffic

### Experiment C — leader propagation extension ablation

Purpose:
- test whether stronger exact leader propagation cuts additional title requests

Design:
- control: current same-batch clustering
- treatment: stronger leader propagation patch
- compare:
  - dispatch groups
  - dispatch requests
  - title-core requests
  - matched source records
  - canonical papers
  - review/conflict burden

### Experiment D — crossref title-lane reduction ablation

Purpose:
- target the now-residual hot path directly

Design:
- once title-cause decomposition exists, run narrow control/treatment experiments only on the subgroup responsible for most remaining `crossref` title latency

Decision use:
- determines whether the next default promotion should be:
  - stricter crossref title triggering
  - altered provider ordering
  - tighter degraded-safe budget mode

---

## Anti-overfitting control rules for any stricter runtime rule

The next phase must not confuse **request suppression** with **safe semantic improvement**.

Any stricter trigger / skip rule must be evaluated as a **one-factor ablation** against the current promoted default.

### Required control design

1. **Control = current promoted default**
   - keep `library_prelink`
   - keep `same_batch_clustering`
   - keep current `identifier_fastpath + title_core`
   - allow new observability only; do not change match behavior
2. **Treatment = exactly one narrow rule change**
   - one subgroup at a time
   - one provider path at a time when possible
   - do not bundle multiple stricter rules into a single promotion test
3. **Slices**
   - fixed slice150
   - at least one fresh-like / recent slice
   - synthetic duplicate stress slices may be used for mechanism diagnosis, but **not** as the sole promotion gate
4. **Outputs required for every control/treatment pair**
   - dispatch requests
   - provider latency
   - title-lane subgroup counts
   - matched source records
   - canonical papers
   - merge review burden
   - conflict burden
   - a candidate-diff basket for every semantic delta

### Promotion gate

A stricter rule is eligible for default promotion only if all of the following hold:

1. runtime win replicates on both fixed and fresh-like slices
2. `canonical_paper_count` does not drop
3. `merge_review_queue_count` does not rise materially
4. `severe_doi_conflict_count` does not rise
5. any changed candidate outcome can be manually explained as precision gain rather than recall loss

If a treatment reduces requests but loses canonical papers, increases review burden, or only wins on a synthetic slice, it should stay **experimental only**.

### Practical interpretation

For this phase, the main risk is not under-optimization; it is **over-tightening title fallback triggers** and accidentally converting recoverable papers into misses.

So the default question is not:

> did the new rule save requests?

It is:

> did the new rule save requests **without creating semantic regression**?

### 2026-04-30 fixed-slice outcome: first strict title-lane ablation failed promotion gate

The first one-factor strict rule test was:

- treatment: skip `crossref` title-lane subgroup `url_canonical_only`
- method: control recorded fixture first, treatment replayed against the same fixture

Result on fixed slice150:

- operational win existed (`crossref` title work and latency dropped sharply)
- but the rule caused **clear semantic regression**
- specifically, it removed `crossref`-only title recoveries for **30 candidates**, each losing DOI-bearing high-confidence metadata and falling back to `normalized_only`
- only **1** candidate improved, where skipping `crossref` removed a preprint-vs-journal DOI conflict and let the `openalex` journal record canonicalize cleanly

Therefore:

- this rule is **rejected for promotion**
- for promotion purposes, it does **not** need a fresh-like confirmation run because it already fails the fixed-slice semantic gate decisively
- if revisited, the next hypothesis must be **strictly narrower** than provider+subreason blanket skipping
- current best next hypothesis: do **not** pre-skip all `crossref:url_canonical_only`; instead test whether `crossref` can be suppressed **after** a successful `openalex` DOI-bearing title recovery for that subgroup

See validation note:
- `docs/validation/day8-crossref-url-only-ablation-fixed150-20260430.md`

### 2026-04-30 fixed-slice outcome: post-openalex conditional suppression passes the first gate

The narrower follow-up test was:

- treatment: keep `crossref:url_canonical_only` by default, but suppress it **only after** `openalex` has already produced a DOI-bearing title recovery for that subgroup
- method: same fixed slice150, same recorded control fixture, treatment replayed against that fixture

Result on fixed slice150:

- the rule suppressed **76 groups / 77 intents** post-openalex
- dispatch requests fell **487 -> 411**
- crossref events fell **368 -> 291**
- crossref latency fell **610,951 ms -> 391,016 ms**
- total provider latency fell **928,175 ms -> 743,555 ms**
- canonical papers improved **292 -> 293**
- merge review queue improved **1 -> 0**
- severe DOI conflicts improved **1 -> 0**
- `normalized_only` fallback proposals stayed flat at **38 -> 38**
- candidate-level review showed **0 DOI-loss regressions**, **0 high-confidence -> fallback collapses**, and **1** retained precision gain case (`cand_e7ece68ba869a802`)

Therefore:

- this narrower rule **passes the fixed-slice semantic gate**
- it appears to preserve the 30 `crossref`-only DOI rescue cases that broke the blanket skip rule
- it keeps roughly **60%** of the earlier blanket-skip request savings while removing the previously observed semantic regression
- it is now the leading promotable Phase 2A strict-rule candidate, but it still **requires a fresh-like / recent-slice control+treatment confirmation run before promotion**

See validation note:
- `docs/validation/day8-crossref-url-only-post-openalex-ablation-fixed150-20260430.md`

### 2026-04-30 fresh-like outcome: post-openalex conditional suppression also passes the second gate

The follow-up confirmation test used:

- source slice: the repo's best currently documented fresh-like cached slice `data/mgap_fresh30_20260410.db`
- control: current promoted default same-batch-cluster profile
- treatment: the same `post_openalex_skip_crossref_url_only` profile
- method: control recorded fixture first, treatment replayed against the same fixture

Result on the fresh-like slice:

- post-openalex suppressed **15 groups / 15 intents**
- dispatch requests fell **127 -> 112**
- title-lane requests fell **88 -> 73**
- crossref events fell **95 -> 80**
- crossref latency fell **144,595 ms -> 107,781 ms**
- total provider latency fell **233,096 ms -> 195,002 ms**
- canonical papers stayed flat **75 -> 75**
- merge review queue stayed flat **0 -> 0**
- severe DOI conflicts stayed flat **0 -> 0**
- `normalized_only` fallback proposals stayed flat **20 -> 20**
- candidate-level review showed **0 DOI-loss regressions**, **0 confidence collapses**, **0 canonical changes**, and **0 new review cases**

Therefore:

- the rule now has a runtime win on both the fixed slice and the best currently available fresh-like slice
- the fresh-like slice reproduces the same core mechanism seen on fixed slice: `crossref` support is removed only when `openalex` is already present, with no observed semantic regression
- under the current Phase 2A promotion gate, this rule is now **eligible for promotion**
- caveat: the second gate used a cached fresh-like slice from `2026-04-10`, not a newer ingest slice, so a later truly recent slice would still be useful as extra confirmation if one becomes available

See validation note:
- `docs/validation/day8-post-openalex-fresh30-ablation-20260430.md`

---

## Monitoring / execution rule for all future long runs in this phase

Every experiment in this phase must follow the hardened owner-wake rule:

1. write state file
2. create `cron(sessionTarget=current, delivery.mode=none)` before launch
3. only then start background replay
4. on wake, reread state file first
5. completion detection alone does not count as task completion

No exceptions for background `exec` visibility or system completion messages.

---

## Recommended immediate next move

Start with:

1. **Track 1** (title-core observability refinement)
2. then **Experiment A** (residual title-lane decomposition baseline)

Reason:
- the next phase should optimize the remaining bottleneck by mechanism, not by guesswork.
