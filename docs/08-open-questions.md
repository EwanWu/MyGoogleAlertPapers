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

## Decision rule
Resolve only what blocks implementation now; defer non-blocking refinements until after the first 10-30 email smoke test.
