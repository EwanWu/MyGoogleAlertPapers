# Open Questions

## Operational questions
1. Will v1 target one mailbox/folder first, or multiple mailboxes?
2. How should the first ~100 emails be sampled?
3. Is a lightweight review workflow needed in v1 (CSV/Markdown/CLI), or is raw export enough?
4. Should alert types be recorded explicitly from the beginning?
5. How much venue metric enrichment should be included in v1 versus deferred?

## Technical questions
1. Which IMAP provider/mailbox is the first target?
2. What auth method will be used for IMAP access?
3. Which provider APIs are guaranteed available from the environment?
4. What should be the preferred schema migration mechanism?
5. Should raw RFC822 be retained for sampled messages only, or all test messages?

## Resolved / clarified after early validation
- The `issac` mailbox is the main test mailbox for current validation work.
- A fresh 30-email real-mailbox run confirmed that enrichment, not parsing/normalization/dedup scaffolding, is the dominant runtime bottleneck.
- The next cycle should prioritize reliability of enrichment rather than adding scope.

## Immediate implementation questions for the next cycle
1. What schema shape should be used for provider-level enrichment progress tracking?
2. Should cached `no_match` and cached `error` results be treated as reusable states by default, or only under explicit retry policy?
3. What retry/backoff policy should apply to provider rows in `error` state?
4. What conflict grades should block promotion into confident `canonical_paper` records?
5. Should provider-level completion be considered sufficient for batch success even when some providers return `no_match`?

## Decision rule
Resolve only what blocks implementation now; defer non-blocking refinements until after the first 10-30 email smoke test. The early smoke-test stage has now been passed; current blocking questions are enrichment resumability, cache authority, and conservative merge judgment.

## Resolved after Package A and Package B (2026-04-16)

The following questions are no longer the main open blockers:

- replay policy comparison is no longer hypothetical; the project now has a working same-batch replay substrate
- policy profile execution is no longer metadata-only; it now drives real replay behavior
- normalized-only fallback has already crossed the threshold from idea to evidence-backed default baseline direction
- broad low-similarity fallback guardrail should **not** be treated as the default path; larger-slice evidence supports staying on `conditional_sources_v2`
- larger-slice controlled replay is now operationally feasible after orchestration hardening

## Current truly open questions (2026-04-16)

1. What is the minimal safe rule shape for a **very narrow anti-garbage patch** on top of `conditional_sources_v2`?
2. Which monetary/accounting fields can be populated from the current runtime directly, and which require new instrumentation?
3. Should the long-run replay standard remain fixed-seed rerun-based, or is true resume-in-place worth the added complexity?
4. What explicit gate should be met before widening provider scope or introducing a new experimental source into the main comparison loop?

## Working rule for the next cycle

Close one decision on a fixed seed at a time.
Prefer narrowing uncertainty over widening scope.
