# Phase 2B next coding task + large experiment runbook (2026-05-02)

## Objective
Prepare the **next minimal code task** and the **next durable large-scale experiment** after the current Phase 2B state.

## Current state
### Known
- Broad residual `top1 -> top5 + best-accepted` was rejected at large scale for efficiency reasons.
- Narrow arXiv-gated residual top5 exception was promotion-approved in docs:
  - `docs/23-phase2B-narrow-activation-arxiv-gate-decision-memo-2026-05-01.md`
  - `docs/24-phase2B-narrow-activation-arxiv-gate-promotion-memo-2026-05-01.md`
- But builtin defaults are still pointing at the older post-openalex-skip-crossref profile:
  - `src/mygooglealertpapers/config.py`
  - `src/mygooglealertpapers/benchmark_baseline.py`
- The non-arXiv residual cleanup route now has a stronger candidate:
  - profile: `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml`
  - decision memo: `docs/24-phase2B-targeted-nonarxiv-reject71-review08-decision-memo-2026-05-01.md`
- That route already has four-slice stable replay artifacts, but **does not yet have a dedicated first-class runner script**.

### Inferred
The most efficient order is:
1. **First** flip the already-approved arXiv-gated patch into runtime defaults.
2. **Then** make the non-arXiv reject71/review08 route reproducible as one durable large-scale replay entrypoint.

---

## Next coding task (recommended)
## Task
Promote the already-approved **arXiv-gated residual top5 exception** into actual runtime defaults.

## Why this first
- It is already decision-approved.
- It is a small code delta.
- It reduces the gap between docs state and runtime state.
- It avoids mixing two different changes in the same first patch.

## Files to edit
1. `src/mygooglealertpapers/config.py`
2. `src/mygooglealertpapers/benchmark_baseline.py`
3. tests that assert default/runtime profile behavior:
   - likely `tests/test_openalex_topk_activation_gate.py`
   - likely `tests/test_enrich_cache_semantics.py`
   - any config/default-profile assertions
4. docs sync:
   - `docs/README.md`
   - `docs/13-project-phase-map-and-current-status-2026-04-22.md`

## Intended code change
### builtin default
Change builtin runtime default from:
- `...post_openalex_skip_crossref_url_only...`

to:
- `...post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate...`

### baseline helper default
Change:
- `src/mygooglealertpapers/benchmark_baseline.py::DEFAULT_POLICY_PROFILE`

to:
- `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate.yaml`

## Minimum verification
```bash
cd /home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers
PYTHONPATH=src python3 -m pytest \
  tests/test_openalex_topk_activation_gate.py \
  tests/test_enrich_cache_semantics.py \
  tests/test_post_openalex_residual_audit.py -q
```

If any config/default tests exist, include them too.

---

## Next large-scale experiment (recommended)
## Task
Create a **dedicated runner** for the non-arXiv cleanup candidate:
- `targeted_nonarxiv_reject71_review08`

This runner should reproduce the existing 4-slice stable replay in one command, with state/log/output management.

## Why this is the right large experiment
- This is the real remaining residual route after the arXiv-gated patch.
- Existing evidence is strong, but the workflow is still fragmented/manual.
- A single runner makes future threshold micro-iterations reproducible.
- It keeps the experiment merge-only and deterministic by reusing donor source records.

## Deliverable
Add a new runner script, e.g.:
- `scripts/run_day12_targeted_nonarxiv_reject71_review08_large_20260502.py`

## Runner design
For each slice:
- source DB = fixed candidate set DB
- donor DB = current control replay DB whose `source_record` state is reused
- stages = `merge dedup` only
- then export residual audit CSV
- write JSON state file + append log

## Slices / donors / outputs
### 1) large_fixed
- source: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- donor: `data/benchmark/day11_final_promotion_gate_large_fixed_control_20260501.db`
- output: `data/benchmark/day12_large_fixed_targeted_nonarxiv_reject71_review08_20260502.db`
- report: `docs/validation/day12-large-fixed-targeted-nonarxiv-reject71-review08-20260502.json`
- audit: `docs/validation/day12-large-fixed-targeted-nonarxiv-reject71-review08-audit-20260502.csv`

### 2) fresh30
- source: `data/mgap_fresh30_20260410.db`
- donor: `data/benchmark/day11_final_promotion_gate_fresh30_control_20260501.db`
- output: `data/benchmark/day12_fresh30_targeted_nonarxiv_reject71_review08_20260502.db`
- report: `docs/validation/day12-fresh30-targeted-nonarxiv-reject71-review08-20260502.json`
- audit: `docs/validation/day12-fresh30-targeted-nonarxiv-reject71-review08-audit-20260502.csv`

### 3) pkg3_guardrail100
- source: `data/mgap_pkg3_guardrail_100.db`
- donor: `data/benchmark/day11_final_promotion_gate_pkg3_guardrail100_control_20260501.db`
- output: `data/benchmark/day12_pkg3_guardrail100_targeted_nonarxiv_reject71_review08_20260502.db`
- report: `docs/validation/day12-pkg3-guardrail100-targeted-nonarxiv-reject71-review08-20260502.json`
- audit: `docs/validation/day12-pkg3-guardrail100-targeted-nonarxiv-reject71-review08-audit-20260502.csv`

### 4) issac100
- source: `data/mgap_issac_100.db`
- donor: `data/benchmark/day11_final_promotion_gate_issac100_control_20260501.db`
- output: `data/benchmark/day12_issac100_targeted_nonarxiv_reject71_review08_20260502.db`
- report: `docs/validation/day12-issac100-targeted-nonarxiv-reject71-review08-20260502.json`
- audit: `docs/validation/day12-issac100-targeted-nonarxiv-reject71-review08-audit-20260502.csv`

## Profile to use
`config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml`

## Core command shape per slice
```bash
PYTHONPATH=src python3 scripts/replay_validation.py \
  --source-db <source_db> \
  --output-db <output_db> \
  --reuse-source-records-from <donor_db> \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml \
  --report-out <report_json> \
  --limit 1000000 \
  --stages merge dedup \
  --stage-timeout-seconds 10800

PYTHONPATH=src python3 scripts/export_post_openalex_residual_audit.py \
  --source-db <source_db> \
  --results-db <output_db> \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml \
  --out-csv <audit_csv> \
  --slice-name <slice_name>
```

## Minimum verification for the runner patch
```bash
cd /home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers
PYTHONPATH=src python3 -m pytest \
  tests/test_policy_and_merge_fallback.py \
  tests/test_post_openalex_residual_audit.py -q
```

---

## Go / no-go criteria
### For coding task completion
- builtin default points to arXiv-gated profile
- baseline helper default points to arXiv-gated profile
- targeted tests pass
- docs explicitly say default has now been flipped

### For large experiment readiness
- dedicated runner exists
- runner writes state JSON + log
- runner reuses donor source records and skips enrich
- runner exports per-slice audit CSVs
- outputs match the already-known shape within expected deterministic replay tolerance

---

## Recommendation
If doing this in one work session, use this order:
1. patch default flip for arXiv gate
2. run focused tests
3. add dedicated reject71/review08 large-runner
4. run focused tests again
5. launch the 4-slice stable replay only after the runner is in place

This keeps the approved patch separate from the still-experimental non-arXiv cleanup route, while making the next residual experiment reproducible instead of ad hoc.
