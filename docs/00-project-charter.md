# Project Charter

## Project name
MyGoogleAlertPapers

## Purpose
Build a low-/non-LLM, local-first ingestion pipeline that converts Google Scholar alert emails into a structured paper database suitable for management, enrichment, deduplication, and later research analysis.

## Primary user goal
Use Google Scholar alert emails as a high-trust entry point for discovering and organizing papers, while preserving safety, cost visibility, and reproducibility.

## Hard constraints
1. Google Scholar alert emails are the primary ingestion source for v1.
2. The testing phase must not alter unread/read state.
3. Validation should begin with about 100 emails before large-scale processing.
4. Token usage, API quota usage, and time cost must be logged.
5. Deduplication must be conservative.
6. LLM usage should be minimized and used only as fallback.
7. The main object is the paper, not the email.

## Non-goals for v1
- No full GUI.
- No full-text/PDF ingestion as a main workflow.
- No aggressive automated merge policy.
- No dependence on Scholar web scraping as the primary source.

## Desired v1 outputs
- A local structured store of paper records
- Traceable source snapshots and provenance
- Validation reports from a 100-email test set
- Cost estimates for scaling to ~8000 emails

## Current charter-aligned status update (2026-04-16)

The project has now moved beyond a planning-only charter stage.
Current reality is:

- an end-to-end mailbox -> candidate -> normalize -> enrich -> merge -> dedup pipeline exists and has been validated on real mailbox slices
- Package A established replay validation as a reusable comparison substrate and provided evidence supporting `conditional_sources_v2` as the current default baseline direction
- Package B tested stricter fallback guardrails and reached a stable deployment conclusion: the broader/default recommendation should remain `conditional_sources_v2`, while `conditional_sources_v4_fallback_guardrail_salvage` should remain experimental only
- the project remains aligned with its original low-/non-LLM, local-first intent; the formal larger-slice Package B replay exercised no paid LLM path

## Current near-term priorities under this charter (2026-04-16)

1. iterate only on a **very narrow** anti-garbage patch on top of `conditional_sources_v2`
2. keep validation evidence canonical and documentation layered into active vs archive views
3. continue improving cost/accounting observability and long-run orchestration robustness without widening scope first
