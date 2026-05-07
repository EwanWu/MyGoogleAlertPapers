# Phase 2B promotion posture memo: targeted non-arXiv `reject71 + review08` for residual `url_canonical_only` (2026-05-02)

## Objective
Decide the current promotion posture for:

- `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08`

This is the narrow non-arXiv cleanup route left open after:
1. broad residual `top5` promotion was rejected
2. narrow arXiv-gated `top5 + best-accepted` was promoted into the default runtime

## Decision
**Do not bind this route into the builtin default yet.**

Current posture should be:
- **validated and reproducible leading candidate** for the remaining non-arXiv residual cleanup route
- **not yet a default-runtime promotion**

## Scope of the rule
Inside the narrow subgroup:
- normalized-only fallback
- `openalex_title_unmatched`
- `url_canonical_only`
- missing `arxiv_id_extracted`

apply:
- `<= 0.71` → reject
- `(0.71, 0.80]` → review

## Evidence base
### 1. Truth-audit direction is strong
From `docs/validation/day11-targeted-nonarxiv-review08-llm-truth-audit-20260501.md`:
- the touched cases were overwhelmingly false-positive canonicalizations
- they concentrated in thesis/article, cross-language, author-blob, and related-but-not-identical document mismatches

### 2. Large-scale stable replay effect is concentrated and operationally clean
From `docs/validation/day11-targeted-nonarxiv-reject71-review08-large-scale-validation-20260501.md` across `956` candidates / `4` slices:
- canonical papers: `783 -> 757` (`-26`)
- review queue: `7 -> 8` (`+1`)
- normalized-only fallback proposals: `141 -> 116` (`-25`)
- changed set: only `10` unique candidates
- `9 / 10` changed candidates were already inside the audited bad-match set
- the only new unique candidate was routed to **review**, not reject

### 3. Reproducibility is now closed
From `docs/validation/day12-targeted-nonarxiv-reject71-review08-repro-validation-20260502.md`:
- the new day12 runner reproduced the prior stable replay exactly on all 4 slices
- aggregate exact match held for:
  - canonical papers: `757 -> 757`
  - review queue: `8 -> 8`
  - merged proposals: `928 -> 928`
  - matched source records: `1322 -> 1322`
  - normalized-only fallback proposals: `116 -> 116`

So this route is no longer just a one-off analysis result; it now has a durable execution path.

## Why this is still not a default flip
### Known
- the route removes cases that are mostly already-audited false positives
- the route is targeted and reproducible
- broad spillover has been avoided

### Still unresolved
What is still not fully closed is not reproducibility.
It is **default-policy posture**.

The remaining unresolved point is:
- whether the project is ready to treat this precision-cleanup tradeoff as a permanent default behavior,
- rather than as the current best candidate awaiting one last decision gate.

Mechanistically, this route intentionally lowers canonical output count and adds a very small review burden:
- canonical `-26`
- review `+1`

That can be the *right* trade if these are truly false-positive canonicalizations.
But default promotion should state that explicitly, not smuggle it in as if it were a neutral runtime tweak.

## Promotion posture
### Recommended posture now
Use this language:

> `targeted_nonarxiv_reject71_review08` is the **current best validated candidate** for the remaining non-arXiv `url_canonical_only` residual cleanup route. It has strong truth-audit support, concentrated effect, and now-passed reproducibility. However, because it deliberately converts a small number of previously accepted canonical proposals into reject/review outcomes, it should remain **one step short of builtin default promotion** until the project explicitly accepts that precision-first trade as the desired default policy.

### What this means operationally
- keep the current builtin default unchanged after the arXiv-gated flip
- keep this profile as the primary candidate for the non-arXiv route
- if doing one more narrow step, audit only the surviving review band `(0.71, 0.80]`
- do **not** reopen the full residual class or broad similarity guardrails

## Bottom line
This route has now crossed three bars:
1. **semantic direction** looks right
2. **large-scale effect** is concentrated and useful
3. **runner-level reproducibility** is confirmed

But it has **not yet crossed the final default-policy bar**.

So the correct current conclusion is:
- **retain it as the leading promoted candidate for the route**
- **do not yet bind it into the builtin default**
- **treat the remaining decision as an explicit policy choice, not an engineering uncertainty**
