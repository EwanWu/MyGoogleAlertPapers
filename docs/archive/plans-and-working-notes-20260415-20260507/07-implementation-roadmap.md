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

## Phase status revision (2026-04-16)

This roadmap remains useful as the long-range structure, but several items above have now moved from planned/in progress into a validated baseline state.

### Delivered enough to treat as current baseline
- **Phase 1 / 1.1**: mailbox ingest, extraction, normalization skeleton, raw snapshot persistence, and basic reporting are no longer just skeleton work
- **Phase 2 core**: provider enrichment and `source_record` persistence are implemented, with profile-driven execution behavior rather than placeholder comparison scaffolding
- **Phase 3 core**: conservative deduplication, `canonical_paper`, `candidate_paper_link`, and `merge_review_queue` are in active use
- **Phase 3.7 / Package A**: reusable replay validation workflow has been delivered in working form and has already produced decision-relevant same-batch evidence

### Decision reached after Package B
- the stricter fallback-guardrail exploration has completed its main decision loop
- current broader/default recommendation returns to `conditional_sources_v2`
- `conditional_sources_v4_fallback_guardrail_salvage` remains a narrow experimental/diagnostic profile, not the default path

### Revised current implementation priority
1. test a **very narrow anti-garbage patch** on top of `conditional_sources_v2`
2. improve monetary cost accounting and explicitly document remaining observability gaps
3. preserve documentation discipline: keep long-lived summaries current and archive transitional notes
4. only then consider wider provider/scope expansion

### Execution rule learned from larger-slice runs
For long replay executions, the current standard should include:
- stage timeout support
- enrich progress logging
- periodic checkpoint commits where useful
- fixed-seed replay/resume workflow for controlled comparison
- chained sparse follow-up rather than one-shot completion checks
