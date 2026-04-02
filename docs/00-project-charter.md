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
