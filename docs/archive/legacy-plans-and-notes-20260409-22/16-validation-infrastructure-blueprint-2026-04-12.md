# Validation Infrastructure Blueprint (2026-04-12)

## Purpose
Fix the next execution direction as a project-readable plan so future code changes and experiments follow a stable validation-first workflow.

This blueprint is intended to become the default execution basis for the next implementation cycle.
Priority order after this document is accepted:
1. Package A: reusable replay validation workflow
2. Package B: rule-based DOI conflict suppression continuation
3. Package C: monetary cost accounting + event-driven execution boundary reduction

---

## Executive decision
The project should treat **same-batch replay validation** as the standard method for evaluating enrichment-policy changes.

Reason:
- it removes live-mailbox drift
- it gives strict apples-to-apples comparison on the same normalized candidate set
- it provides the cleanest base for correctness, resource, and future cost comparisons
- it is the right foundation before broadening more providers or more aggressive policy logic

This means the next engineering work should not start from another ad hoc validation run.
It should start from replay workflow productization.

---

## Current confirmed state

### Already implemented / confirmed
- provider-level enrichment resumability exists through `candidate_enrichment_status`
- query-cache uniqueness exists through `(provider, query_type, query_key)`
- merge-side PubMed DOI suppression is already implemented for a first high-value pattern
- `cost_event` schema already includes token and estimated-cost fields
- `batch_run` already provides a usable run-state ledger

### Still missing / incomplete
- no standard replay command or script exists yet
- replay is documented but still manually assembled
- `estimated_cost_usd` is not truly populated in execution
- tracker still writes zeroed request/token/cost fields
- orchestration still lacks a lightweight completion-boundary mechanism that avoids repeated state polling with assistant context alive

---

# Package A: Reusable replay validation workflow

## Objective
Create a reusable, explicit, scriptable replay workflow that reruns enrichment/merge/dedup on a fixed normalized candidate set and automatically emits a comparison-ready report.

## Why Package A goes first
Package A is the shared validation foundation for:
- new DOI suppression rules
- source-strategy changes
- cost-accounting changes
- orchestration overhead reduction measurement

Without Package A, later improvements remain harder to compare and easier to misinterpret.

## Scope
Package A should deliver:
1. replay entrypoint
2. replay reset contract
3. policy-profile selection
4. automatic result summary
5. comparison-ready output document or JSON artifact

## Recommended deliverables

### A1. Replay driver script
Create a first executable entrypoint, recommended path:
- `scripts/replay_validation.py`

Preferred capabilities:
- accept `--source-db`
- accept `--output-db`
- accept `--policy-profile`
- accept `--limit`
- accept `--stages` (default: enrich, merge, dedup)
- accept `--report-out`
- emit machine-readable summary JSON
- optionally emit Markdown report stub

### A2. Replay DB construction contract
The replay flow should:
1. create replay DB from baseline source DB or copied baseline seed
2. retain the fixed `paper_candidate_normalized` set being replayed
3. clear downstream execution tables before rerun
4. rerun chosen stages under the selected policy profile
5. export metrics and differences

### A3. Minimum reset table set
The replay reset step should clear at least:
- `source_record`
- `candidate_enrichment_status`
- `merged_metadata_proposal`
- `canonical_paper`
- `candidate_paper_link`
- `merge_review_queue`
- `cost_event`
- `batch_run`

This keeps the candidate set stable while fully resetting downstream derivations.

### A4. Policy profile mechanism
Introduce policy profiles so replay compares explicit strategy versions rather than an ambiguous working-tree state.

Recommended location:
- `config/policy_profiles/`

Initial profile examples:
- `baseline_guardrail.yaml`
- `conditional_sources_v1.yaml`
- `conditional_sources_v2.yaml`

At minimum, profiles should be able to control:
- provider ordering / enabled state
- narrow-trigger rules for Europe PMC / arXiv / PubMed
- merge suppression rules
- fallback policy knobs used by replay experiments

### A5. Standard replay report fields
Every replay run should report at least:
- source DB path
- output DB path
- policy profile name
- replay candidate count
- provider intent count
- provider event count
- matched source count
- merged proposal count
- canonical paper count
- blocked review count
- severe DOI conflict count
- total batch duration
- total provider latency
- per-provider event and latency summary
- estimated cost summary if available

### A6. Acceptance criteria for Package A
Package A is considered complete when:
1. the same historical candidate set can be rerun without rescanning mailbox
2. the result is reproducible enough for policy comparison
3. replay requires one standard command rather than manual multi-step DB surgery
4. a report artifact is produced automatically

---

# Package B: DOI conflict suppression continuation

## Objective
Extend the first PubMed DOI suppression success into a cleaner, rule-based signal-suppression framework.

## Principle
Do not broadly weaken PubMed.
Instead, add narrow, evidence-driven suppression rules for recurrent false-conflict patterns.

## Immediate target pattern
Evaluate a new suppression rule when all or most of the following hold:
- PubMed and Europe PMC point to the same biomedical item context (same PMID or strong title agreement)
- PubMed DOI conflicts with stronger non-PubMed DOI evidence or Europe PMC-linked context
- PubMed participated only as fallback/title-led evidence
- PubMed is not supposed to override core DOI in the current field-level merge policy

## Implementation direction
Refactor suppression handling from a single special-case function toward a small rule application layer, for example:
- rule id
- trigger conditions
- suppressed field
- suppression reason
- supporting evidence trace

## Validation rule
No suppression rule should be accepted as default policy until it has passed:
1. same-batch replay validation
2. at least one fresh-slice confirmation run
3. manual inspection of changed blocked/recovered cases

---

# Package C: Cost accounting and orchestration overhead reduction

## C1. Monetary cost accounting

### Objective
Populate `cost_event.estimated_cost_usd` from configurable pricing rules so resource reporting separates:
- wall-clock burden
- provider/API burden
- monetary burden

### Implementation direction

#### Step C1.1: pricing config
Add configurable provider pricing, recommended path:
- `config/provider_pricing.yaml`

Even zero-cost providers should be explicitly represented as zero-cost by policy rather than implicit placeholder behavior.

#### Step C1.2: tracker upgrade
Upgrade `CostTracker.record_stage_cost()` and related call sites so events can record:
- `request_count`
- `tokens_prompt`
- `tokens_completion`
- `tokens_total`
- `estimated_cost_usd`

#### Step C1.3: reporting upgrade
Upgrade cost reporting so summaries include:
- event counts by provider
- total latency by provider
- total estimated USD by provider
- batch total estimated USD

## C2. Event-driven execution boundary reduction

### Objective
Reduce useless assistant-side polling overhead by making long-running batch stages observable through explicit run completion signals.

### Problem being solved
The waste is not mainly inside provider execution.
The waste is in repeated orchestration polling while assistant context remains alive.

### Immediate practical strategy
Reuse existing `batch_run` rather than introducing a heavy event system first.

Recommended deliverables:
- `scripts/latest_batch_status.py`
- `scripts/wait_for_batch_run.py`

Expected behavior:
- a batch stage exposes its `run_id`
- downstream orchestration can wait once on run completion
- next step proceeds only when the batch is finished
- repeated context-carrying polling is replaced by a narrow completion check

### Optional secondary output
If useful, finished runs may also write a lightweight artifact such as:
- `run_state/<run_id>.json`

This is optional and should not block the first implementation.

---

## Recommended implementation order

### Phase 1: foundation
1. build Package A replay entrypoint
2. define reset contract
3. define policy-profile structure
4. auto-export replay summary

### Phase 2: correctness continuation
5. use Package A to test new DOI suppression rule(s)
6. inspect changed blocked/recovered cases
7. decide whether to promote the rule into default policy

### Phase 3: resource and execution control
8. add pricing config and populate `estimated_cost_usd`
9. add `wait_for_batch_run` and `latest_batch_status`
10. rerun replay-based comparison to measure both pipeline-side and orchestration-side resource reduction

---

## Immediate coding priority after this blueprint
The next implementation step should begin with Package A.

Specifically:
1. create the first replay driver script
2. create a replay-progress note / report template
3. run Package-A-first implementation before starting Package B or broad cost work

This priority should hold unless a critical bug blocks Package A execution.

---

## Definition of done for the current planning step
This planning step is complete when:
- the blueprint exists in the repo
- roadmap / dev notes point to it as the next execution basis
- git state has been checked and synchronized before code implementation proceeds
- Package A starts only after that synchronization check is done
