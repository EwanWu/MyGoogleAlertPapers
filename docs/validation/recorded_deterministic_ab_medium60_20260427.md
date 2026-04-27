# Recorded deterministic A/B confirmation (medium60, 2026-04-27)

## Objective
Do one stronger confirmation for `title_payload_reuse_enabled` using a larger deterministic sample (`limit=60`), and check not only aggregate counts but also table-level and candidate-level semantic equivalence.

## Inputs
- Source DB: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- Baseline profile: `config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`
- Experiment profile: `data/benchmark/title_payload_reuse_experiment_profile_20260427.yaml`
- Recorded fixture: `data/benchmark/http_fixture_medium60_20260427.jsonl`

## Runs
1. `recorded_baseline_live_medium60_20260427`
   - live provider calls + fixture record
2. `recorded_baseline_replay_medium60_20260427`
   - baseline replay against the recorded fixture
3. `recorded_experiment_replay_medium60_20260427`
   - experiment replay against the same recorded fixture

Validation JSON / run reports (archived support artifacts):
- `docs/validation/archive/day3-runtime-optimization-20260427/recorded_baseline_live_medium60_20260427.json`
- `docs/validation/archive/day3-runtime-optimization-20260427/recorded_baseline_replay_medium60_20260427.json`
- `docs/validation/archive/day3-runtime-optimization-20260427/recorded_experiment_replay_medium60_20260427.json`

## Aggregate result
Across all three runs, the core output counts are identical:

- `provider_intent_count = 248`
- `source_record_count = 248`
- `matched_source_record_count = 137`
- `merged_metadata_proposal_count = 60`
- `normalized_only_fallback_proposal_count = 7`
- `canonical_paper_count = 51`
- `merge_review_queue_count = 2`
- `severe_doi_conflict_count = 2`

Dispatch summary:
- baseline replay: `dispatch_request_count = 201`, `request_savings_vs_runnable_intents = 47`
- experiment replay: `dispatch_request_count = 201`, `request_savings_vs_runnable_intents = 47`
- experiment-only reuse stats:
  - `shared_title_reuse_group_count = 12`
  - `shared_title_reuse_intent_count = 24`
  - `shared_title_reuse_request_count = 12`
  - `shared_title_reuse_request_savings = 12`

## Table-level confirmation
### Baseline live vs baseline replay
Direct equality holds for:
- `candidate_enrichment_status`
- `source_record`
- `merged_metadata_proposal`
- `merge_review_queue`

`canonical_paper` and `candidate_paper_link` differ only in generated `paper_id` values. After normalizing away regenerated IDs and comparing semantic content, they are identical.

### Baseline replay vs experiment replay
Direct equality holds for:
- `source_record`
- `merged_metadata_proposal`
- `merge_review_queue`

`candidate_enrichment_status` differs only by instrumentation notes:
- experiment adds `notes = "shared_title_reuse"`
- no status / query / error / cache semantics changed

`canonical_paper` and `candidate_paper_link` again differ only in regenerated `paper_id` values. After semantic normalization, they are identical.

## Candidate-level confirmation
Across all candidates in the run:
- semantic changed candidates: `0`

That check compared, per candidate:
- matched source records
- merged proposal content
- review-queue entries
- assigned canonical paper semantics (via join to `canonical_title_key`, not raw `paper_id`)

## Where reuse actually happened
The experiment reused title payloads only for four duplicated title cases, across three providers (`crossref`, `openalex`, `semanticscholar`):

1. `Cerebrovascular Reactivity Assessment with Breath-Hold Functional MRI in Patients with Moyamoya Angiopathy: Which Time Period to Analyze?`
2. `Preliminary results of 3D MRI-DSA fusion for navigation planning in endovascular recanalization of chronic intracranial artery occlusion`
3. `Relevance of the Diffusion Tensor Imaging along the Perivascular Space (DTI-ALPS) Index in Small Vessel Disease-A Study in Patients with Mild Ischaemic Stroke`
4. `Serial vessel wall imaging reveals rupture site and treatment response in a flow-related aneurysm associated with an arteriovenous malformation: illustrative case`

Interpretation:
- 4 duplicate title pairs × 3 providers = 12 reuse groups
- 24 candidate-provider intents participated
- 12 provider fetches were avoided inside those groups

## What is known
- Under a larger deterministic sample (`limit=60`), baseline and experiment produce the same semantic enrich / merge / dedup outputs.
- No candidate-level semantic regression was observed.
- The experiment’s observable differences are instrumentation-only (`shared_title_reuse` notes) plus the expected reuse counters.

## What is inferred
- The previously observed live jitter is still best explained by provider-side response/order variability, not by the reuse optimization itself.
- For the currently enabled scope (`crossref` / `openalex` / `semanticscholar` title reuse with per-candidate accept/match preserved), the optimization is semantically stable on this sample.

## Remaining caveat
- Raw `paper_id` values are not a stable semantic comparison key; they are regenerated across replays. Future diff tooling should compare canonical content or candidate→canonical semantic links, not raw paper IDs.

## Recommendation
Recommend promoting `title_payload_reuse_enabled` to default behavior for the current narrow scope, because:
- deterministic `medium40` already passed
- deterministic `medium60` now also passes
- candidate-level semantic diff is zero
- the optimization remains bounded to shared title fetch reuse while preserving per-candidate match/accept logic
