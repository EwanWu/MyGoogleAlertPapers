# Package B phase summary and archive guide (2026-04-16)

## Purpose

This document is the durable phase-level summary for Package B. It is meant to replace the need to read a long chain of intermediate notes, handoff docs, temporary failure reports, and local planning artifacts.

If you are arriving fresh, read this file first.

---

## Scope of this phase

Package B focused on one question:

> How should normalized-only fallback behavior be tightened without overpaying in overall recall/canonical yield?

The work split into two coupled tracks:

1. **Policy track**
   - audit normalized-only fallback cases
   - add guardrails
   - test whether a narrow salvage rule can recover safe cases

2. **Execution track**
   - make larger-slice replay robust enough to support a trustworthy `v2` vs `v4` comparison on the same fixed seed

---

## Durable conclusions

### 1. `v3` established the main guardrail direction, but at a recall cost

`conditional_sources_v3_fallback_guardrail` introduced stricter handling for normalized-only fallback.

On the fixed 249-candidate slice, the stable conclusion was:

- `248 merged / 10 review / 195 canonical`

Relative to `v2`, this showed that the guardrail could divert several high-risk cases away from direct canonicalization, but it also reduced canonical yield.

### 2. `v4` provided only a very narrow salvage gain

`conditional_sources_v4_fallback_guardrail_salvage` added a restrained salvage path centered on author-tail pollution cleanup.

On the same 249-candidate slice, it improved only one case:

- `248 merged / 9 review / 196 canonical`

This was real, but small.

### 3. The formal larger-slice replay changed the deployment recommendation

On the formal same-seed larger replay (`368 candidates / 1405 provider intents`):

- `v2`: `293 canonical / 2 review / 368 merged / 777 matched_source_record`
- `v4`: `284 canonical / 10 review / 367 merged / 780 matched_source_record`

This is the decision-driving result.

Interpretation:

- `v4` got slightly more source matches,
- but those gains did not improve the final merge outcome,
- and the broader guardrail increased review burden while lowering canonical yield.

### 4. Therefore the current default should be `v2`, not `v4`

This phase ends with a clear recommendation:

- **Keep `conditional_sources_v2` as the broader/default policy**
- **Keep `conditional_sources_v4_fallback_guardrail_salvage` only as a narrow experiment or diagnostic profile**

### 5. Future iteration should be narrow, not broad

If this line of work continues, the promising direction is:

- start from `v2`
- keep only very narrow anti-garbage logic
- avoid broad low-similarity fallback blocking by default

In practice, the most plausible retained patch class is:

- obvious author-blob / malformed-title rejection

not a generic low-similarity review gate.

---

## What changed in code during this phase

### Policy / merge logic

Primary file:

- `src/mygooglealertpapers/pipeline/merge.py`

Main additions in this phase included:

- normalized-only fallback guardrail logic
- author-blob / author-tail pollution handling
- low source-title similarity review logic
- sparse-metadata low-similarity review logic
- narrow salvage logic for author-tail cleanup under strong conditions

Related policy profiles:

- `config/policy_profiles/conditional_sources_v3_fallback_guardrail.yaml`
- `config/policy_profiles/conditional_sources_v4_fallback_guardrail_salvage.yaml`

### Enrich robustness and orchestration hardening

Primary files:

- `src/mygooglealertpapers/enrich/openalex.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `scripts/replay_validation.py`
- `scripts/run_packageB_large_slice_replay_20260416.sh`
- `scripts/resume_packageB_large_slice_replay_20260416.sh`
- `scripts/summarize_packageB_large_slice_replay_20260416.py`

Durable technical outcomes:

- fixed OpenAlex `primary_location.source = null` parsing bug
- added stage timeout support
- added progress logging during enrich
- added checkpoint commits for long runs
- improved failure reporting so failed runs emit usable artifacts instead of failing silently
- established fixed-seed resume + summary workflow for larger replay comparisons

---

## What was transient and should not drive future decisions

The following categories were useful during execution, but should not dominate future reading:

- temporary handoff notes
- one-off run plans
- mid-run failure snapshots later superseded by successful formal replay
- exploratory overfitting discussions that were later resolved by the larger-slice result
- smoke-run artifacts once formal replay succeeded

These are archived, not deleted, because they still preserve debugging context.

---

## Canonical artifact set for this phase

### Read first

- `docs/11-packageB-decision-memo-2026-04-16.md`
- `docs/12-packageB-phase-summary-and-archive-guide-2026-04-16.md`

### Read when decision detail is needed

- `docs/10-packageB-large-slice150-v2-v4-decision-analysis-2026-04-16.md`

### Canonical validation evidence

- `docs/validation/packageB-large-slice150-summary-20260416_slice150.md`
- `docs/validation/packageB-large-slice150-summary-20260416_slice150.json`
- `docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.md`
- `docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.json`
- `docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.md`
- `docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.json`

### Important code / config anchors

- `src/mygooglealertpapers/pipeline/merge.py`
- `src/mygooglealertpapers/pipeline/enrich.py`
- `src/mygooglealertpapers/enrich/openalex.py`
- `scripts/replay_validation.py`
- `scripts/resume_packageB_large_slice_replay_20260416.sh`
- `scripts/summarize_packageB_large_slice_replay_20260416.py`
- `config/policy_profiles/conditional_sources_v4_fallback_guardrail_salvage.yaml`

---

## Archive structure created in this cleanup

To reduce reading noise while preserving provenance:

- top-level Package B intermediate docs were moved under:
  - `docs/archive/packageB-20260415-16/`
- transient validation artifacts were moved under:
  - `docs/validation/archive/packageB-20260415-16/`

This keeps the current docs layer decision-oriented and keeps the detailed execution trail available when needed.

---

## Documentation maintenance rule going forward

For future project doc cleanup:

### Keep at the active layer

Only keep documents that answer one of these questions quickly:

1. What is the current decision?
2. What is the current implementation state?
3. What evidence is canonical?
4. What should the next agent read first?

### Move to archive

Archive documents when they are mainly:

- handoff notes
- temporary plans
- intermediate checkpoints
- superseded failure reports
- smoke-run summaries
- detailed exploratory branches whose conclusion is already captured elsewhere

### Update long-lived docs instead of spawning endless short-lived docs

Preferred pattern:

- short-lived notes during active execution are acceptable
- once the phase stabilizes, fold them into:
  - one decision memo
  - one phase summary / archive guide
  - a small canonical evidence set

This is the standard to use for future phases.
