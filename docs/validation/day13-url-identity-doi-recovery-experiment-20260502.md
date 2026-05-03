# Day13 deterministic URL-identity DOI recovery experiment (2026-05-02)

## Goal
Validate whether a **narrow deterministic URL-identity DOI recovery lane** is a real next-layer runtime optimization target for the current Phase 2B default workflow, instead of broad fetch-based DOI scraping or another round of transport/payload tuning.

## What was implemented

### Code path
- `src/mygooglealertpapers/normalize/identifiers.py`
  - added `recover_doi_from_url_identity(...)`
  - current rules:
    1. `recursive_url_decode`
    2. `nature_article_slug`
- `src/mygooglealertpapers/pipeline/enrich.py`
  - `_build_provider_intents(...)` now optionally upgrades `url_canonical` candidates from title-path to DOI-path when:
    - `doi_extracted is null`
    - `arxiv_id_extracted is null`
    - runtime flag `url_identity_doi_recovery_enabled: true`
- experimental profile:
  - `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml`

### Test coverage
Passed targeted regression suite including new tests for:
- recursive URL decode DOI recovery
- Nature article slug DOI recovery
- promotion from title query to DOI query inside `enrich_candidates(...)`

## Deterministic recovery coverage on the validated slice150 source DB
Source DB:
- `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`

### Recoverable cases found by the implemented rules
Total recoverable (`doi_extracted is null`, `arxiv_id_extracted is null`, deterministic URL rule succeeds): `10`

Recovered candidates:
- `cand_ef45f083c154b55c` → `nature_article_slug` → `10.1038/s41598-026-42032-x`
- `cand_721f728d8e406dd5` → `nature_article_slug` → `10.1038/s44161-026-00785-8`
- `cand_8c0fcffbabdce4e6` → `recursive_url_decode` → `10.14366/usg.23232`
- `cand_671ed1ecf3aa215c` → `nature_article_slug` → `10.1038/s43856-026-01413-z`
- `cand_99e05fb4078181d5` → `nature_article_slug` → `10.1038/s43856-026-01413-z`
- `cand_caed51f7383710a2` → `nature_article_slug` → `10.1038/s41598-026-43624-3`
- `cand_6712f73abd8e5a01` → `nature_article_slug` → `10.1038/s41598-026-43624-3`
- `cand_210c27dfc78ab052` → `nature_article_slug` → `10.1038/s41598-026-43624-3`
- `cand_983e32088eed4586` → `nature_article_slug` → `10.1038/s41598-026-38473-z`
- `cand_aafaa7c0485410af` → `nature_article_slug` → `10.1038/s44303-026-00156-9`

Within the current medium60 replay slice, recoverable cases = `3`:
- `cand_ef45f083c154b55c`
- `cand_721f728d8e406dd5`
- `cand_8c0fcffbabdce4e6`

## Experiment design

### Baseline
- DB: `data/benchmark/day2_baseline_small-fixed_day13-apikey-mailto-only-medium60-20260502.db`
- policy profile: builtin current default

### Treatment
- DB: `data/benchmark/day2_baseline_small-fixed_day13-urlid-doi-medium60-20260502-exp.db`
- policy profile:
  - `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml`
- command actually used for the valid treatment run:
  - `python3 scripts/replay_validation.py --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db --output-db data/benchmark/day2_baseline_small-fixed_day13-urlid-doi-medium60-20260502-exp.db --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08_url_identity_doi_recovery.yaml --report-out docs/validation/day2-baseline-small-fixed-day13-urlid-doi-medium60-20260502-exp.json --limit 60 --stages enrich merge dedup`

## Baseline vs treatment

### Runtime / dispatch
- `planned_provider_intents`: `248 -> 242` (`-6`)
- `dispatch_request_count`: `75 -> 73` (`-2`)
- `title_lane_group_count`: `72 -> 66` (`-6`)
- `title_lane_request_count`: `56 -> 51` (`-5`)
- `post_openalex_unsuppressed_targeted_group_count`: `13 -> 11` (`-2`)
- `identifier_fastpath lane groups`: `34 -> 40` (`+6`)
- `title_core lane groups`: `72 -> 66` (`-6`)

### End-to-end replay runtime
- `total_batch_duration_ms`: `177538 -> 122784` (`-54754 ms`, about `-30.8%`)
- `total_provider_latency_ms`: `174873 -> 119068` (`-55805 ms`, about `-31.9%`)

### Provider latency shift
- Crossref total latency: `63779 -> 62076` ms (small improvement)
- OpenAlex total latency: `108389 -> 54458` ms (large improvement)

Interpretation:
- the main speedup came from moving a few candidates out of OpenAlex title search and into DOI / DOI-batch paths
- the gain is not primarily from fewer total requests; it is mostly from **cheaper identifier-path requests replacing slower title-path requests**

### Output quality
- `matched_source_record_count`: `83 -> 87` (`+4`)
- `merged_metadata_proposal_count`: `57 -> 58` (`+1`)
- `canonical_paper_count`: `48 -> 49` (`+1`)
- `merge_review_queue_count`: unchanged at `2`
- `normalized_only_fallback_proposal_count`: unchanged at `4`
- `severe_doi_conflict_count`: unchanged at `2`

## Candidate-level evidence

### 1. `cand_8c0fcffbabdce4e6` — real semantic rescue
Baseline:
- Crossref: `title` query, unmatched, stale/wrong DOI signal `10.14366/usg.25200`
- OpenAlex: `title` query, unmatched

Treatment:
- Crossref: `doi` query `10.14366/usg.23232`, matched
- OpenAlex: `doi_batch` query `10.14366/usg.23232`, matched
- outcome: candidate becomes newly canonicalized in treatment

This is the strongest proof that deterministic URL identity recovery is not just a runtime trick; it can also repair a real residual miss.

### 2. `cand_ef45f083c154b55c` — removes a wrong OpenAlex title path
Baseline:
- Crossref title already matched to `10.1038/s41598-026-42032-x`
- OpenAlex title path returned a wrong DOI: `10.7326/0003-4819-55-1-33`

Treatment:
- Crossref DOI query matched correctly
- OpenAlex DOI-batch query matched correctly to `10.1038/s41598-026-42032-x`

Interpretation:
- this is a clean example where URL identity recovery improves both runtime path and provider correctness.

### 3. `cand_721f728d8e406dd5` — title-path to identifier-path conversion
Baseline:
- OpenAlex used title query
Treatment:
- OpenAlex switched to `doi_batch` on `10.1038/s44161-026-00785-8`
- Crossref gained a DOI query record for the same candidate

Interpretation:
- this case contributes to runtime reduction even when baseline was already semantically acceptable.

## Decision

### Keep or rollback?
**Keep as an experimental patch worth promoting to the next validation round.**

Reason:
- narrow deterministic rule set
- measurable runtime improvement on medium60
- positive semantic effect (`matched_source_record +4`, `canonical_paper +1`)
- no observed new review burden
- no observed severe DOI-conflict increase

### What this result means strategically
This confirms the earlier hypothesis, but with a refinement:

> the valuable next layer is not generic URL-origin DOI scraping; it is a **deterministic URL identity recovery micro-lane**.

In other words:
- **worth doing**: deterministic decode / deterministic publisher slug mapping
- **not first choice**: broad fetch-based page scraping
- **not first choice**: PII lane
- **not first choice**: venue-veto relaxation as the next main optimization

## Recommended next step
Promote this narrow patch into a larger fixed-slice validation run next, still keeping the rule surface intentionally small:
1. keep current `recursive_url_decode`
2. keep current `nature_article_slug`
3. do **not** add generic fetch logic yet
4. only consider another publisher-specific rule when the mapping is equally deterministic and easy to audit
