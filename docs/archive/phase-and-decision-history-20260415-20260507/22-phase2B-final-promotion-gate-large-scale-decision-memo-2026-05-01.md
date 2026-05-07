# Phase 2B final promotion-gate memo — large-scale validation for `top1` vs `top5 + best-accepted` (2026-05-01)

## Objective
Decide whether the residual `url_canonical_only` OpenAlex path should be promoted from the current default:

- **control** = current default residual path (`top1`)

to the larger package:

- **treatment** = `top5 + best-accepted`

This is the stricter gate left open after day10, which had already shown that **within a shared top5 fixture**, `best-accepted reranking` is better than `first-result selection`.

## Scope
Large-scale validation matrix:

- core gate
  - `large_fixed`: 368 candidates
  - `fresh30`: 95 candidates
- auxiliary stress slices
  - `pkg3_guardrail100`: 249 candidates
  - `issac100`: 244 candidates

Total: **956 candidates** across 8 replay runs.

## Decision
**Do not promote `top1 -> top5 + best-accepted` into the default runtime path yet.**

The package passes the **semantic safety gate**, but it does **not** pass a convincing **efficiency / runtime-value gate** at larger scale.

More precisely:
- semantic outcomes remain effectively stable
- residual `crossref:url_canonical_only` work is reduced consistently
- but the added OpenAlex top5 retrieval cost usually outweighs those savings
- aggregate runtime/latency therefore regresses on the larger validation matrix

So the correct current position is:

1. keep the current default residual path at **`top1`**
2. keep the day10 conclusion that **if top5 is used, it should always pair with `best-accepted`**
3. do **not** widen top5 to the default residual runtime path without a narrower activation rule

## Known

### 1) Semantic safety held across all four slices
Across the 4 control/treatment pairs:

- `canonical_paper_count`: unchanged on all slices
- `merge_review_queue_count`: unchanged on all slices
- `severe_doi_conflict_count`: unchanged on all slices
- candidate-level comparison found:
  - **0 DOI lost**
  - **0 DOI gained through regression-like swap artifacts**
  - **0 DOI changed**
  - no title/year semantic changes

Observed candidate-level differences were limited to a handful of **venue-string formatting variations** (for example case/punctuation normalization such as `arXiv preprint arXiv` vs `arXiv`, or venue capitalization differences) while DOI/title/year remained unchanged.

This means the package is **semantically safe enough** for consideration.

### 2) Crossref residual work dropped consistently on all four slices
Treatment reduced residual `url_canonical_only` pressure everywhere:

- **large_fixed**
  - unsuppressed targeted groups: `52 -> 29` (`-44.2%`)
  - dispatch requests: `413 -> 390` (`-5.6%`)
  - title-lane requests: `266 -> 243` (`-8.6%`)
  - crossref events: `293 -> 270` (`-7.8%`)
  - crossref latency: `278,339 -> 259,206 ms` (`-6.9%`)

- **fresh30**
  - unsuppressed targeted groups: `12 -> 8` (`-33.3%`)
  - dispatch requests: `112 -> 108` (`-3.6%`)
  - title-lane requests: `73 -> 69` (`-5.5%`)
  - crossref events: `80 -> 76` (`-5.0%`)
  - crossref latency: `84,328 -> 75,192 ms` (`-10.8%`)

- **pkg3_guardrail100**
  - unsuppressed targeted groups: `39 -> 24` (`-38.5%`)
  - dispatch requests: `289 -> 274` (`-5.2%`)
  - title-lane requests: `184 -> 169` (`-8.2%`)
  - crossref events: `203 -> 188` (`-7.4%`)
  - crossref latency: `234,054 -> 224,483 ms` (`-4.1%`)

- **issac100**
  - unsuppressed targeted groups: `44 -> 25` (`-43.2%`)
  - dispatch requests: `297 -> 278` (`-6.4%`)
  - title-lane requests: `193 -> 174` (`-9.8%`)
  - crossref events: `181 -> 162` (`-10.5%`)
  - crossref latency: `231,250 -> 210,265 ms` (`-9.1%`)

Aggregate across all 956 candidates:
- dispatch requests: `1111 -> 1050` (`-61`, `-5.5%`)
- title-lane requests: `716 -> 655` (`-61`, `-8.5%`)
- unsuppressed targeted groups: `147 -> 86` (`-61`, `-41.5%`)
- crossref events: `757 -> 696` (`-61`, `-8.1%`)
- crossref latency: `827,971 -> 769,146 ms` (`-7.1%`)

### 3) But the OpenAlex top5 expansion usually cost more than it saved
OpenAlex event count is unchanged because the same candidates still query OpenAlex, but per-query payload width rises on the targeted subgroup.

That cost showed up clearly:

- **large_fixed**: OpenAlex latency `239,822 -> 293,146 ms` (`+22.2%`)
- **fresh30**: `64,495 -> 71,181 ms` (`+10.4%`)
- **pkg3_guardrail100**: `174,837 -> 248,158 ms` (`+41.9%`)
- **issac100**: `224,634 -> 267,182 ms` (`+18.9%`)

Aggregate OpenAlex latency:
- `703,788 -> 879,667 ms` (`+175,879 ms`, `+25.0%`)

### 4) Net runtime result was not robustly positive
Total provider latency:
- **large_fixed**: `604,970 -> 693,135 ms` (`+14.6%`)
- **fresh30**: `178,077 -> 193,223 ms` (`+8.5%`)
- **pkg3_guardrail100**: `486,113 -> 511,989 ms` (`+5.3%`)
- **issac100**: `505,109 -> 498,095 ms` (`-1.4%`)

Aggregate total provider latency:
- `1,774,269 -> 1,896,442 ms` (`+122,173 ms`, `+6.9%`)

Total batch duration also regressed in aggregate:
- `1,800,998 -> 1,927,028 ms` (`+126,030 ms`)

So treatment wins on **crossref suppression mechanics**, but loses on **overall runtime efficiency** for 3 of the 4 tested slices.

### 5) Quality nudges were weakly positive but not large enough to justify the runtime tax
Aggregate small improvements:
- matched source records: `1322 -> 1326` (`+4`)
- normalized-only fallback proposals: `141 -> 137` (`-4`)

These are real but modest. They do not compensate for the larger aggregate latency penalty.

## Interpretation

### Mechanistic reading
The full package combines two different effects:

1. **good local decision rule**
   - once top5 results exist, `best-accepted` selection does recover better OpenAlex hits than naive rank-1 selection
2. **expensive retrieval-width expansion**
   - moving from `top1` to `top5` increases OpenAlex payload/selection work on the targeted subgroup

Day10 proved (1).
Day11 tested the combined package `(1) + (2)` against the current default.

The large-scale outcome says:
- the package is **safe**
- the package is **mechanistically real**
- but the package is **not efficient enough as a broad default**

In other words, the reranking idea is sound, but the activation scope of top5 is still too wide for default promotion.

## Promotion-gate judgment

### Passes
- no canonical-count drop
- no review increase
- no severe DOI conflict increase
- no DOI-level semantic regression observed
- consistent reduction in redundant residual crossref work

### Fails / not strong enough
- no robust total-runtime win
- aggregate provider latency gets worse
- 3/4 slices show slower total provider latency
- aggregate benefits in matched/fallback quality are too small to offset the added OpenAlex top5 cost

## Recommendation

### Default-runtime decision
**Keep the current default at `top1`. Do not promote the full `top5 + best-accepted` package yet.**

### What remains valid from day10
**Retain the local rule that whenever top5 is explicitly enabled, it should use `best-accepted` rather than first-result selection.**

### Best next move
Do **not** abandon the idea entirely. Narrow it.

The next promising directions are:
1. activate top5 only for a stricter subset of `url_canonical_only`
   - for example only when some query-shape or title-quality predicate predicts high OpenAlex rescue probability
2. improve OpenAlex query shaping / normalization first
   - to raise rank-1 success without paying top5 width everywhere
3. test capped variants such as
   - top3 instead of top5
   - or top5 only after a cheaper failure signal

## Bottom line
The large-scale final gate changed the answer.

- **Day10 answer**: inside a shared top5 result set, reranking is better than first-result selection.
- **Day11 answer**: the full default-promotion package `top1 -> top5 + best-accepted` is **safe but not efficient enough** to become the new default residual path.

So the promotion should **stop here for now**: keep `top1` as default, keep `best-accepted` as the correct selector whenever top5 is deliberately enabled, and move the next iteration toward a **narrower activation rule** rather than a broad default flip.
