# Phase 2B decision memo — OpenAlex residual `url_canonical_only` top5 reranking ablation (2026-05-01)

## Objective
Close the pending day10 follow-up by interpreting the same-fixture replay results for a narrow residual-path change:

- control = OpenAlex title `per_page=5` + first-result selection
- treatment = OpenAlex title `per_page=5` + best-accepted reranking

The goal is to decide whether reranking is a real improvement inside the residual `url_canonical_only` path, and what remains unproven for default-runtime promotion.

## Decision
**Treatment wins the day10 ablation and is locally promotable as the preferred companion to residual top5 OpenAlex lookup for `url_canonical_only`.**

This result is strong enough to support:
- enabling `openalex_title_pick_best_accepted_subreasons=['url_canonical_only']`
- whenever `openalex_title_per_page_by_subreason.url_canonical_only=5` is already enabled

This result is **not yet sufficient by itself** to prove that the full package `top1 -> top5 + best-accepted` should replace the current runtime default.

## Known

### Fixed150
- semantic safety remained clean:
  - `canonical_paper_count`: `293 -> 293`
  - `merge_review_queue_count`: `0 -> 0`
  - `severe_doi_conflict_count`: `0 -> 0`
  - candidate diff: no DOI loss, no review added, no semantic regression
- operational improvement was consistent:
  - `provider_intent_count`: `680 -> 657` (`-23`, `-3.4%`)
  - `dispatch_request_count`: `413 -> 390` (`-23`, `-5.6%`)
  - `title_lane_request_count`: `266 -> 243` (`-23`, `-8.6%`)
  - residual unsuppressed `crossref:url_canonical_only`: `52 -> 29` (`-23`, `-44.2%`)
  - `crossref` events: `293 -> 270` (`-23`, `-7.8%`)
  - `crossref` latency: `510,194 ms -> 433,392 ms` (`-15.1%`)
  - total provider latency: `1,004,023 ms -> 838,964 ms` (`-16.4%`)
- quality nudges were positive, not neutral-only:
  - `matched_source_record_count`: `534 -> 536`
  - `normalized_only_fallback_proposal_count`: `40 -> 38`
  - `fallback_to_high_confidence`: `2`

### Fresh30
- semantic safety also remained clean:
  - `canonical_paper_count`: `75 -> 75`
  - `merge_review_queue_count`: `0 -> 0`
  - `severe_doi_conflict_count`: `0 -> 0`
  - candidate diff: no DOI loss, no review added, no semantic regression
- operational improvement repeated at smaller scale:
  - `provider_intent_count`: `181 -> 177` (`-4`, `-2.2%`)
  - `dispatch_request_count`: `112 -> 108` (`-4`, `-3.6%`)
  - `title_lane_request_count`: `73 -> 69` (`-4`, `-5.5%`)
  - residual unsuppressed `crossref:url_canonical_only`: `12 -> 8` (`-4`, `-33.3%`)
  - `crossref` events: `80 -> 76` (`-4`, `-5.0%`)
  - `crossref` latency: `121,782 ms -> 111,112 ms` (`-8.8%`)
  - total provider latency: `228,121 ms -> 213,336 ms` (`-6.5%`)
- quality nudges were again positive:
  - `matched_source_record_count`: `116 -> 117`
  - `normalized_only_fallback_proposal_count`: `21 -> 20`
  - `fallback_to_high_confidence`: `1`

## Interpretation

### Mechanistic reading
The residual subgroup is not purely an OpenAlex recall failure.
A material fraction of the remaining `openalex_title_unmatched` cases are actually **selection failures within already-returned OpenAlex top5 results**.

That matters because the treatment does not ask OpenAlex for a broader or different external search space than control. It wins by making better local use of the same recorded candidate set.

So the causal story is:
1. residual `url_canonical_only` cases trigger OpenAlex title lookup
2. top5 contains an acceptable DOI-bearing result more often than rank-1 alone reveals
3. best-accepted reranking recovers those acceptable later hits
4. recovered DOI-bearing OpenAlex matches then unlock additional post-openalex suppression of redundant `crossref` title work
5. redundant `crossref` calls fall, while semantic outputs remain stable

### Why this is stronger than a latency-only win
If treatment had only reduced requests without improving match/fallback structure, the gain could still be dismissed as fragile or overly incidental.

But here we see all of the following moving in the same direction:
- fewer residual `crossref` requests
- lower latency
- slightly more matched source records
- slightly fewer fallback-only proposals
- a small number of fallback-to-high-confidence upgrades
- zero observed semantic regressions on both slices

That is the signature of a genuinely better local decision rule, not a cosmetic runtime tweak.

## What remains unproven
This ablation isolates:
- **given the same top5 fixture**, reranking beats first-result selection

It does **not** isolate:
- whether the system should globally move from current default `top1` behavior to `top5 + best-accepted`

That promotion decision still requires one more narrow gate, because the unanswered factor is the external retrieval-width change itself (`per_page=1` vs `per_page=5`).

## Recommended next step
If the goal is only to settle the day10 local question:
1. treat reranking as validated inside the residual top5 path
2. keep `best-accepted` coupled to `url_canonical_only` whenever top5 is enabled

If the goal is default-runtime promotion:
1. run one final promotion-gate comparison:
   - current default residual path = `top1`
   - candidate promoted path = `top5 + best-accepted`
2. keep the same fixed + fresh-like semantic bar:
   - no canonical drop
   - no review increase
   - no conflict increase
3. promote only if the full package clears that stricter gate

## Bottom line
**Day10 answered the intended local question cleanly: within a shared top5 result set, reranking is meaningfully better than first-result selection, and it wins without semantic cost.**

The remaining open question is no longer “does reranking help?”
It is only “is the full `top1 -> top5 + reranking` package strong enough to become the default residual runtime path?”
