# Phase 2B promotion memo: narrow arXiv-gated `top5 + best-accepted` for residual `url_canonical_only` (2026-05-01)

## Decision

**Promote** the following narrow runtime exception as the next validated residual OpenAlex rule:

- keep the default residual OpenAlex title path at **`top1`**
- but for title-lane subgroup **`url_canonical_only`**
- when **`arxiv_id_extracted`** is present
- activate **`top5 + best-accepted`** instead of `top1`

This rule is implemented by:

- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate.yaml`

Supporting runtime gate is implemented in:

- `src/mygooglealertpapers/pipeline/enrich.py`

## Rollout status

As of this memo:

- rule logic: **implemented**
- profile: **implemented**
- focused tests: **passing**
- builtin default runtime profile: **not flipped in this turn**

So this memo is a **promotion decision + enable recommendation**, not a claim that the project-wide default has already been changed.

## Why this memo exists

Phase 2B produced two distinct conclusions on the same day:

1. `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md`
   - broad `top1 -> top5 + best-accepted` is **semantically safe**
   - but **not efficient enough** for default promotion
2. `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`
   - the useful gains are not spread broadly
   - they are concentrated in a tiny **arXiv-native residual subgroup**

This memo records the decision implied by combining those two findings:

- reject the broad default flip
- promote the narrow exception that preserves the real gain without paying the broad runtime tax

## Promoted rule

Only widen OpenAlex title retrieval when all of the following hold:

1. title-lane reason is the residual identifier-gap path
2. title-lane subreason is **`url_canonical_only`**
3. the candidate has **`arxiv_id_extracted`**

Then:

- OpenAlex title query width = **5**
- selection rule = **`best-accepted`**

Otherwise:

- keep the current default OpenAlex residual behavior = **`top1`**

## Why this rule is the right retained exception

### 1. The broad package failed as a default

From the large-scale promotion gate over **956 candidates**:

- semantic safety held
- but aggregate provider latency worsened
- total batch duration worsened
- the quality gains were real but modest

Therefore broad `top5 + best-accepted` should **not** become the default residual path.

### 2. The useful gains were fully concentrated

Retrospective exact subgroup validation over the completed day11 matrix showed:

- total final-confidence promotions under the broad treatment: **4**
- promotions inside the proposed arXiv-gated subgroup: **4 / 4**
- promotions outside that subgroup: **0**
- fallback reductions outside that subgroup: **0**

So the broad package's real quality benefit was entirely localized.

### 3. Activation size is genuinely narrow

The proposed rule would activate on only:

- **26 / 956 = 2.72%** of candidates

Per slice:

- `large_fixed`: `9 / 368`
- `fresh30`: `6 / 95`
- `pkg3_guardrail100`: `8 / 249`
- `issac100`: `3 / 244`

This is small enough to behave like a targeted exception rather than a hidden broad default flip.

## Promotion evidence

### Broad-gate rejection memo

- `docs/22-phase2B-final-promotion-gate-large-scale-decision-memo-2026-05-01.md`

Key conclusion retained from that memo:

- broad `top5 + best-accepted` is **safe but not efficient enough** as the default residual path

### Narrow-rule decision memo

- `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`

Key conclusion retained from that memo:

- the arXiv-gated narrow rule preserves all observed quality gains at a much smaller runtime cost surface

### Candidate-level retained wins

The four observed confidence promotions preserved by the narrow rule were:

- `cand_7a1dd15089495cf9`
- `cand_40874060f658736c`
- `cand_cd1c124046a3d47d`
- `cand_f23cfc83ef0d4011`

These are documented in `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`.

### Test evidence

Passing focused tests:

- `tests/test_openalex_topk.py`
- `tests/test_openalex_topk_activation_gate.py`
- `tests/test_default_policy_profile.py`

## Promotion-gate verdict

This narrow rule passes the decision gate that the broad rule failed.

### Passes

- preserves the broad treatment's observed output-side gains
- keeps `canonical_paper_count` unchanged
- keeps `merge_review_queue_count` unchanged
- keeps `severe_doi_conflict_count` unchanged
- keeps activation surface extremely small
- converts a broad latency penalty into a much smaller targeted overhead

### Important limitation

This is **not** a throughput / request-elimination promotion.

It should be interpreted as:

- a **small quality-focused rescue patch**
- not a general claim that `url_canonical_only` should broadly move to `top5`

## Recommended enable scope

Promote only the exact rule that has evidence:

- subgroup: residual `url_canonical_only`
- extra predicate: `arxiv_id_extracted` present
- retrieval width: OpenAlex `top5`
- selector: `best-accepted`

Do **not** expand promotion to:

- non-arXiv `url_canonical_only`
- other title-lane subreasons
- a global `top1 -> top5` default flip
- `top5` without `best-accepted`

## Recommended enable path

If you want to operationalize this promotion, the recommended sequence is:

1. keep the current broad default unchanged
2. bind this arXiv-gated profile logic into the default runtime layer as a narrow exception
3. monitor the next recent slice for:
   - `matched_source_record_count`
   - `normalized_only_fallback_proposal_count`
   - review/conflict burden
   - candidate-local latency on the gated subgroup
4. do **not** widen beyond this subgroup unless new replay evidence appears

## Minimal enable recommendation

The final enable recommendation is:

> **Enable the narrow arXiv-gated `url_canonical_only -> top5 + best-accepted` exception, but do not enable broad `top5` as the default residual path.**

## Bottom line

The correct Phase 2B outcome is now:

- **broad `top5 + best-accepted`**: rejected as the default residual upgrade
- **narrow arXiv-gated exception**: promoted as the evidence-supported retained patch
