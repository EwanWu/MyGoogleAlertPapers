# Implementation Roadmap

## Phase 1: minimal working skeleton
Deliverables:
- repo scaffold
- IMAP read-only connector
- Google Scholar alert detection
- raw snapshot storage
- candidate extraction
- SQLite schema bootstrap
- structured logging

### Phase 1.1: safe small-sample smoke-test readiness
Deliverables:
- `.env.example` for local setup
- raw snapshot persistence to `data/raw_mail_snapshots/`
- lightweight batch report command
- improved candidate extraction beyond bare anchor fallback
- candidate count write-back into mail_ingestion_record
- basic self-checks/tests for detector and extractor

## Phase 2: normalization and enrichment
Deliverables:
- title/author normalization
- identifier extraction
- provider clients
- source_record persistence
- merged metadata proposal layer

## Phase 3: conservative deduplication
Deliverables:
- exact match layer
- near-match layer
- version-link layer
- uncertain bucket handling

## Phase 4: formal validation on ~100 emails
Deliverables:
- evaluation scripts
- error case exports
- batch reports
- scale-up estimate for ~8000 emails

## Phase 5: optional LLM fallback
Only after empirical need is demonstrated.
Potential use cases:
- parser fallback for malformed templates
- metadata conflict disambiguation
- complex version matching

## Guiding rule
Move from safety and observability first, then toward smarter automation.
