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
