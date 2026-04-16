# Validation Protocol

## Goal
Validate safety, extraction quality, metadata quality, deduplication behavior, and cost observability before scaling.

## Validation phases

### Phase A: 10-30 emails
Purpose:
- Smoke test IMAP read-only workflow
- Identify parser/template issues
- Validate schema and logging

### Phase B: ~100 emails
Purpose:
- Measure extraction performance
- Evaluate enrichment hit rates
- Evaluate conservative deduplication behavior
- Estimate cost for ~8000 emails

## Test dimensions

### T1. Read/unread safety
Check unread status before and after scan for sampled UIDs.
Success criterion:
- no unread state changes during test

### T2. Google Scholar alert identification
Human-label a sample:
- alert / not alert
Measure:
- precision
- recall
- false positives
- false negatives

### T3. Candidate extraction quality
Human-check per mail:
- number of paper candidates extracted
- correctness of title
- correctness of links
- correctness of author/source line extraction

### T4. Metadata enrichment quality
For sampled candidates, review:
- DOI
- PMID
- title
- abstract
- venue
- year
Compare source agreement and note conflicts.

### T5. Deduplication quality
Create a small gold set of:
- true duplicate / same conceptual paper
- same work but different versions
- near-match but should not merge
Measure:
- false merge rate
- missed merge rate
- uncertain bucket rate

### T6. Cost accounting quality
Measure:
- average per-email time
- average per-candidate API count
- average LLM usage if any
- provider hit rate and retry rate
- variance and long-tail cases

## Output artifacts
- evaluation summary report
- sampled error cases
- ambiguous cases list
- scale-up estimate for ~8000 emails

## Validation protocol state update (2026-04-16)

The protocol above is still the right high-level structure, but the project has now completed enough real replay work to sharpen what counts as the canonical validation path.

### What has now been validated in practice
- same-batch replay is the standard comparison substrate for policy evaluation
- Package A established that `normalized_only_fallback` on top of the baseline path produces a meaningful canonical-yield gain on a fixed 249-candidate slice without increasing severe conflict burden
- Package B established that stricter fallback guardrails must be judged on larger fixed seeds, not just small local slices
- the formal larger-slice `v2` vs `v4` comparison now functions as the main decision-grade validation result for Package B

### Current validation rule
When comparing policy variants:

1. use the same fixed normalized seed
2. prefer replay-based comparison over separate live runs
3. keep a small canonical evidence set rather than many equally-ranked intermediate notes
4. treat smoke runs and transient failure notes as operational support artifacts, not final validation evidence

### Current canonical validation evidence for active reading
- `docs/validation/packageA-baseline-guardrail-replay-100-2026-04-15.md`
- `docs/validation/packageA-conditional-sources-v2-replay-100-2026-04-15.md`
- `docs/validation/packageB-large-slice150-summary-20260416_slice150.md`
- `docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.md`
- `docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.md`

### Operational lesson from larger-slice validation
Long validation runs should now assume the need for:
- stage timeout support
- progress logging during enrich
- periodic checkpointing where helpful
- explicit follow-up/monitoring logic rather than assuming completion will surface automatically
