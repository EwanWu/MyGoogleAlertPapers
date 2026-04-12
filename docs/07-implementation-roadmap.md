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
- multi-account test mailbox support via existing IMAP skill config
- extractor v2 with Scholar URL unwrapping and snippet-derived venue/year hints
- normalization skeleton for title keys, canonical URLs, and DOI/PMID/PMCID/arXiv extraction

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

## Phase 2 (in progress): enrichment skeleton
Deliverables:
- source_record persistence
- Crossref DOI/title lookup
- PubMed PMID/title lookup
- OpenAlex DOI/title lookup
- enrichment coverage reporting

## Phase 3 (in progress): dedup scaffold
Deliverables:
- canonical_paper scaffold
- candidate_paper_link scaffold
- conservative matching cascade (DOI/PMID/PMCID/title-author-year)
- dedup compression statistics

## Phase 3.5 (in progress): cost/timing instrumentation
Deliverables:
- report-cost command
- stage/provider latency summaries from cost_event
- experiment reflection document

## Phase 3.6 (implemented / first-pass complete): enrichment reliability hardening
Delivered or largely implemented:
- provider-level enrichment status tracking for checkpoint/resume selection
- normalized and deduplicated query-cache keys with stronger reuse guarantees
- safer partial-rerun behavior after interruption or provider failure
- stricter title-fallback handling in the current enrichment policy
- merge conflict grading that distinguishes superficial formatting differences from severe DOI/PMID/content disagreement
- canonicalization guardrails for severe-conflict proposals

## Phase 3.7 (current priority): validation infrastructure productization
Execution basis:
- `docs/16-validation-infrastructure-blueprint-2026-04-12.md`

Deliverables:
1. Package A: reusable replay validation workflow
2. Package B: rule-based DOI conflict suppression continuation
3. Package C: monetary cost accounting plus event-driven execution-boundary reduction

## Immediate implementation priority
Do not widen scope first.
Before additional provider expansion or new broad validation runs:
1. productize same-batch replay as the standard validation workflow
2. use replay to validate the next DOI suppression rule set
3. populate real monetary cost reporting
4. reduce orchestration-side polling overhead through batch-run completion gating
