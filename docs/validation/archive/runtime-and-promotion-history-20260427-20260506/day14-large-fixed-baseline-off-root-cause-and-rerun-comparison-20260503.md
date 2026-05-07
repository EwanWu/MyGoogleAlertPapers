# Day14 large-fixed baseline-off root-cause and rerun comparison (2026-05-03)

## Objective
Diagnose why the original large-fixed baseline-off run terminated with a `SIGKILL`-like outer failure, rerun the full chain cleanly, and compare:
1. original incomplete run
2. recovered control reconstructed from the incomplete enrich DB
3. clean full-chain rerun

## Artifacts
- Original incomplete DB: `data/benchmark/day14_openalex_repo_shadow_large_fixed_baseline_off_20260502.db`
- Recovered control DB: `data/benchmark/day14_openalex_repo_shadow_large_fixed_baseline_off_recovered_20260503.db`
- Recovered control report: `docs/validation/day14-openalex-repo-shadow-large-fixed-baseline-off-recovered-20260503.json`
- Clean rerun DB: `data/benchmark/day14_openalex_repo_shadow_large_fixed_baseline_off_rerun_20260503.db`
- Clean rerun report: `docs/validation/day14-openalex-repo-shadow-large-fixed-baseline-off-rerun-20260503.json`
- Clean rerun log: `logs/day14_openalex_repo_shadow_large_fixed_baseline_off_rerun_20260503.log`
- Original control-session SIGKILL notice (assistant session transcript): `/home/ewan/.openclaw/agents/deepblue/sessions/776194e4-584a-4012-8cb7-41a0a87c9de5.jsonl` line 5

## Known

### 1. The original failure was not a deterministic pipeline bug in `merge` or `dedup`
The original incomplete DB contains a fully successful enrich stage:
- `batch_run = 1`
- only row: `stage = enrich_candidates`, `processed_count = 755`, `status = ok`, `duration_ms = 8149528`
- enrich outputs are already present:
  - `source_record_count = 726`
  - `matched_source_record_count = 487`
  - `candidate_enrichment_status = 726`
- but there is no downstream output:
  - `merged_metadata_proposal_count = 0`
  - `canonical_paper_count = 0`
  - `merge_review_queue_count = 0`
  - no JSON/MD report written

The same incomplete enrich DB was then copied into a forensic recovery path and `merge + dedup` completed successfully in well under 1 second:
- recovered `merge_metadata`: `368` processed, `366 ms`
- recovered `dedup_candidates`: `357` processed, `43 ms`

So the original failure happened **after enrich was already durable**, not because merge/dedup logic itself was broken.

### 2. The exact query named in the SIGKILL notice does not reproduce the failure
The original user-visible system notice said:
- `Exec failed (... signal SIGKILL)` while handling Crossref title query
- query key: `FDG PET-CT uncovers cardiac sarcoidosis when CMR is inconclusive: the impact of multimodal imaging`

On the clean rerun, the same query appears in the log and the run still completes normally:
- rerun log line 422: Crossref title dispatch at `700/755`
- rerun log line 423: OpenAlex title dispatch for the same query immediately after
- rerun process exits with code `0`
- rerun report JSON/MD are written successfully

This rules out the strongest “that particular query always crashes the pipeline” hypothesis.

### 3. The clean rerun completed end-to-end and is much faster than the original enrich-only run

| run | report | batch_run_count | provider_intent_count | source_record_count | matched_source_record_count | merged_metadata_proposal_count | canonical_paper_count | review_queue_count | total_batch_duration_ms | total_provider_latency_ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| original incomplete | no | 1 | 726 | 726 | 487 | 0 | 0 | 0 | 8,149,528 | 8,131,763 |
| recovered control | yes | 3 | 726 | 726 | 487 | 357 | 283 | 0 | 8,149,937 | 8,131,763 |
| clean rerun | yes | 3 | 702 | 702 | 532 | 356 | 281 | 2 | 3,467,324 | 3,459,062 |

### 4. The rerun’s runtime win came from a materially smaller title/Crossref tail
Comparing recovered control vs rerun enrich-dispatch summaries:

| metric | recovered | rerun | delta |
|---|---:|---:|---:|
| runnable_provider_intents | 755 | 755 | 0 |
| dispatch_request_count | 459 | 434 | -25 |
| title_lane_request_count | 312 | 287 | -25 |
| post_openalex_suppressed_group_count | 28 | 53 | +25 |
| post_openalex_unsuppressed_targeted_group_count | 98 | 73 | -25 |
| shared_title_reuse_group_count | 61 | 62 | +1 |
| shared_title_reuse_request_savings | 73 | 74 | +1 |

The runtime difference is therefore tightly explained by:
- more `post_openalex` suppression in rerun (`53` vs `28`)
- fewer residual targeted Crossref title requests (`73` vs `98`)
- same runnable intent count

This is not a control-plane effect alone; the bibliographic outcome space actually changed.

### 5. The clean rerun is not semantically identical to the recovered control
#### Final counts
- recovered control:
  - `merged_metadata_proposal_count = 357`
  - `canonical_paper_count = 283`
  - `merge_review_queue_count = 0`
  - `severe_doi_conflict_count = 0`
- clean rerun:
  - `merged_metadata_proposal_count = 356`
  - `canonical_paper_count = 281`
  - `merge_review_queue_count = 2`
  - `severe_doi_conflict_count = 2`

#### Provider-level matched-source composition changed
Matched source records by provider:
- recovered: `crossref 294`, `openalex 177`, `arxiv 9`, `pubmed 5`, `europepmc 2`
- rerun: `crossref 269`, `openalex 252`, `arxiv 1`, `pubmed 5`, `europepmc 5`

So rerun shifts evidence mass away from Crossref and toward OpenAlex/biomedical providers.

#### Candidate-level changes with semantic consequence
1. **Two candidates newly blocked into review in rerun**
   - `cand_380600011de29f8b`
   - `cand_3a6f282d35458d76`
   - recovered behavior: Crossref-only match to SSRN preprint DOI `10.2139/ssrn.5959308`, accepted into canonical
   - rerun behavior: OpenAlex also matches a 2026 *Neurobiology of Aging* article DOI `10.1016/j.neurobiolaging.2026.03.005` with PMID `41863983`
   - result: rerun correctly surfaces `severe_conflict:doi` and blocks both into review

2. **Two recovered-only canonicals disappear in rerun without becoming review items**
   - `cand_8994637b2b637b39`
   - `cand_f3f78ee6a4d53c12`
   - both are cases where recovered accepted a weaker fallback/canonical path, but rerun upstream matches changed enough that no stable canonical survived.

3. **One new canonical appears only in rerun**
   - `cand_a9bfd54eb53be57b`
   - recovered: no matched source record usable for canonicalization
   - rerun: OpenAlex title match yields DOI `10.7298/yfgk-pd08`

### 6. Many recovered-vs-rerun changes are metadata-surface changes rather than hard semantic changes
Across shared merged proposals, there are many field-level differences (e.g. PMID presence, publication-type string, venue normalization, author spelling variants). Example classes:
- recovered lacked PMID but rerun gained it
- recovered had `article` while rerun had `journal-article`, or vice versa
- recovered used OpenAlex as preferred source where rerun used Crossref, or the reverse

These explain much of the 123 merged-proposal row differences without all of them being “real decision regressions.”

## Inferred

### A. Most likely root cause of the original SIGKILL
The most likely cause is **outer-process termination external to the replay pipeline logic**, not deterministic in-pipeline corruption.

Why this is the strongest inference:
1. original enrich committed cleanly and durably
2. the same problematic query succeeds in rerun
3. merge/dedup on the original enrich payload succeed immediately when resumed separately
4. clean rerun exits code `0`

So the event is more consistent with one of:
- supervisor / wrapper / session-level kill
- transient host/resource pressure event
- exec/session control-path interruption after enrich completion but before summary writing

### B. The rerun is probably the more trustworthy control snapshot for current provider reality
Because rerun:
- completed cleanly end-to-end
- has an auditable full log
- surfaces two real DOI conflicts that recovered control missed
- produces more OpenAlex matches and fewer residual Crossref title fallbacks

That does **not** mean recovered control is useless. It remains valuable as a forensic reconstruction of what the original enrich payload would have produced if the wrapper had not died.

## Speculative / unresolved
- I do **not** have kernel/OOM evidence, so I cannot prove an OOM kill.
- I also cannot prove whether the original `SIGKILL` came from OpenClaw exec/session supervision, host-level pressure, or another external controller.
- The large runtime improvement in rerun could reflect a combination of provider-side response variability and changed live index state, not just algorithmic savings.

## Bottom line
1. **Original failure mode**: external/outer termination after enrich durability, not a deterministic merge/dedup bug.
2. **Recovered control**: valid forensic reconstruction of the original enrich payload; gives `283 canonical / 0 review`.
3. **Clean rerun**: current best control artifact for decision-making; gives `281 canonical / 2 review`, and those two review items are justified severe DOI conflicts.
4. **Decision implication**: if the next step is A/B comparison against treatment-on, the clean rerun is the better control baseline for current evidence, while the recovered control should be kept as a forensic reference rather than discarded.
