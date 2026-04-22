# Resource consumption and billing summary for conditional-source experiments (2026-04-10)

## Scope
This report redoes the previous resource summary using a stricter framework that includes:
- technical-resource consumption
- economic / billing-oriented consumption
- explicit observability gaps for missing economic metrics

Included experiment groups:
1. Historical 100-mail baseline
2. Live 100-mail conditional-source run
3. Same-batch 249-candidate replay run
4. Fresh-30 integration comparison where helpful for source-level marginal cost interpretation

## Data sources
### Reports consulted
- `docs/validation/conditional-source-integration-2026-04-10.md`
- `docs/validation/package3-conditional-sources-100-validation-2026-04-10.md`
- `docs/validation/package3-conditional-sources-replay-249-2026-04-10.md`

### Databases inspected
- `data/mgap_pkg3_guardrail_100.db`
- `data/mgap_pkg3_guardrail_100_conditional_20260410.db`
- `data/mgap_pkg3_guardrail_100_replay_conditional_20260410.db`

### Tables inspected for cost/billing observability
- `batch_run`
- `source_record`
- `candidate_enrichment_status`
- `query_cache`
- `cost_event`

---

# 1. Technical resource metrics

## 1.1 Historical 100-mail baseline
### Workload size
- scanned mails: `100`
- detected Scholar mails: `64`
- normalized candidates: `249`
- source records: `996`
- query cache rows: `828`
- cost events: `1861`

### Batch / stage durations
- scan: `92396 ms`
- extract_candidates: `200 ms`
- normalize_candidates: `14 ms`
- enrich_candidates: `2219856 ms`
- merge_metadata: `212 ms`
- dedup_candidates: `13 ms`

### Provider/API activity
- crossref: `249` calls, `199` matched, avg `2007.6 ms`, total `499883 ms`
- openalex: `249` calls, `167` matched, avg `2966.4 ms`, total `738623 ms`
- pubmed: `249` calls, `104` matched, avg `2642.1 ms`, total `657886 ms`
- semanticscholar: `249` calls, `33` matched, avg `1224.7 ms`, total `304946 ms`

### Technical proxy total
- provider total latency proxy: `2201338 ms`

## 1.2 Live 100-mail conditional-source run
## Comparability note
This run is not strictly same-input comparable to the historical baseline because live mailbox contents changed.

### Workload size
- scanned mails: `100`
- detected Scholar mails: `50`
- normalized candidates: `100`
- source records: `382`
- query cache rows: `351`
- cost events: `819`

### Batch / stage durations
- scan: `67604 ms`
- extract_candidates: `137 ms`
- normalize_candidates: `7 ms`
- enrich_candidates: `650876 ms`
- merge_metadata: `41 ms`
- dedup_candidates: `4 ms`

### Provider/API activity
- arxiv: `2` calls, `2` matched, avg `1732.5 ms`, total `3465 ms`
- crossref: `100` calls, `85` matched, avg `2232.2 ms`, total `223216 ms`
- europepmc: `40` calls, `10` matched, avg `2230.1 ms`, total `89202 ms`
- openalex: `100` calls, `75` matched, avg `1163.4 ms`, total `116340 ms`
- pubmed: `40` calls, `24` matched, avg `2673.9 ms`, total `106954 ms`
- semanticscholar: `100` calls, `21` matched, avg `1087.0 ms`, total `108697 ms`

### Technical proxy total
- provider total latency proxy: `647874 ms`

## 1.3 Same-batch 249-candidate replay run
This is the most reliable resource comparison because it reuses the same normalized candidate set.

### Workload size
- normalized candidates: `249`
- source records: `951`
- query cache rows: `795`
- cost events: `1411`
- merged proposals: `211`
- canonical papers: `170`

### Batch / stage durations
- enrich_candidates: `1514821 ms`
- merge_metadata: `200 ms`
- dedup_candidates: `11 ms`

### Provider/API activity
- arxiv: `8` calls, `8` matched, avg `1918.4 ms`, total `15347 ms`
- crossref: `249` calls, `197` matched, avg `2144.3 ms`, total `533939 ms`
- europepmc: `98` calls, `28` matched, avg `1915.4 ms`, total `187708 ms`
- openalex: `249` calls, `173` matched, avg `1132.2 ms`, total `281912 ms`
- pubmed: `98` calls, `60` matched, avg `2371.6 ms`, total `232416 ms`
- semanticscholar: `249` calls, `18` matched, avg `1030.9 ms`, total `256693 ms`

### Technical proxy total
- provider total latency proxy: `1508015 ms`

## 1.4 Fresh-30 marginal-cost signal
This run is useful mainly for source-policy marginal analysis.

### Europe PMC narrowing effect
- planned intents: `379 -> 351`
- europepmc calls: `64 -> 36`
- merged proposals: `74 -> 74`

### Interpretation
Narrowing Europe PMC reduced provider work while preserving output, which strongly supports its fallback/bridge-only role.

---

# 2. Economic / billing-oriented metrics

## 2.1 Model call counts
### Checked
- `cost_event` in all inspected databases

### Result
- no model-specific provider entries exist
- no separate LLM/model invocation counters were found in these experiment databases

### Status
- **Unavailable in current experiment DBs**

## 2.2 Tool call counts
### Checked
- `cost_event.stage`
- `batch_run`
- pipeline reports

### Observable tool-like counts available
These are pipeline-stage event counts, not OpenClaw chat-tool counts:

#### Historical baseline `cost_event` counts
- scan: `100`
- extract_candidates: `64`
- normalize_candidates: `249`
- enrich_candidates / crossref: `249`
- enrich_candidates / openalex: `249`
- enrich_candidates / pubmed: `249`
- enrich_candidates / semanticscholar: `249`
- merge_metadata: `249`
- dedup_candidates: `203`

#### Live 100 conditional run `cost_event` counts
- scan: `100`
- extract_candidates: `50`
- normalize_candidates: `100`
- enrich_candidates / arxiv: `2`
- enrich_candidates / crossref: `100`
- enrich_candidates / europepmc: `40`
- enrich_candidates / openalex: `100`
- enrich_candidates / pubmed: `40`
- enrich_candidates / semanticscholar: `100`
- merge_metadata: `100`
- dedup_candidates: `87`

#### Replay 249 conditional run `cost_event` counts
- enrich_candidates / arxiv: `8`
- enrich_candidates / crossref: `249`
- enrich_candidates / europepmc: `98`
- enrich_candidates / openalex: `249`
- enrich_candidates / pubmed: `98`
- enrich_candidates / semanticscholar: `249`
- merge_metadata: `249`
- dedup_candidates: `211`

### Important caveat
These are **pipeline internal event counts**, not the number of OpenClaw chat tools or external LLM tool invocations used by me as the assistant in chat.

### Status
- **Partially available, but only as pipeline event counts**

## 2.3 Token breakdown
### Checked
- `cost_event.tokens_prompt`
- `cost_event.tokens_completion`
- `cost_event.tokens_total`

### Result
Across all inspected experiment databases:
- prompt tokens: all `0`
- completion tokens: all `0`
- total tokens: all `0`

### Status
- **Schema exists but values are unpopulated**

## 2.4 Estimated monetary cost
### Checked
- `cost_event.estimated_cost_usd`

### Result
Across all inspected experiment databases:
- `estimated_cost_usd` exists
- all values are `0.0`

### Status
- **Schema exists but monetary estimation is not implemented/populated**

## 2.5 Bill-like proxy currently available
Since direct billing is missing, the only consistent economic-adjacent proxy currently available is:
- provider call count
- provider total latency
- total event count

### Proxy totals
#### Historical baseline
- cost events: `1861`
- provider latency proxy total: `2201338 ms`

#### Live 100 conditional
- cost events: `819`
- provider latency proxy total: `647874 ms`

#### Replay 249 conditional
- cost events: `1411`
- provider latency proxy total: `1508015 ms`

### Caution
These are **not real billing totals**. They are only workload/burden proxies.

---

# 3. Assistant-side model / tool / token economics for the reporting work

## Scope of this section
This section covers the assistant-side OpenClaw session activity used to:
- create the `resource-cost-reporting` skill
- redo the billing-aware report
- inspect local session files to recover missing economic records

It does **not** cover the entire long experiment day perfectly end-to-end.
Instead, it covers the directly relevant reporting-repair window visible in the current session log.

## Session source
- session key: `agent:main:service-7x24`
- session file: `/home/ewan/.openclaw/agents/main/sessions/a17a18ec-1c51-4fdd-9ca8-f4990bd898b2.jsonl`
- model/provider from session metadata: `openai-codex / gpt-5.4`
- extraction tool: `~/.openclaw/workspace/skills/resource-cost-reporting/scripts/extract_openclaw_session_cost.py`

## Current session-level totals at inspection time
From `sessions.json` / `session_status` during inspection:
- model: `gpt-5.4`
- provider: `openai-codex`
- session input tokens: `18239`
- session output tokens: `5620`
- session total tokens: `82664`
- cache hit summary: `80% hit`, `71k cached`, `0 new`

## Reporting-repair window extracted from JSONL
Time window extracted for this correction pass:
- `2026-04-10T15:31:00Z` to `2026-04-10T15:39:30Z`

### Assistant model-call count
- assistant messages with usage records in this window: `14`
- all recorded on model `gpt-5.4`
- provider: `openai-codex`

### Assistant tool-call count
Tool calls observed in this reporting-repair window:
- `exec`: `8`
- `update_plan`: `3`
- `write`: `2`
- `read`: `1`
- `session_status`: `1`

Note: some assistant messages contain more than one tool call, so total tool calls exceed tool-using message count.

### Assistant token breakdown in reporting-repair window
Aggregated from assistant message `usage` records in JSONL:
- input tokens: `26931`
- output tokens: `7437`
- cache read tokens: `1102720`
- cache write tokens: `0`
- aggregate total tokens: `1137088`
- cost input: `0.067328`
- cost output: `0.111555`
- cost cache read: `0.275680`
- cost cache write: `0.000000`
- aggregate model-side estimated cost: `0.454563`

### Reproducible extraction command
```bash
python3 ~/.openclaw/workspace/skills/resource-cost-reporting/scripts/extract_openclaw_session_cost.py \
  ~/.openclaw/agents/main/sessions/a17a18ec-1c51-4fdd-9ca8-f4990bd898b2.jsonl \
  --start 2026-04-10T15:31:00Z \
  --end 2026-04-10T15:39:30Z \
  --pretty
```

### Interpretation of assistant-side economics
- The reporting/correction pass itself used the higher-capability model `gpt-5.4`, not `gpt-5.4-mini`.
- Cache-read volume dominated token accounting during this window.
- The largest single output-heavy assistant step was writing the redone report body.
- The tool mix was dominated by local inspection and file-writing work (`exec`, `write`).

## Boundary note
These assistant-side figures describe the reporting work in the OpenClaw session.
They are separate from the project pipeline database metrics, which describe the MGAP pipeline itself.
The two cost surfaces should not be merged blindly.

# 4. Observability gaps

## Missing or insufficiently observable economic metrics
### 3.1 Model invocation counts
- Not available in current experiment DBs
- No per-model run counter found

### 3.2 Real token usage
- token fields exist in `cost_event`
- all stored values are zero
- therefore instrumentation is present in schema but not populated in practice

### 3.3 Real monetary spend
- `estimated_cost_usd` exists in schema
- all stored values are zero
- therefore cost estimation is not implemented or not wired into these runs

### 3.4 OpenClaw-side tool usage for this chat session
- Not stored in the pipeline DBs
- This report therefore cannot truthfully summarize assistant chat-tool usage from project DB alone

## Consequence
The current system supports strong reporting for:
- runtime burden
- provider burden
- relative workload change

But it does **not yet support** high-quality reporting for:
- true billing
- token economics
- model-economics attribution
- assistant tool-economics attribution

---

# 5. Observability gaps

## Missing or insufficiently observable economic metrics
### 5.1 Model invocation counts inside the MGAP pipeline
- Not available in current experiment DBs
- No per-model run counter found inside pipeline records

### 5.2 Real token usage inside the MGAP pipeline
- token fields exist in `cost_event`
- all stored values are zero
- therefore instrumentation is present in schema but not populated in practice

### 5.3 Real monetary spend inside the MGAP pipeline
- `estimated_cost_usd` exists in schema
- all stored values are zero
- therefore cost estimation is not implemented or not wired into these runs

### 5.4 Assistant-side tool economics outside the extracted reporting window
- Now partially observable from OpenClaw session JSONL
- but not yet normalized into a reusable per-task accounting export
- therefore end-to-end assistant cost for the entire day is still only partially reconstructed

## Consequence
The current system now supports stronger reporting for:
- runtime burden
- provider burden
- session-level assistant model/tool/token usage for inspected windows
- relative workload change

But it still does **not yet support** complete high-quality reporting for:
- true pipeline billing
- pipeline token economics
- fully normalized per-task assistant cost attribution across long sessions

# 6. Key bottlenecks

## Historical baseline bottlenecks
1. OpenAlex total latency: `738623 ms`
2. PubMed total latency: `657886 ms`
3. Crossref total latency: `499883 ms`

## Replay conditional bottlenecks
1. Crossref total latency: `533939 ms`
2. OpenAlex total latency: `281912 ms`
3. Semantic Scholar total latency: `256693 ms`
4. PubMed total latency: `232416 ms`
5. Europe PMC total latency: `187708 ms`

## Resource shift interpretation
After the conditional-source redesign:
- PubMed ceased being a dominant cost center
- Europe PMC entered the cost stack, but in a bounded way
- Crossref and OpenAlex remained core workhorses
- arXiv added almost negligible burden relative to its gains

---

# 7. Key bottlenecks

## Historical baseline bottlenecks
1. OpenAlex total latency: `738623 ms`
2. PubMed total latency: `657886 ms`
3. Crossref total latency: `499883 ms`

## Replay conditional bottlenecks
1. Crossref total latency: `533939 ms`
2. OpenAlex total latency: `281912 ms`
3. Semantic Scholar total latency: `256693 ms`
4. PubMed total latency: `232416 ms`
5. Europe PMC total latency: `187708 ms`

## Assistant-side reporting bottlenecks in the correction window
1. Cache-read dominated token accounting: `1102720`
2. `exec` dominated tool activity: `8` calls
3. High-output write/reporting turns were the largest direct model-output contributors

## Resource shift interpretation
After the conditional-source redesign:
- PubMed ceased being a dominant pipeline cost center
- Europe PMC entered the pipeline cost stack, but in a bounded way
- Crossref and OpenAlex remained core workhorses
- arXiv added almost negligible burden relative to its gains
- for assistant-side repair/reporting work, the main economic burden came from model context/cache usage rather than external project APIs

# 8. Interpretation

## Known
- The same-batch replay is the most reliable comparison.
- On the same 249 candidates, provider-latency proxy total dropped from `2201338 ms` to `1508015 ms`, about `-31.5%`.
- On the same 249 candidates, enrich wall time dropped from `2219856 ms` to `1514821 ms`, about `-31.7%`.
- arXiv remained low-volume and high-yield.
- Europe PMC added useful metadata but also non-trivial cost.
- PubMed fallback demotion produced the clearest reduction in provider burden.

## Inferred
- The narrowed conditional-source design is a net win in technical resource consumption.
- From an economic-reporting perspective, the project is still immature because token/cost fields are present but effectively empty.
- Any statement about “billing savings” would currently be overstated unless phrased as proxy-only.

## Missing / unobservable
- true model call counts
- true token consumption
- true assistant tool call counts for this reporting task
- true USD-equivalent spend for pipeline operations

---

# 8. Interpretation

## Known
- The same-batch replay is the most reliable comparison for pipeline resources.
- On the same 249 candidates, provider-latency proxy total dropped from `2201338 ms` to `1508015 ms`, about `-31.5%`.
- On the same 249 candidates, enrich wall time dropped from `2219856 ms` to `1514821 ms`, about `-31.7%`.
- arXiv remained low-volume and high-yield.
- Europe PMC added useful metadata but also non-trivial cost.
- PubMed fallback demotion produced the clearest reduction in provider burden.
- Assistant-side reporting work in the inspected correction window used `gpt-5.4`, `14` assistant model responses with usage records, and at least `15` direct tool calls.

## Inferred
- The narrowed conditional-source design is a net win in technical resource consumption.
- Assistant-side reporting economics are now partially recoverable from OpenClaw session JSONL, which is enough to enrich future reports substantially.
- Any statement about “pipeline billing savings” is still proxy-only until pipeline token/cost instrumentation is populated.

## Missing / unobservable
- true model call counts inside the MGAP pipeline
- true token consumption inside the MGAP pipeline
- full-day normalized assistant per-task accounting without additional extraction logic
- true USD-equivalent spend for pipeline operations

# 9. Recommended next actions

## Reporting process
1. Keep using the combined technical + economic reporting framework from the new `resource-cost-reporting` skill.
2. Never label a report as “resource/cost” complete unless token/model/tool/cost fields were checked explicitly.

## Instrumentation
3. Populate `cost_event.tokens_prompt`, `tokens_completion`, `tokens_total` when any LLM-assisted stage exists.
4. Populate `cost_event.estimated_cost_usd` using configurable provider pricing.
5. Add explicit model/provider identifiers where model-based enrichment or assistant-side calls matter.
6. If assistant-side tool economics matter, store or export OpenClaw run metadata separately from project pipeline DB.

## Pipeline policy
7. Keep arXiv narrow-trigger.
8. Keep Europe PMC as narrowed biomedical bridge/fallback.
9. Keep PubMed fallback-only for PMID/PMCID/abstract and PMID-led paths.

---

# 9. Recommended next actions

## Reporting process
1. Keep using the combined technical + economic reporting framework from the new `resource-cost-reporting` skill.
2. When local session access is permitted, always inspect OpenClaw session JSONL for assistant-side model/tool/token/cost usage.
3. Never label a report as “resource/cost” complete unless token/model/tool/cost fields were checked explicitly on both pipeline-side and assistant-side where relevant.

## Instrumentation
4. Populate `cost_event.tokens_prompt`, `tokens_completion`, `tokens_total` when any LLM-assisted stage exists.
5. Populate `cost_event.estimated_cost_usd` using configurable provider pricing.
6. Add explicit model/provider identifiers where model-based enrichment or assistant-side calls matter.
7. If assistant-side tool economics matter routinely, add a reusable extraction script that converts OpenClaw session JSONL into per-task accounting summaries.

## Pipeline policy
8. Keep arXiv narrow-trigger.
9. Keep Europe PMC as narrowed biomedical bridge/fallback.
10. Keep PubMed fallback-only for PMID/PMCID/abstract and PMID-led paths.

# 10. Bottom line
This redone report gives the correct framing:

- **Technically**, the current conditional-source strategy is more efficient and more productive on the strict same-batch replay.
- **Economically**, the project currently lacks enough instrumentation to produce a true billing report.
- What we can say today is about **workload proxies**, not real spend.
- The most important economic conclusion is therefore not just “which source is expensive”, but also “which billing dimensions are still invisible and must be instrumented next”.
