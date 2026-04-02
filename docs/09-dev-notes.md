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

## Recommended next coding step
Proceed from candidate extraction into metadata enrichment, using the existing normalization skeleton (title keys, canonical URLs, DOI/PMID/PMCID/arXiv extraction) as the handoff layer.

- Batch-level timing should be tracked explicitly so full-run and per-stage wall-clock durations are reportable, not inferred only from provider latency.

- Query-level caching is now a required optimization target; repeated DOI/title/provider lookups should not refetch identical requests unnecessarily.

- Merge-side normalization should collapse superficial string differences before flagging provider conflicts.
