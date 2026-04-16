# Architecture Overview

## Objective
Create a reproducible pipeline from Google Scholar alert email to canonical paper record with conservative matching and explicit provenance.

## Pipeline modules

### M1. Mailbox scan
- Connect via IMAP in read-only mode
- Fetch headers and bodies with peek semantics
- Record mailbox, UID, message-id, dates, subject, sender

### M2. Mail parsing
- Parse MIME structure
- Extract HTML/text body
- Detect Google Scholar alert template
- Extract paper candidate blocks

### M3. Normalization
- Clean title
- Normalize authors
- Extract DOI / PMID / PMCID / arXiv ID / URLs
- Build title keys and lookup keys

### M4. Metadata enrichment
Cascade queries across:
- PubMed
- Europe PMC
- Crossref
- Semantic Scholar
- OpenAlex

### M5. Deduplication / version linking
- Exact identifier matching
- Conservative title-author-year matching
- Version linking for preprint / conference / journal
- Uncertain cases remain in candidate/provisional layer

### M6. Cost accounting
- Log API calls, token usage, latency, retries, and per-stage processing costs

### M7. Evaluation
- Assess parsing accuracy
- Assess metadata accuracy
- Assess deduplication precision/recall on sampled data
- Estimate scale-up cost for ~8000 emails

### M8. Storage/export
- SQLite as v1 primary store
- CSV/JSONL export for review and downstream analysis

## Design principles
- Local-first
- Read-only test safety
- Provenance-preserving
- Conservative merging
- LLM fallback only for ambiguity

## Architecture state alignment update (2026-04-16)

The high-level architecture above remains valid, but the project has now moved from architectural intent into a working multi-stage system.

### Modules now proven in real replay/validation use
- mailbox -> parse -> normalize -> enrich -> merge -> dedup is no longer only conceptual; it has been exercised on real mailbox slices
- replay validation is now a first-class operational layer rather than an ad hoc script pattern
- profile-driven execution now affects real enrich/merge behavior in controlled comparisons
- merge review queue and conservative canonicalization guardrails are active parts of the pipeline, not future design placeholders

### Architecture-level conclusion after Package A and Package B
- the current broader/default policy baseline should be understood as `conditional_sources_v2`
- normalized-only fallback is part of the current baseline architecture
- broad fallback guardrail tightening, as tested in full `v4`, should not be treated as part of the default architecture
- orchestration hardening for long replays is now part of the practical architecture, including timeout/progress/checkpoint support around larger validations

### Where to read current architecture-in-use
For current system behavior, pair this overview with:

1. `docs/35-project-phase-map-and-current-status-2026-04-16.md`
2. `docs/21-packageA-implementation-and-replay-results-2026-04-15.md`
3. `docs/34-packageB-phase-summary-and-archive-guide-2026-04-16.md`
