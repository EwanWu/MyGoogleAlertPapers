# Day13 medium60 ablation: non-arXiv `url_canonical_only` OpenAlex top5 + best-accepted without arXiv gate (2026-05-02)

## Question
After validating deterministic URL-identity DOI recovery, is the next useful runtime patch to relax the existing OpenAlex extra-result gate so that **all** `url_canonical_only` candidates (not just arXiv-gated ones) can use:
- `openalex title per_page = 5`
- `pick_best_accepted = true`

## Profiles

### Current best baseline for this ablation
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml`
- existing medium60 DB:
  - `data/benchmark/day2_baseline_small-fixed_day13-urlid-doi-medium60-20260502-exp.db`

### Treatment profile
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml`
- critical override detail:
  - because policy profiles inherit builtin runtime defaults by dict update, **omitting** `openalex_title_extra_result_require_arxiv_id_subreasons` does **not** clear the builtin gate
  - the treatment must therefore explicitly set:
    - `openalex_title_extra_result_require_arxiv_id_subreasons: []`

### Treatment run artifacts
- DB:
  - `data/benchmark/day2_baseline_small-fixed_day13-urlid-doi-openalex-top5-nongated-medium60-20260502-v2.db`
- JSON:
  - `docs/validation/day2-baseline-small-fixed-day13-urlid-doi-openalex-top5-nongated-medium60-20260502-v2.json`

## Result summary

### Output quality
No semantic delta at headline level:
- `matched_source_record_count`: `87 -> 87`
- `merged_metadata_proposal_count`: `58 -> 58`
- `canonical_paper_count`: `49 -> 49`
- `merge_review_queue_count`: `2 -> 2`
- `severe_doi_conflict_count`: `2 -> 2`

### Request / dispatch shape
The treatment does reduce residual Crossref title traffic:
- `dispatch_request_count`: `73 -> 68` (`-5`)
- `title_lane_request_count`: `51 -> 46` (`-5`)
- `post_openalex_suppressed_group_count`: `15 -> 20` (`+5`)
- `post_openalex_unsuppressed_targeted_group_count`: `11 -> 6` (`-5`)
- `source_record_count`: `107 -> 102` (`-5`)
- `cost_event_count`: `225 -> 220` (`-5`)

### Runtime
No convincing runtime win on this medium60 live slice:
- `total_batch_duration_ms`: `122784 -> 123566` (`+782 ms`)
- `total_provider_latency_ms`: `119068 -> 120492` (`+1424 ms`)

Provider shift:
- Crossref total latency: `62076 -> 45137` ms (`-16939`)
- OpenAlex total latency: `54458 -> 71825` ms (`+17367`)

Interpretation:
- the treatment trades `5` Crossref title requests for `5` more expensive OpenAlex top5 title resolutions
- on this slice, that trade is essentially runtime-neutral to slightly worse

## Candidate-level mechanism
Exactly `5` candidates flipped from:
- baseline: `openalex title unmatched` + `crossref title matched`
- treatment: `openalex title matched` + `crossref title suppressed`

Candidates:
- `cand_1c8d63b26d68bca3`
- `cand_3b632c81aa6b162c`
- `cand_3c2e407353cf4446`
- `cand_4940296152b16081`
- `cand_e6e0961ddf95e426`

Representative examples:

### `cand_e6e0961ddf95e426`
Baseline:
- OpenAlex title returned repository-hosted record and stayed unmatched:
  - venue: `Universität Zürich, ZORA`
  - DOI: `10.5167/uzh-433681`
- Crossref title matched published article:
  - venue: `European Journal of Radiology`
  - DOI: `10.1016/j.ejrad.2026.112801`

Treatment:
- OpenAlex top5 + best-accepted selected the published article directly
- Crossref title request disappeared

### `cand_3c2e407353cf4446`
Baseline:
- OpenAlex title drifted to unrelated result:
  - `Obesity and Cardiovascular Disease: Pathophysiology, Evaluation, and Effect of Weight Loss`
- Crossref title matched the target article:
  - `The Effect of Preoperative Epicardial Adipose Tissue Thickness on Postoperative Morbidity and Mortality in Patients Undergoing Isolated Coronary Artery Bypass Grafting`

Treatment:
- OpenAlex top5 + best-accepted selected the correct article
- Crossref title request was suppressed

## Decision
**Do not promote this nongated OpenAlex top5 url-only relaxation as the next default/runtime patch.**

Why:
1. it is a real mechanism, but only a **request-routing substitution** here
2. it produced **no headline semantic gain** on medium60
3. it produced **no convincing runtime gain** on medium60 live providers
4. the current best evidence still favors keeping this as a narrow optional experiment rather than broadening the default beyond the existing arXiv-gated posture

## Updated inference
After the URL-identity DOI recovery patch, the next layer is **not obviously** “remove the arXiv gate from OpenAlex top5 for all url-only candidates.”

What this ablation really shows is:
- the repository / venue acceptance boundary is real
- OpenAlex top5 can recover several currently Crossref-rescued non-arXiv url-only cases
- but under current live latency tradeoffs, that recovery is mostly **provider substitution**, not net pipeline gain

So if we keep digging, the more promising next question is narrower:
> can we design a **precision-preserving acceptance rule** for repository-hosted / alternate-location exact-title hits that improves semantic outcome or suppresses title-fallback more cheaply than a general non-arXiv top5 expansion?
