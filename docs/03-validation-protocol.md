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
