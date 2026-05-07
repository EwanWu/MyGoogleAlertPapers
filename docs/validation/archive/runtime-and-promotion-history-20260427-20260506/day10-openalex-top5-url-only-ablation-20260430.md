# Day10 validation — OpenAlex top5 `url_canonical_only` same-fixture reranking ablation (2026-04-30)

## Objective
Evaluate a narrow one-factor change inside the residual `url_canonical_only` path:

- **control** = OpenAlex title `per_page=5` + **first-result selection**
- **treatment** = OpenAlex title `per_page=5` + **best-accepted reranking**

Crossref fallback behavior remains unchanged. Treatment replays the exact same recorded top5 fixture as control, so the only changed factor is local OpenAlex result selection.

## Inputs
- Fixed slice source DB: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- Fresh-like source DB: `data/mgap_fresh30_20260410.db`
- Control profile: `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_control.yaml`
- Treatment profile: `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only.yaml`
- Fixed control fixture: `data/benchmark/http_fixture_day10_openalex_top5_url_only_control_150_20260430.jsonl`
- Fresh control fixture: `data/benchmark/http_fixture_day10_openalex_top5_url_only_control_fresh30_20260430.jsonl`

## Fixed150 result
- `provider_intent_count`: `680 -> 657`
- `matched_source_record_count`: `534 -> 536`
- `normalized_only_fallback_proposal_count`: `40 -> 38`
- `canonical_paper_count`: `293 -> 293`
- `merge_review_queue_count`: `0 -> 0`
- `severe_doi_conflict_count`: `0 -> 0`
- `post_openalex_suppressed_group_count`: `74 -> 97`
- `post_openalex_unsuppressed_targeted_group_count`: `52 -> 29`
- `dispatch_request_count`: `413 -> 390`
- `title_lane_request_count`: `266 -> 243`
- residual `crossref:url_canonical_only` title requests: `52 -> 29`
- `crossref` events: `293 -> 270`
- `crossref` latency: `510,194 ms -> 433,392 ms`
- total provider latency: `1,004,023 ms -> 838,964 ms`

### Candidate-level semantic diff (fixed150)
- `doi_lost`: `0`
- `doi_gained`: `0`
- `high_to_fallback_confidence_drop`: `0`
- `review_added`: `0`
- `canonical_semantic_changed`: `0`
- `fallback_to_high_confidence`: `2`
  - `cand_2ab2b1a43f16ee1f` — *Diffusion MRI Transformer with a Diffusion Space Rotary Positional Embedding (D-RoPE)*
  - `cand_53f38bf4ec58086c` — *Confidence Matters: Uncertainty Quantification and Precision Assessment of Deep Learning-based CMR Biomarker Estimates Using Scan-rescan Data*
- `crossref_removed_but_openalex_present_same_doi`: `23`

## Fresh30 result
- `provider_intent_count`: `181 -> 177`
- `matched_source_record_count`: `116 -> 117`
- `normalized_only_fallback_proposal_count`: `21 -> 20`
- `canonical_paper_count`: `75 -> 75`
- `merge_review_queue_count`: `0 -> 0`
- `severe_doi_conflict_count`: `0 -> 0`
- `post_openalex_suppressed_group_count`: `15 -> 19`
- `post_openalex_unsuppressed_targeted_group_count`: `12 -> 8`
- `dispatch_request_count`: `112 -> 108`
- `title_lane_request_count`: `73 -> 69`
- residual `crossref:url_canonical_only` title requests: `12 -> 8`
- `crossref` events: `80 -> 76`
- `crossref` latency: `121,782 ms -> 111,112 ms`
- total provider latency: `228,121 ms -> 213,336 ms`

### Candidate-level semantic diff (fresh30)
- `doi_lost`: `0`
- `doi_gained`: `0`
- `high_to_fallback_confidence_drop`: `0`
- `review_added`: `0`
- `canonical_semantic_changed`: `0`
- `fallback_to_high_confidence`: `1`
  - `cand_2ab2b1a43f16ee1f` — *Diffusion MRI Transformer with a Diffusion Space Rotary Positional Embedding (D-RoPE)*
- `crossref_removed_but_openalex_present_same_doi`: `4`

## Interpretation
### Known
- Under the shared top5 fixture, **best-accepted reranking dominates first-result selection** on both slices.
- No semantic regression was observed on either slice.
- Treatment converts part of the residual `openalex_title_unmatched` subgroup into successful OpenAlex matches, which then enables additional post-openalex suppression of redundant `crossref:url_canonical_only` work.
- The gain is modest but real: fewer residual crossref title requests, slightly lower latency, slightly better match/fallback counts, and a small number of confidence upgrades.

### Inferred
- The remaining residual problem is at least partly **ranking/selection failure inside returned OpenAlex results**, not only outright recall failure.
- For some `url_canonical_only` cases, OpenAlex already contains an acceptable later result; first-result selection was simply leaving that value on the table.

### Speculative / caveat
- This experiment strictly proves the value of **reranking within a shared top5 result set**.
- It does **not by itself fully isolate** the separate question of whether `per_page=5` should replace the current runtime default `per_page=1`, because both control and treatment use top5.

## Decision
- **Day10 treatment is validated and locally promotable** as the winner of the top5 same-fixture ablation: if we choose to run top5 for residual `url_canonical_only`, we should also enable `best-accepted` selection.
- For a stricter default-runtime promotion standard, the remaining open question is whether the full `top5 + best-accepted` package should replace the current default `top1` behavior. If that proof is required, run one additional promotion-gate comparison against the current default profile.

## Recommended next step
1. **If operator goal is local day10 decision only**: adopt `openalex_title_pick_best_accepted_subreasons=['url_canonical_only']` wherever `openalex_title_per_page_by_subreason.url_canonical_only=5` is used.
2. **If operator goal is default-runtime promotion**: run a final narrow gate comparing current default (`top1`) vs `top5 + best-accepted` on fixed + fresh-like slices, then promote only if the larger package clears the same semantic bar.
