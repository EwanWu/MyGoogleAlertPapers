# Mainline convergence plan (2026-04-22)

## Purpose

This document fixes the current mainline convergence plan after Track A and Track B micro-experiments.

It is not an exploratory memo. It is the working plan for closing the current policy branch and validating a single integrated mainline candidate.

## Current stable conclusions

### 1. Bibliographic default stays on `conditional_sources_v2`
Broader fallback-tightening variants have already failed the default-promotion test.

### 2. Track A narrow late-fallback filter is the only remaining correctness-side patch worth promoting
The `author_blob_fallback_only` rule is promising because it is placed at the final `normalized_only` fallback acceptance step rather than at live matching time.

### 3. Track B is decision-closed
Unpaywall should not be used to replace bibliographic providers. Its production role is post-dedup OA enhancement.

## Mainline candidate to validate

The integrated mainline candidate for the next validation round is:

- bibliographic policy: `conditional_sources_v2`
- fallback garbage filter: `conditional_sources_v2_author_blob_fallback_only`
- OA enhancement: post-dedup `enrich-paper-oa`

In shorthand:

> `v2 + late-fallback filter + post-dedup OA`

## Execution plan

### Step 1. Archive the plan and freeze the target
- write this document
- use it as the active handoff reference for the next work block

### Step 2. Promote Track A narrow patch into the mainline candidate set
- review the late-fallback-only author-blob code path
- confirm tests and replay infrastructure support the intended causal interpretation
- prepare a focused Track A commit instead of mixing it with other pending work

### Step 3. Run a formal integrated validation
Control:
- `conditional_sources_v2`

Treatment:
- `conditional_sources_v2_author_blob_fallback_only`
- then post-dedup `enrich-paper-oa`

Validation must report three groups of outcomes:
1. correctness: canonical / review / severe DOI conflict
2. resource usage: provider latency, OA enrichment latency, paid-LLM usage if any
3. incremental value: blocked garbage case and OA URL coverage gain

### Step 4. If stable, update the effective production flow
Target flow:
1. `normalize-candidates`
2. `enrich-candidates`
3. `merge-metadata`
4. `dedup-candidates`
5. `enrich-paper-oa`

## What not to prioritize now
- no new broad anti-garbage heuristics
- no new Unpaywall placement experiments
- no fresh mailbox-selection work unless the next experiment explicitly needs a new mail slice

## Expected deliverables from this work block
- one focused Track A commit
- one integrated validation summary
- one updated statement of current mainline candidate status
