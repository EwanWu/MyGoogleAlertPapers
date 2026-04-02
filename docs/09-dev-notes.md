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

## Recommended next coding step
Implement the minimal skeleton described in `07-implementation-roadmap.md`.
