# Development Notes

## Working assumptions
- Python is the preferred implementation language for v1.
- SQLite is sufficient for v1 storage.
- Testing uses read-only IMAP access and peek semantics.
- Scholar email parsing should be rule/template based first.
- LLM usage is fallback-only.
- Preferred interpreter target is Python 3.11, but the current machine may not expose a `python3.11` executable on PATH; bootstrap and local checks should use the available `python3` unless/until a stricter interpreter path is confirmed.

## Initial external resources to borrow from conceptually
- IMAP read-only / BODY.PEEK workflows
- Python email parsing ecosystem
- Crossref, OpenAlex, Semantic Scholar, PubMed, Europe PMC APIs
- Zotero duplicate detection heuristics
- ASySD and BibDedupe dedup ideas

## Guardrails
- Never allow test runs to silently mutate unread state.
- Preserve raw source snapshots before aggressive normalization.
- Keep source-specific metadata separate from merged proposals.
- Prefer conservative non-merge over speculative auto-merge.
- Always log enough to estimate scale-up cost.
- Reuse existing local credential stores when practical instead of duplicating email secrets across multiple project files.
- For substantial validation runs, produce a structured results document in the repo.
- Keep documents updated, but do not artificially suppress useful in-chat discussion during execution.
- Planning, design, exploratory discussion, and execution updates should still be discussed fully with the user when helpful.

## Current execution basis
For the next implementation cycle, follow:
- `docs/16-validation-infrastructure-blueprint-2026-04-12.md`

This blueprint is now the default basis for code and experiment sequencing.
Priority order:
1. Package A: reusable replay validation workflow
2. Package B: rule-based DOI conflict suppression continuation
3. Package C: monetary cost accounting + event-driven execution-boundary reduction

## Recommended next coding step
Start with Package A rather than another ad hoc validation run.

Immediate tasks:
- create the first replay driver script
- define replay reset contract for downstream tables
- define policy-profile loading structure
- emit machine-readable replay summaries and a report artifact

Additional notes:
- Batch-level timing should continue to be tracked explicitly so full-run and per-stage wall-clock durations are reportable, not inferred only from provider latency.
- Query-level caching and provider-level resumability are already in place; the next leverage point is turning replay into the standard comparison harness.
- Merge-side DOI suppression changes should only be promoted after replay-based validation.
- Monetary cost reporting and batch-run completion gating should follow after Package A establishes the shared validation base.
