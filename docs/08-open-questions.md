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
