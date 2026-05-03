# Day13 current-default medium60 runtime check and optimization-space memo (2026-05-02)

## Objective
Run one **representative medium-scale live benchmark** under the **current builtin default workflow** after both retained Phase 2B patches were promoted, and identify the remaining optimization headroom.

## Run
Command:

```bash
PYTHONPATH=src python3 -m mygooglealertpapers.cli benchmark-baseline \
  --preset small-fixed \
  --run-tag day13-new-default-medium60-20260502 \
  --execute
```

Artifacts:
- report json: `docs/validation/day2-baseline-small-fixed-day13-new-default-medium60-20260502.json`
- report md: `docs/validation/day2-baseline-small-fixed-day13-new-default-medium60-20260502.md`
- output db: `data/benchmark/day2_baseline_small-fixed_day13-new-default-medium60-20260502.db`

Policy profile:
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`

## Why this sample is representative enough
- uses the validated fixed slice150 seed
- uses `limit=60`, which is beyond smoke size but well below full150 live cost
- exercises the real current default live provider path rather than fixture replay
- directly exposes runtime shape of the promoted workflow

## Core result
### Output summary
- provider intents: `106`
- matched source records: `83`
- merged proposals: `57`
- canonical papers: `48`
- review queue: `2`
- severe DOI conflicts: `2`

### Runtime summary
- total batch duration: `156847 ms` (`2.61 min`)
- total provider latency: `151028 ms` (`2.52 min`)
- dispatch requests: `75`
- processed runnable intents: `122 / 122`
- request savings vs processed intents: `47`

## Current bottleneck structure
### Provider latency shares
- `crossref`: `82258 ms` (`54.5%`), `44` events, avg `1869.5 ms/event`
- `openalex`: `62726 ms` (`41.5%`), `60` events, avg `1045.4 ms/event`
- `europepmc`: `3178 ms` (`2.1%`), `1` event
- `pubmed`: `2866 ms` (`1.9%`), `1` event

### Dispatch structure
- planned provider intents: `248`
- runnable provider intents after skips: `122`
- final dispatch requests: `75`
- title-lane requests: `56`
- title-lane requests by provider:
  - `openalex = 36`
  - `crossref = 20`

### Residual `url_canonical_only` structure
- identifier-gap title-lane groups by subreason:
  - `url_canonical_only = 58`
  - `mixed_non_doi_identifier = 6`
- identifier-gap request counts by provider/subreason:
  - `openalex:url_canonical_only = 29`
  - `crossref:url_canonical_only = 13`
  - `openalex:mixed_non_doi_identifier = 3`
  - `crossref:mixed_non_doi_identifier = 3`

### Existing savings already working
- shared-title reuse request savings: `8`
  - `crossref = 4`
  - `openalex = 4`
- post-openalex crossref suppression: `16` groups suppressed
- same-batch clustered candidates: `8`

## Comparison to the older medium60 live baseline (2026-04-27)
Reference:
- `docs/validation/archive/day3-runtime-optimization-20260427/recorded_baseline_live_medium60_20260427.json`

### Old -> current
- provider intent count: `248 -> 106`
- matched source records: `137 -> 83`
- canonical papers: `51 -> 48`
- review queue: `2 -> 2`
- severe DOI conflicts: `2 -> 2`
- total batch duration: `675687 ms -> 156847 ms`
- total provider latency: `673055 ms -> 151028 ms`
- dispatch requests: `201 -> 75`

### Interpretation
This is not a strict apples-to-apples semantic baseline comparison, because the current default workflow intentionally changed the policy/runtime shape. But as an operator-side runtime picture, it is still useful:
- the hot path is now dramatically narrower than the older medium60 live path
- `semanticscholar` has disappeared from the default cost center
- `pubmed` / `europepmc` are now only marginal contributors on this sample
- the remaining runtime is now dominated almost entirely by the `crossref + openalex` residual title path

## Optimization space
### Known
1. The biggest remaining runtime burden is now **Crossref residual title work**, not the old broad multi-provider fanout.
2. `openalex` is still the second major cost center, but its average per-event latency is much lower than `crossref`.
3. The promoted savings layers are real but already mostly harvested on this sample:
   - same-batch clustering: present but modest here
   - shared title reuse: present but bounded
   - post-openalex crossref suppression: already saving `16` groups
4. `library_prelink` contributed `0` prelinked candidates on this sample, so it is not the next lever here.

### Inferred
The remaining optimization headroom is now concentrated in a much narrower place:
- **non-arXiv `url_canonical_only` residual title path after OpenAlex fails to resolve the candidate**

This matches the current dispatch summary:
- post-openalex unsuppressed targeted crossref groups: `13`
- all are `openalex_title_unmatched`
- all are `without_arxiv_id`

So the remaining hotspot is no longer “broad provider architecture.”
It is:
- how to further shrink the residual non-arXiv `crossref:url_canonical_only` title requests
- without reopening broad recall or semantic risk

### Rough upper-bound estimate
A naive upper bound for eliminating the remaining `13` unsuppressed residual Crossref title requests is roughly:
- `13 * 1.87 s ≈ 24 s`

That is about:
- `~15%` of current total provider latency
- `~15%` of current end-to-end wall time on this sample

This is only an order-of-magnitude estimate, not a guaranteed realized gain.

## Bottom line
### Known
- the new default workflow completes a representative medium60 live run in about **2.6 minutes**
- the current hot path is now overwhelmingly **Crossref + OpenAlex residual title work**
- the largest remaining specific hotspot is the **non-arXiv `openalex_title_unmatched -> crossref:url_canonical_only` tail**

### Inferred
The new workflow has already captured the large structural wins.
The next meaningful optimization space is now **narrow, late, and residual**, not architectural.

## Recommended next step
If the goal is runtime optimization rather than more policy exploration, the highest-value next experiment is:

> a one-factor runtime probe targeting the surviving non-arXiv `openalex_title_unmatched -> crossref:url_canonical_only` residual tail, with strict replay gating and explicit runtime accounting.

Not recommended:
- reopening broad provider-lane expansion
- revisiting Semanticscholar-like large switches
- broad similarity-based guardrails
