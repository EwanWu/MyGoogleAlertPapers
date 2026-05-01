# Next-step code and experiment plan after post-openalex promotion (2026-04-30)

## Objective

Now that the narrow `post_openalex_skip_crossref_url_only` rule has been promoted into the default runtime layer, the next phase should shift from **whether this rule is safe** to **how to measure and shrink the remaining residual `crossref` title cost without reopening semantic risk**.

## Known

1. Blanket pre-dispatch skip of `crossref:url_canonical_only` is rejected.
2. Post-openalex conditional suppression passed both:
   - fixed slice150
   - best available fresh-like cached slice
3. The remaining default-layer question is no longer "should we keep this rule?" but:
   - where residual `crossref` title cost still comes from
   - which remaining subgroup is safe to optimize next

## Inferred

The next bottleneck is unlikely to be a broad provider-level rule.
It is more likely one of these narrower mechanisms:

1. **unsuppressed `url_canonical_only` residuals**
   - cases where `openalex` did not recover a DOI-bearing title match, so `crossref` remained necessary
2. **cluster-leader-path residual title work**
   - especially where same-batch clustering still leaves title requests on the leader path
3. **mixed non-DOI identifier residuals**
   - e.g. URL / PMID / PMCID / other partial-identifier shapes where provider asymmetry still forces title fallback

## Next code tasks

### P0 — add post-promotion observability for the *remaining* unsuppressed residuals

Current observability is strong on:
- what got suppressed
- how much request/latency was saved

But it is weaker on:
- why specific `crossref` title-lane groups were **not** suppressible

#### Recommended code changes

1. Add counters for **post-openalex non-suppression reasons** on targeted groups, for example:
   - `openalex_no_doi_title_match`
   - `openalex_no_match`
   - `cluster_leader_path_exempt`
   - `non_target_subreason`
2. Surface these counters in:
   - `pipeline/enrich.py`
   - `pipeline/enrich_stats.py`
   - `scripts/replay_validation.py`
3. Preserve provider + title-subreason breakdown symmetry with the existing `post_openalex_suppressed_*` fields.

#### Why this is first

Without these counters, the next optimization round risks returning to guesswork.
With them, the next candidate patch can again be chosen by mechanism rather than intuition.

---

### P1 — add a candidate-audit export for residual crossref title requests

#### Recommended artifact

A small audit export path that emits, for selected replay runs:
- candidate id
- provider
- title reason / subreason
- whether post-openalex suppression fired
- whether openalex had DOI-bearing title recovery
- whether crossref remained the only DOI rescue

Output can be JSONL or CSV under `docs/validation/` or `data/benchmark/`.

#### Why this matters

The current aggregate counters are enough for promotion decisions, but not ideal for the next micro-patch design loop.
A targeted audit table would make the next residual subgroup immediately inspectable.

---

### P2 — add a default-path smoke check that exercises the builtin profile end-to-end

Current tests verify:
- builtin default profile structure
- baseline helper default path binding

Add one narrow integration smoke test that confirms:
- when no explicit profile is passed,
- the default runtime really carries `title_lane_post_openalex_skip_subreasons_by_provider.crossref = ['url_canonical_only']`
- and dispatch stats expose the expected runtime field.

This is not urgent, but it would make the new default binding more robust against future config drift.

## Next experiments

### Experiment 1 — residual decomposition after promotion

**Purpose**
Find the dominant source of the *remaining* `crossref` title cost under the new default.

**Design**
Run replay on:
1. fixed slice150
2. fresh-like cached slice

Collect:
- total remaining `crossref` title requests
- remaining `url_canonical_only` requests
- remaining `cluster_leader_path` requests
- remaining `mixed_non_doi_identifier` requests
- new non-suppression reason counters
- candidate audit basket for the top remaining subgroup

**Decision use**
This chooses the next micro-patch target.

---

### Experiment 2 — newer recent-slice confirmatory replay when available

**Purpose**
Close the only remaining evidence caveat from the current promotion.

**Design**
When a newer ingest slice exists:
- run control/default vs current promoted default if needed for observability comparison, or
- at minimum run the current promoted default and compare residual subgroup structure against fixed/fresh-like expectations

**Decision use**
Not required to justify the completed promotion, but valuable for drift detection.

---

### Experiment 3 — cluster-leader-path narrowing ablation

Run this **only if Experiment 1 shows cluster-leader-path is now a major residual cost**.

**Hypothesis**
Some remaining title requests may be leader-path artifacts rather than genuinely necessary provider work.

**Constraint**
Must again be a one-factor ablation and must preserve the same semantic gate:
- no canonical drop
- no review increase
- no conflict increase

---

### Experiment 4 — mixed non-DOI identifier rescue-path study

Run this **only if Experiment 1 shows mixed non-DOI identifier residuals are material**.

**Hypothesis**
Some residual title work may be compressible by better identifier harmonization rather than stricter suppression.

This would likely be a better next move than broadening post-openalex suppression.

## Recommended order

### Immediate next build cycle
1. P0 observability for non-suppression reasons
2. P1 candidate-audit export
3. replay Experiment 1 on fixed + fresh-like

### After that
4. choose exactly one next subgroup based on Experiment 1
5. run one-factor ablation only on that subgroup
6. keep newer recent-slice replay as a drift / confidence follow-up when a better slice appears

## What not to do next

1. do **not** broaden suppression from `url_canonical_only` to other title subreasons yet
2. do **not** re-open blanket provider-level skip ideas
3. do **not** bundle multiple residual optimizations into one treatment
4. do **not** weaken the fixed + fresh-like semantic gate just because the current promotion succeeded

## Smallest useful next action

If acting immediately, the best next concrete step is:

> implement **post-openalex non-suppression observability** for residual `crossref` title groups, then rerun a fixed+fresh-like residual decomposition under the new default.

That gives the next code patch a real target instead of another hypothesis-first loop.
