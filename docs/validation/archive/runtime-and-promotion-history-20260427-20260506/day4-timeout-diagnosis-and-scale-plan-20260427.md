# Day 4 timeout diagnosis, cron status, and scale-out plan (2026-04-27)

## 1. Cron status for the current dialogue

### Operational conclusion
- **Yes, current-session first-class cron is working again for this dialogue.**
- Evidence:
  - first-class `cron` tool calls succeeded in-session
  - cron monitor job `ae57c590-2a68-4a97-b53f-338fc178f089` was created and fired correctly
  - the wake resumed the same owner session and produced the monitoring result without polling loops

### Remaining root issue
- The underlying issue is **not fully fixed at the session-metadata layer**.
- `~/.openclaw/agents/deepblue/sessions/sessions.json` still shows the current `agent:deepblue:main` session tool snapshot **without `cron`**.
- Therefore the practical state is:
  - **runtime capability:** working now
  - **persisted session tool snapshot:** still stale / inconsistent

### Stable monitoring judgement
- **For the current live dialogue: yes, stable cron-based status monitoring is now operational.**
- **As a general durable guarantee across future compactions / fresh resumptions: not fully guaranteed until the stale session tool snapshot issue is fixed or bypassed with a preflight.**

### Immediate workflow rule
Before every long task:
1. verify current runtime can actually call first-class `cron`
2. schedule `cron(sessionTarget=current, delivery.mode=none)` before starting the task
3. if runtime cannot call `cron`, stop and refresh owner session instead of falling back to CLI cron or polling

## 2. What caused the timeout

## Direct failure
- enrich stage timed out after 1799s:
  - `python3 -m mygooglealertpapers.cli enrich-candidates --limit 368`

## What the preserved metrics show
- candidate set: `368`
- planned provider intents: `1405`
- dispatch groups after dedup/batching: `1149`
- processed runnable intents before timeout: `800 / 1405` (`56.9%`)
- elapsed batch duration: `1779809 ms`
- total provider latency: `1768445 ms`

### Key interpretation
`total_provider_latency_ms / total_batch_duration_ms ≈ 0.994`, which strongly suggests the current enrich execution is **near-serial**, not meaningfully concurrent.

At the observed throughput:
- processed rate: about `0.45 intents/s`
- projected full-run time: about `3126 s` (`52.1 min`)

So even if provider behavior stayed stable, this full live slice would still project well beyond the current `1800 s` timeout.

## Provider bottlenecks from this run
- `semanticscholar`: `186 events`, `845734 ms`, avg `4547 ms/event`
- `crossref`: `187 events`, `406405 ms`, avg `2173 ms/event`
- `pubmed`: `80 events`, `178273 ms`, avg `2228 ms/event`
- `openalex`: `265 events`, `200930 ms`, avg `758 ms/event`

### Main diagnosis
- **OpenAlex DOI batching is not the primary bottleneck.**
- The main bottleneck is the **serial live fanout across high-latency providers**, especially Semantic Scholar, then Crossref / PubMed-class calls.

## 3. What we learned about OpenAlex batching
- `openalex_batch_request_count = 3`
- This matches the earlier enrichment-plan expectation for the slice150 seed:
  - `127 unique DOI -> 3 batch requests`

### Conclusion
OpenAlex DOI batching is already reaching the expected batch shape. The next scale problem is broader throughput architecture, not “OpenAlex failed to batch”.

## 4. Timeout report wording fix
The timeout report has now been corrected to distinguish:
- `processed_runnable_intents`
- `request_savings_vs_processed_intents`
- `request_savings_vs_total_planned_intents`

For this timeout run:
- `dispatch_request_count = 538`
- `processed_runnable_intents = 800 / 1405`
- `request_savings_vs_processed_intents = 262`
- `request_savings_vs_total_planned_intents = 867`

This avoids misreading timeout snapshots as if they were final full-run savings.

## 5. External evidence for scale-out strategy

### OpenAlex
Official docs indicate:
- API keys are free with daily free usage
- list+filter usage is metered / quota-governed
- **bulk snapshot access is free**

Implication: OpenAlex is suitable for a **hybrid model**:
- live API for deltas / targeted lookups
- bulk/snapshot-backed local serving for scale

### Crossref
Official REST API guidance recommends for very large pulls:
- consider the annual public data file / local database route instead of high-volume REST
- cache results
- split large queries into smaller slices
- avoid repeated duplicate calls

Implication: Crossref should not remain a purely serial live per-candidate dependency at scale.

### Semantic Scholar
Official API page states:
- unauthenticated access may be throttled during heavy use
- API-key access starts at **1 RPS**
- datasets are available as free/open resources

Implication: Semantic Scholar is especially risky as a synchronous primary enrichment dependency for large live runs. It is a strong candidate for:
- async fallback lane
- selective unresolved-case use only
- or local dataset/index-backed enrichment

## 6. Scale-out solution for larger production promotion

### A. Split correctness from throughput
Do not treat one monolithic live enrich pass as the only path to correctness.

Recommended structure:
1. **fast identifier lane**
   - DOI / PMID / arXiv id
   - OpenAlex DOI batch first
   - cheap deterministic providers first
2. **medium-confidence title lane**
   - Crossref / OpenAlex title lookup
3. **slow fallback lane**
   - Semantic Scholar and other long-tail providers only for unresolved cases

### B. Move to local-first / hybrid provider architecture
For large-scale promotion:
- OpenAlex: local snapshot + live delta API
- Crossref: local dump / cached mirror + selective live fallback
- Semantic Scholar: dataset or async fallback, not synchronous default for every candidate

### C. Add provider-specific concurrency and budgets
Current enrich path is effectively serial.
For scale, introduce:
- per-provider concurrency limits
- explicit rate budgeters
- backoff / retry policies
- circuit breakers for slow providers
- max-time budget per provider lane

### D. Make long runs resumable by design
Already improved:
- in-flight dispatch metrics now persist during enrich

Still needed:
- resumable provider-lane checkpoints
- stage continuation without replaying the entire live fanout
- timeout-safe partial completion semantics

### E. Promote by evidence, not by one big live run
For semantic safety:
- keep deterministic replay / fixture checks for merge-dedup correctness

For throughput safety:
- use live narrower profiling runs to isolate bottlenecks before promoting broader changes

## 7. Next narrower throughput-localization experiment

## Goal
Identify which live providers are preventing a realistic full-scale enrich SLA, without conflating that question with merge/dedup semantics.

## Proposed experiment
Use the same fixed seed source DB, but run **enrich-only** on a narrower candidate window with provider-ablation profiles.

### Recommended slice
- `limit = 120`
- same source DB: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`

Reason:
- keeps real mixed DOI/title structure
- likely finishes well inside the current timeout budget
- still large enough to expose provider-latency ranking and batching behavior

### Profiles to compare
1. **baseline-current**
   - current default profile
2. **no-semanticscholar**
   - disable Semantic Scholar only
3. **no-crossref**
   - disable Crossref only
4. **identifier-fastpath**
   - keep identifier-driven providers and OpenAlex DOI batch
   - disable most title-search fanout

### Metrics to compare
- `processed_runnable_intents`
- `total_batch_duration_ms`
- `total_provider_latency_ms`
- `dispatch_request_count`
- `request_savings_vs_processed_intents`
- provider latency totals and per-event averages
- `matched_source_record_count` (throughput-side signal only)

### Decision rule
- If removing Semantic Scholar collapses runtime while preserving enough matched-source coverage, demote it to fallback / async lane.
- If Crossref is the next dominant cost after Semantic Scholar removal, consider local cache/snapshot strategy before more API-centric tuning.
- If identifier-fastpath finishes quickly, treat it as the scalable core lane and push title-heavy lookups into a second-stage backlog.

## 8. Recommended immediate next step
1. keep the corrected timeout report format
2. run the narrower provider-ablation enrich-only experiment (`limit=120`)
3. use those results to decide whether the next engineering move is:
   - provider demotion/reordering
   - provider concurrency
   - or local snapshot / cache-first architecture
