# MyGoogleAlertPapers

A local-first pipeline for ingesting Google Scholar alert emails, extracting paper candidates, enriching metadata, conservatively deduplicating records, and building a structured paper store for downstream analysis.

## Status

Planning / pre-implementation.

## Initial goals

- Read Google Scholar alert emails safely in read-only mode
- Do not change unread state during testing
- Extract paper candidates from alert emails
- Enrich metadata via external scholarly APIs
- Deduplicate conservatively
- Track token / API / time consumption for cost estimation
- Validate on ~100 emails before scaling toward ~8000 emails

## Repo structure

See `docs/` for planning, architecture, validation protocol, and implementation notes.
