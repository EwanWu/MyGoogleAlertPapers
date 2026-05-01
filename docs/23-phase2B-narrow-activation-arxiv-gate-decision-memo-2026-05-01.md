# Phase 2B narrow activation memo — `url_canonical_only` top5 gated to arXiv-native residuals (2026-05-01)

## Objective

Design a **narrower activation rule** so that the residual `url_canonical_only` OpenAlex title path does **not** expand from `top1` to `top5 + best-accepted` globally, but still captures the small subgroup where the larger day11 matrix showed real return.

## Proposed rule

Keep the current default residual path unchanged for almost all cases:

- default residual path: **`top1`**

Only activate the larger OpenAlex package when all of the following are true:

1. title-lane subreason = **`url_canonical_only`**
2. the candidate also has **`arxiv_id_extracted`** (equivalently, an arXiv-native URL / preprint signal)

Then use:

- **`top5 + best-accepted`**

Profile implemented at:

- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate.yaml`

Runtime gate implemented at:

- `src/mygooglealertpapers/pipeline/enrich.py`

## Why this subgroup

Using the completed large day11 matrix (`956 candidates`, 4 slices), the broader treatment had only **4** candidate-level final-confidence promotions (`merge_confidence: 0.15 -> 0.9`).

All **4/4** of those promotions were inside the same narrow subgroup:

- `url_canonical_only`
- `arxiv_id_extracted` present
- arXiv-native URL / preprint-like venue guess

Outside that subgroup, the broader `top5 + best-accepted` treatment produced:

- **0** additional final-confidence promotions
- **0** reductions in `normalized_only` fallback

So the broad treatment’s *real* quality gains were fully concentrated in the arXiv-native residual slice.

## Validation basis

This memo uses the already completed day11 matrix artifacts:

Control reports / DBs:
- `docs/validation/day11-final-promotion-gate-large-fixed-control-20260501.json`
- `docs/validation/day11-final-promotion-gate-fresh30-control-20260501.json`
- `docs/validation/day11-final-promotion-gate-pkg3-guardrail100-control-20260501.json`
- `docs/validation/day11-final-promotion-gate-issac100-control-20260501.json`
- corresponding DBs under `data/benchmark/day11_final_promotion_gate_*_control_20260501.db`

Broad top5 treatment reports / DBs:
- `docs/validation/day11-final-promotion-gate-large-fixed-treatment-20260501.json`
- `docs/validation/day11-final-promotion-gate-fresh30-treatment-20260501.json`
- `docs/validation/day11-final-promotion-gate-pkg3-guardrail100-treatment-20260501.json`
- `docs/validation/day11-final-promotion-gate-issac100-treatment-20260501.json`
- corresponding DBs under `data/benchmark/day11_final_promotion_gate_*_treatment_20260501.db`

I also implemented a fresh replay script:

- `scripts/run_day11_narrow_activation_arxiv_gate_20260501.py`

but aborted the live rerun after it entered very slow OpenAlex waits and stopped being a sensible use of time/resources. The recommendation below is therefore based on **retrospective exact subgroup validation over the completed large matrix**, not on a fresh full live rerun.

## Gated population size

Across the full matrix, the proposed rule would activate on only:

- `26 / 956 = 2.72%` of candidates

Per slice:

- `large_fixed`: `9 / 368`
- `fresh30`: `6 / 95`
- `pkg3_guardrail100`: `8 / 249`
- `issac100`: `3 / 244`

## Candidate-level gains preserved by the narrow gate

The 4 observed final-confidence promotions were:

- `cand_7a1dd15089495cf9`
  - `Progressive Learning with Anatomical Priors for Reliable Left Atrial Scar Segmentation from Late Gadolinium Enhancement MRI`
- `cand_40874060f658736c`
  - `DINOv3 with Test-Time Calibration for Automated Carotid Intima-Media Thickness Measurement on CUBS v1`
- `cand_cd1c124046a3d47d`
  - `FedAgain: A Trust-Based and Robust Federated Learning Strategy for an Automated Kidney Stone Identification in Ureteroscopy`
- `cand_f23cfc83ef0d4011`
  - `Structure and Progress Aware Diffusion for Medical Image Segmentation`

These were exactly the candidates that moved from `normalized_only` fallback to a matched-provider-backed proposal under the broader treatment.

## Simulated matrix outcome for the narrow gate

Because all real quality gains were entirely inside the gated subgroup, the narrow gate preserves the broad treatment’s useful output-side gains while avoiding broad activation elsewhere.

### Output-side metrics

Predicted narrow-gate aggregate versus control:

- `matched_source_record_count`: `1322 -> 1326` (`+4`)
- `normalized_only_fallback_proposal_count`: `141 -> 137` (`-4`)
- `canonical_paper_count`: `783 -> 783` (`no change`)
- `merge_review_queue_count`: `7 -> 7` (`no change`)
- `severe_doi_conflict_count`: `7 -> 7` (`no change`)

So, on semantic / safety gates, the narrow rule preserves the same observed win as the broad rule.

### Runtime / cost proxy

Important nuance: this arXiv gate is **not** a request-saving optimization in the same way the broad rule was.

Observed matrix-wide control vs broad treatment:

- `dispatch_request_count`: `1111 -> 1050` (`-61`)
- `total_provider_latency_ms`: `1774269 -> 1896442` (`+122173 ms`, `+6.89%`)
- `total_batch_duration_ms`: `1800998 -> 1927028` (`+126030 ms`, `+7.00%`)

For the proposed arXiv-only gate, the candidate-local latency delta extracted from the completed matrix is only about:

- `+7730 ms` total provider-latency proxy across all `956` candidates
- approximately **`+0.44%`** versus control

And because the gated subgroup did **not** drive the broad treatment’s crossref-suppression savings, the narrow rule is best understood as:

- a **tiny-overhead quality patch**
- **not** a global throughput optimization

## Interpretation

This is the first narrower rule that actually looks defensible.

What it does well:

- keeps activation tiny (`2.72%`)
- preserves all observed final-confidence gains from the broad treatment
- keeps semantic safety unchanged
- reduces the runtime penalty from roughly `+122 s` to about `+7.7 s` on the full matrix proxy

What it does **not** do:

- it does **not** reproduce the broad treatment’s request-count savings
- it does **not** justify a broader claim that `url_canonical_only` should generally move to `top5`
- it mostly behaves like an **arXiv-native preprint rescue / stabilization patch**, not a general OpenAlex recall fix

## Recommendation

### Recommended decision

**Promote this narrow arXiv-gated rule if the goal is a low-overhead quality patch.**

Concretely:

- keep the global default residual path at **`top1`**
- add a narrow exception for **`url_canonical_only + arxiv_id_extracted`**
- only there use **`top5 + best-accepted`**

### Not recommended

Do **not** reinterpret this as evidence for a broader promotion of `top5` on non-arXiv `url_canonical_only` traffic.

That broader default still failed the large-scale runtime/value gate.

## Minimal conclusion

- **Broad `top5 + best-accepted`**: still **not** promotable as the default residual path
- **Narrow arXiv-only gate**: **promotable** as a small quality-focused exception
