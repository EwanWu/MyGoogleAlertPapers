# Current library-build status and tail issues (2026-05-07)

## Objective

Summarize the current state of the 163 formal-library build, identify the remaining blockers, and state what should and should not be treated as the next mainline path.

## Scope

- DB: `/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db`
- Project root: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers`
- Key artifacts referenced here:
  - `data/exports/remaining_need_merge_after_tail57_20260507.{json,md}`
  - `data/exports/residual48_triage_summary_20260507.{json,md}`
  - `data/exports/manual_standard_entries_20260507.json`
  - `scripts/run_phase2_regular_chunk07_bounded_fastpass_163_incremental_20260507.sh`

---

## Executive summary

The library build has effectively exited the high-throughput regular-chunk phase and entered a **residual-tail cleanup phase**.

The regular `identifier_fastpath` mainline was successful for chunk03-05 and was the right choice after chunk02's slow OpenAlex title-lane failure. However, by the time we reached the tail, the remaining candidates were no longer amenable to standard chunk-style automation. The recent bounded chunk07 check showed that the regular fast-pass route is now functionally exhausted for the leftover set.

The practical meaning is:

1. **Mainline bulk building is largely complete.**
2. **The remaining work is not throughput-limited; it is sample-quality-limited.**
3. **The next phase should be residual triage and selective rescue, not chunk08+ continuation.**

---

## Current status

### Known (directly supported)

#### 1) Current confirmed DB scale

Direct live DB checks confirm:

- `canonical_papers = 14638`
- `candidate_paper_links = 64478`
- `review_queue_total = 12`

Also directly observable:

- `paper_candidate_normalized = 64528`
- `candidate_paper_link distinct candidate_id = 64478`
- therefore `unlinked_total = 50`

Interpretation:
- the build has already linked the overwhelming majority of normalized candidates;
- the current unresolved tail is small in absolute count, but difficult in composition.

#### 2) Regular fast-pass mainline is exhausted on the current tail

The bounded chunk07 regular fast-pass validation (`CHUNK_LIMIT=50`) produced:

- `library_prelinked_candidate_count = 0`
- `pre-experimental runnable intents = 100`
- `experimental_skipped_provider_intents = 100`
- `runnable_provider_intents = 0`
- `dispatch_requests = 0`
- final DB counts unchanged

This is strong evidence that the current leftover set is no longer reachable by the existing regular fast-pass path.

Source artifacts:
- `data/exports/remaining_need_merge_after_tail57_20260507.md`
- `memory/projects/MyGoogleAlertPapers.md` summary of the bounded chunk07 run

#### 3) Residual triage has already produced meaningful gains

Residual-tail triage has already landed:

- downloaded thesis/dissertation-like PDFs: **13**
- standard entries established: **6**
- failed thesis direct-download attempts: **0** (after browser/CDP rescue)

Source:
- `data/exports/residual48_triage_summary_20260507.md`
- `data/exports/manual_standard_entries_20260507.json`

#### 4) Tail57 audit already showed diminishing automatic return

After the chunk06 tail57 title-core sweep:

- remaining `need_merge = 48`
- only **1** additional candidate was converted by that sweep
- the residual set was dominated by repository PDFs, ResearchGate copies, books/ebooks, and other non-standard or low-authority URL/title-only records

Source:
- `data/exports/remaining_need_merge_after_tail57_20260507.md`

---

## Working interpretation

### Inferred

#### 1) Effective remaining `need_merge` is now about **42**

This is inferred from:

- tail57 residual export: `need_merge = 48`
- standard entries established after triage/follow-up: `6`

That yields a tracked remaining tail of approximately:

- `48 - 6 = 42`

This matches the latest project memory summary and should be treated as the current working residual count unless superseded by a fresher export.

#### 2) The bottleneck has shifted from pipeline throughput to residual heterogeneity

Earlier stages were limited by throughput and provider-lane strategy. Now the dominant problem is different:

- leftover items are structurally messy;
- many are weak-identifier, title-only, repository, mirror, or low-authority records;
- many do not justify another standard pipeline pass.

So the problem is no longer “how do we make the main pipeline faster?” but rather:

- “which remaining items are worth saving?”
- “which require browser-assisted rescue?”
- “which should be skipped as low-value or out-of-scope?”

---

## Main problems

### Problem 1 — regular chunk-style automation has reached the end of its useful life on this dataset tail

The current leftover set does not benefit from:

- library prelink,
- standard identifier fast-pass,
- or a generic title-core revisit.

This means treating the current residual set as `chunk08+` would mostly create empty or low-yield runs.

### Problem 2 — remaining candidates are low-standardization, low-authority, or structurally ambiguous

The current tail is dominated by categories such as:

- repository PDFs;
- ResearchGate copies;
- books / book-chapter-like records;
- non-standard pages;
- title-only or weak-identifier items.

These are hard not because the pipeline “missed” them accidentally, but because they are fundamentally poor inputs for the standard route.

### Problem 3 — the cleanup path is increasingly hybrid and operator-dependent

A meaningful subset of salvage work now depends on:

- browser-visible/manual verification;
- Windows visible Chrome + remote debugging attach;
- CDP-level PDF interception or download behavior;
- selective manual metadata establishment.

This is slower and less scalable than the earlier mainline, but it is the correct mode for this stage.

### Problem 4 — some unresolved items may not be worth saving into the canonical library

The residual summary already shows skip buckets including:

- books/book-chapter-like;
- non-English out of scope;
- repo PDFs not clearly theses;
- other nonstandard / low-confidence items.

This is a scope problem, not just a tooling problem. A fully exhaustive “save everything” policy would likely have poor ROI and lower library quality.

### Problem 5 — observability for run-level retrospective analysis is still weaker than ideal

The recent chunk02 forensic review exposed schema/observability friction, including the failed assumption that some tables exposed `run_id` directly for the needed rollups. This does not block current library completion, but it does make retrospective diagnosis and run-comparison analysis more cumbersome than they should be.

---

## What should happen next

### Recommended next phase

Treat the project as being in **residual mode**, not **regular chunk mode**.

#### Priority A — high-confidence standard entries

Continue case-by-case establishment for candidates that have:

- credible publisher pages;
- DOI recoverability;
- clear journal/proceedings identity;
- strong title match with low ambiguity.

#### Priority B — thesis/dissertation rescue

Continue to rescue thesis/dissertation-like PDFs when:

- the item is genuinely thesis-like;
- the PDF is reachable via direct HTTP, visible browser session, or CDP interception;
- the result contributes real library value.

#### Priority C — explicit skip / archive buckets

Do not spend standard-chunk compute on:

- books / book chapters by default;
- low-authority mirrors with no trustworthy metadata path;
- weak nonstandard leftovers with low confidence and low expected value.

---

## What should *not* happen next

### Do not

- continue with `chunk08+` as if the regular fast-pass mainline were still productive;
- reintroduce slow title-heavy automation into the mainline without a bounded justification;
- interpret the remaining tail as a throughput problem alone;
- spend bulk pipeline effort on low-value residual buckets that are better skipped or archived.

---

## Bottom line

### Known

- The mainline build succeeded and reached a very high coverage level.
- Current confirmed scale is `canonical_papers=14638`, `candidate_paper_links=64478`, `review_queue_total=12`, `unlinked_total=50`.
- Residual triage already recovered **13 PDFs** and established **6 standard entries**.
- Bounded chunk07 showed the regular fast-pass route is effectively exhausted for the remaining tail.

### Inferred

- The working residual `need_merge` is about **42**.
- The dominant remaining difficulty is **sample quality / heterogeneity**, not mainline throughput.

### Decision

The library build should now be managed as a **small, selective residual-tail program**, not as another round of standard chunked automation.
