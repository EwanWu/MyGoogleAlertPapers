# Package B larger-slice150: v2 vs v4 decision analysis (2026-04-16)

## Purpose

Explain why `conditional_sources_v4_fallback_guardrail_salvage` looked acceptable on the earlier 249-candidate slice but regressed materially on the formal larger fixed seed (`368 candidates / 1405 provider intents`), then turn that into a deployment recommendation and a narrow optimization plan.

## Executive decision

**Decision:** do **not** promote `v4` as the broader Package B default.

For the formal larger same-seed replay:

- `v2`: `293 canonical / 2 review / 368 proposal / 777 matched_source_record`
- `v4`: `284 canonical / 10 review / 367 proposal / 780 matched_source_record`

So `v4 - v2` is:

- `canonical_paper_count: -9`
- `merge_review_queue_count: +8`
- `merged_metadata_proposal_count: -1`
- `matched_source_record_count: +3`
- `total_batch_duration_ms: -15981`
- `total_provider_latency_ms: -16813`

Interpretation:

- `v4` gets **slightly more matched source records**,
- but that does **not** turn into better merge output,
- and instead it blocks materially more candidates at the fallback-guardrail layer.

The runtime win is negligible relative to the output loss.

## Core mechanism

The regression is **not** an enrich/runtime problem in the completed formal comparison. The formal rerun completed cleanly on both sides. The regression comes from the **merge fallback policy**.

More specifically:

- the larger-slice regression is dominated by **normalized-only fallback cases**,
- `v4` adds a broad title-similarity guardrail over those cases,
- on the larger slice, that guardrail converts multiple previously-accepted `v2` fallback canonicalizations into review or rejection,
- but the recovered `+3 matched_source_record` does not compensate for those blocks.

In short, **v4 is stricter in exactly the region where the larger slice contains more noisy but still practically usable fallback-only candidates**.

## What changed case-by-case

Relative to `v2`, `v4` loses **9 linked canonical outcomes**.

Breakdown:

1. **8 candidates moved from canonicalized in `v2` to review in `v4`**
2. **1 candidate disappeared from proposal/canonical output entirely in `v4`**

The two original severe DOI-conflict review cases are unchanged between `v2` and `v4`.

### New `v4` review reasons

`v4` review queue reason counts:

- `fallback_guardrail:low_source_title_similarity` × `6`
- `fallback_guardrail:sparse_metadata_low_source_title_similarity` × `1`
- `fallback_guardrail:title_has_author_tail_pollution` × `1`
- existing severe conflicts unchanged:
  - `severe_conflict:doi` × `1`
  - `severe_conflict:doi,venue` × `1`

### The 8 new `v4` review cases

1. `cand_054270b0fef2b17a`
   - title: `Современные возможности бесконтрастной МР-перфузии: от научных исследований до клинической практики`
   - reason: `low_source_title_similarity`
   - max similarity: `0.446`
   - metadata present: author + venue + year

2. `cand_35c39e1b2ee566cc`
   - title: `Spironolactone, Early Acute eGFR Changes, and Clinical Outcomes in Patients with Heart Failure with Preserved Ejection Fraction: Insights from TOPCAT Americas`
   - reason: `title_has_author_tail_pollution`
   - max similarity: `0.0`
   - identifier present: yes (`doi_extracted` present)

3. `cand_3c0daf67a3c4f756`
   - title: `Domain-Guided Machine Learning for High-Dimensional Multi-Modal Neuroimaging and Biomarker Integration in Alzheimer's Disease`
   - reason: `low_source_title_similarity`
   - max similarity: `0.415`
   - metadata present: author + year, venue missing

4. `cand_505b2326b7b8f0e5`
   - title: `Measuring blood flow and pulsatility with MRI: optimisation, validation and application in cerebral small vessel`
   - reason: `sparse_metadata_low_source_title_similarity`
   - max similarity: `0.455`
   - metadata present: none of author / venue / year

5. `cand_693adeec78169f65`
   - title: `Background and aims: Hybrid atrial fibrillation (AF) ablation ...`
   - reason: `low_source_title_similarity`
   - max similarity: `0.420`
   - metadata present: author + venue + year

6. `cand_8c0fcffbabdce4e6`
   - title: `Perivascular space (PVS) volume on cranial ultrasonography in neonates ...`
   - reason: `low_source_title_similarity`
   - max similarity: `0.419`
   - metadata present: author + venue + year

7. `cand_cc340e92866d3360`
   - title: `食管鳞癌免疫微环境异质性及免疫治疗联合策略`
   - reason: `low_source_title_similarity`
   - max similarity: `0.381`
   - metadata present: author + venue + year

8. `cand_e4783c70fe9603a2`
   - title: `基于血管内超声分析载脂蛋白B 控制水平对冠状动脉斑块进展影响的队列研究`
   - reason: `low_source_title_similarity`
   - max similarity: `0.291`
   - metadata present: author + venue + year

### The 1 extra hard loss in `v4`

`cand_400e144162689110`

- `v2`: produced a normalized-only fallback proposal and was linked into canonical output
- `v4`: produced **no** `merged_metadata_proposal`
- normalized title: `Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3`

Interpretation:

- this looks like an **obvious malformed / author-blob title**,
- so this is the **one part of stricter filtering that is plausibly desirable**,
- but by itself it does not justify the broader `v4` regression.

## Why the 249-candidate slice made `v4` look acceptable

Because the earlier slice was too small and too local to expose the full cost of the new broad guardrail.

On the 249-candidate slice, `v4` looked good because:

- it rescued **one** high-precision salvage case,
- and the added guardrail did not yet hit many additional borderline normalized-only cases,
- so the apparent effect looked like a net improvement.

On the larger fixed seed, the picture changes:

- the **salvage upside stays small**,
- but the **blocking cost grows**,
- because the larger slice contains more multilingual, weak-match, or metadata-imperfect normalized-only candidates,
- and the generic similarity thresholds fire more often than the earlier slice suggested.

So the earlier apparent win was not pure noise, but it was **not representative enough for deployment selection**.

## What this says about the v4 design

The problem is **not** that the idea of guardrailing fallback-only merges is always wrong.

The problem is that `v4` mixes together two very different behaviors:

1. **high-precision corruption detection**
   - e.g. obvious author-blob / malformed-title patterns
2. **broad low-similarity skepticism**
   - generic title-similarity thresholds over normalized-only candidates

The larger-slice result says:

- the first class may be useful,
- the second class is currently too expensive in recall for Package B.

## Recommended deployment decision

### Default recommendation

Keep **`v2`** as the broader/default Package B recommendation.

Reason:

- it wins on the larger formal same-seed comparison,
- the loss from `v4` is not marginal,
- and the user preference for this stage is overall performance rather than maximum conservatism on a handful of fallback-only cases.

### Status of `v4`

Demote `v4` from “best current candidate” to **narrow local experiment / diagnostic branch**.

It is still useful as:

- a stress test for fallback-only failure modes,
- a source of candidate heuristics,
- an audit profile for suspicious normalized-only cases.

But it is **not** the right broader default.

## Optimization plan

### Option A, recommended: narrow the guardrail back down

Build the next iteration around this rule:

- **keep only the highest-precision anti-garbage logic**,
- **remove generic low-similarity review blocking from the default path**.

Concretely:

1. Keep obvious malformed-title / author-blob rejection logic.
2. Do **not** default-block canonicalization for generic `low_source_title_similarity` on normalized-only fallbacks.
3. Do **not** default-block canonicalization for `sparse_metadata_low_source_title_similarity` unless independent evidence shows strong precision gain at acceptable recall cost.
4. Keep salvage logic only if it is tied to a demonstrably high-precision corruption pattern, not to a broad threshold rule.

This yields a direction closer to:

- `v2` behavior for broad fallback recall,
- plus a **very narrow** anti-garbage filter,
- without dragging in the broader `v4` review inflation.

### Option B, not recommended as default: keep `v4` only as audit mode

Use `v4` only when the goal is:

- conservative review generation,
- manual QA of fallback-only cases,
- policy debugging.

Not recommended for default production replay because the larger-slice recall hit is too visible.

## Decision-relevant summary

If we reduce the formal larger-slice comparison to one sentence:

> `v4` does not fail because enrich got worse; it fails because its broader fallback guardrail blocks too many normalized-only cases that `v2` would have carried through, while the salvage upside remains too small to pay for that stricter behavior.

## Operational note

This comparison was completed with no paid LLM path exercised.

- paid_llm_usage_present: `false`
- note: `No paid LLM call path was exercised in this replay run.`

## Recommended next action

If continuing Package B policy work, the next step should be:

1. **restore `v2` as the broader recommendation**, and
2. prototype a **much narrower post-v2 anti-garbage patch** that targets only obvious malformed-title / author-blob cases, then
3. rerun on the same larger fixed seed before making any new claim of improvement.
