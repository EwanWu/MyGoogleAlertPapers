# Conditional-source replay validation on the same 249 normalized candidates

## Date
2026-04-10

## Objective
Run a strict apples-to-apples replay comparison on the **same normalized candidate set** from the historical 100-mail baseline, in order to evaluate the current conditional-source strategy without live-mailbox drift.

## Replay design
### Baseline database
- `data/mgap_pkg3_guardrail_100.db`

### Replay database
- `data/mgap_pkg3_guardrail_100_replay_conditional_20260410.db`

### Procedure
1. Copy `data/mgap_pkg3_guardrail_100.db`
2. Preserve `paper_candidate` and `paper_candidate_normalized`
3. Clear downstream tables:
   - `query_cache`
   - `source_record`
   - `candidate_enrichment_status`
   - `merged_metadata_proposal`
   - `canonical_paper`
   - `candidate_paper_link`
   - `merge_review_queue`
   - `cost_event`
   - `batch_run`
4. Re-run only:
   - `enrich-candidates --limit 500`
   - `merge-metadata --limit 500`
   - `dedup-candidates --limit 500`

This makes the comparison strictly reuse the same `249` normalized candidates.

## Candidate set
- baseline normalized candidates: `249`
- replay normalized candidates: `249`

So this comparison is genuinely same-batch.

## Headline result
The current conditional-source strategy was **better overall** on the same candidate set.

### Improvements
- merged proposals: `203 -> 211` (`+8`)
- canonical papers: `164 -> 170` (`+6`)
- enrich duration: `2219856 ms -> 1514821 ms` (`-705035 ms`, about `-31.7%`)

### New downside
- review queue: `0 -> 2`

## Batch-level comparison
### Baseline
- enrich_candidates: processed `882`, duration `2219856 ms`
- merge_metadata: processed `249`, duration `212 ms`
- dedup_candidates: processed `203`, duration `13 ms`

### Replay
- enrich_candidates: processed `837`, duration `1514821 ms`
- merge_metadata: processed `249`, duration `200 ms`
- dedup_candidates: processed `211`, duration `11 ms`

## Interpretation of batch-level cost
Even after adding `Europe PMC` and `arXiv`, the replay run actually produced:
- fewer total provider intents materialized into processed enrich work (`837` vs `882`)
- much lower total enrich wall time

This suggests that the current conditional-source logic reduces unnecessary broad fallback behavior more than it adds new work.

## Provider comparison
### Baseline provider summary
- crossref: `249` calls, `199` matched, avg `2007.6 ms`, total `499883 ms`
- openalex: `249` calls, `167` matched, avg `2966.4 ms`, total `738623 ms`
- pubmed: `249` calls, `104` matched, avg `2642.1 ms`, total `657886 ms`
- semanticscholar: `249` calls, `33` matched, avg `1224.7 ms`, total `304946 ms`

### Replay provider summary
- arxiv: `8` calls, `8` matched, avg `1918.4 ms`, total `15347 ms`
- crossref: `249` calls, `197` matched, avg `2144.3 ms`, total `533939 ms`
- europepmc: `98` calls, `28` matched, avg `1915.4 ms`, total `187708 ms`
- openalex: `249` calls, `173` matched, avg `1132.2 ms`, total `281912 ms`
- pubmed: `98` calls, `60` matched, avg `2371.6 ms`, total `232416 ms`
- semanticscholar: `249` calls, `18` matched, avg `1030.9 ms`, total `256693 ms`

## Provider interpretation
### arXiv
- very small volume: `8` calls
- perfect match yield: `8/8`
- clearly worth keeping as a narrow resolver for arXiv-native candidates

### Europe PMC
- `98` calls, `28` matched
- useful, but still a non-trivial cost source
- appropriate as a biomedical bridge/fallback, not as a broad primary source

### PubMed
- calls reduced sharply: `249 -> 98`
- total latency reduced sharply: `657886 -> 232416 ms`
- still contributes useful `pmid/abstract` information
- demotion to fallback is strongly supported

### OpenAlex
- same call count, better match count (`167 -> 173`)
- dramatically better latency in this replay run
- remains a strong core source

### Semantic Scholar
- same call count but fewer matches (`33 -> 18`)
- however overall merged output still improved
- current result suggests Semantic Scholar may be less central than Crossref/OpenAlex for this candidate set

## Cost-event proxy comparison
Direct money billing is still not implemented.
So current accounting remains a proxy based on:
- event counts
- provider call counts
- latency

### Baseline provider latency proxy total
- `2201338 ms`

### Replay provider latency proxy total
- `1508015 ms`

This is about a `31.5%` reduction in external-provider latency burden on the same input set.

## Merge confidence comparison
### Baseline
- `0.9`: `151`
- `0.8`: `36`
- `0.65`: `4`
- `0.45`: `12`

### Replay
- `0.9`: `161`
- `0.8`: `40`
- `0.65`: `2`
- `0.45`: `6`
- `0.25`: `2`

## Interpretation of merge confidence
- high-confidence merges increased
- medium/low-confidence merges decreased overall
- two very-low-confidence cases appeared and both corresponded to the new review-queue blocks

So the quality pattern is broadly favorable, with a small number of newly surfaced problematic cases.

## New merged gains
Replay produced `8` merged proposals that the baseline did not produce.
There were `0` cases that baseline merged but replay lost.

### Composition of the 8 gains
- `6` appear to be arXiv-native gains or arXiv-assisted gains
- `2` are biomedical/JAMA cases that became merged but were correctly blocked for canonicalization due to severe DOI conflict

Representative new gains include:
- `cand_2ab2b1a43f16ee1f` → arXiv-native dMRI transformer paper
- `cand_40874060f658736c` → arXiv-native CIMT/DINOv3 paper
- `cand_53f38bf4ec58086c` → arXiv-native CMR uncertainty paper
- `cand_7a1dd15089495cf9` → arXiv-native LGE-MRI scar segmentation paper
- `cand_cd1c124046a3d47d` → arXiv-native federated-learning paper
- `cand_a0eb313c3c2bc88b` and `cand_ced429ee0899aece` show arXiv + Europe PMC / PubMed complementarity

## Review-queue analysis
Replay introduced `2` blocked candidates:
- `cand_04a4b541bf557208`
- `cand_2148e2f27a27de8f`

Both are effectively the same JAMA Cardiology paper and both were blocked for:
- `severe_conflict:doi`

### What happened
For these candidates:
- `Europe PMC` matched a record with DOI `10.1001/jamacardio.2026.0083`
- `PubMed` matched the same title / PMID (`41811342`) but returned DOI `10.1161/circep.124.013059`

This is a serious DOI inconsistency.
The replay pipeline correctly escalated it to review instead of silently canonicalizing.

### Important interpretation
This does **not** primarily indicate that the new strategy degraded quality.
Instead, it indicates that the new source combination surfaced a latent metadata inconsistency that the baseline path did not expose clearly enough.

In other words, these 2 new review cases are better interpreted as:
- newly surfaced metadata conflict
- correct safety behavior by the merge guardrail

not as simple regression noise.

## Known
- Same candidate set was reused successfully.
- Current conditional-source strategy improved merged coverage and canonical-paper yield.
- Replay enrichment wall time decreased substantially.
- PubMed fallback demotion looks strongly validated.
- arXiv narrow-trigger integration is clearly beneficial.
- Europe PMC adds real value but still carries meaningful cost.
- Two severe DOI conflicts were surfaced and correctly blocked.

## Inferred
- The current strategy is a net improvement over the earlier baseline for this workload.
- Europe PMC is useful enough to keep, but only in a narrowed bridge/fallback role.
- Some of the apparent cost reduction may also reflect provider-side runtime variance, especially for OpenAlex, so repeated replay would still help characterize stability.

## Speculative
- A small further rule change may remove the 2 new blocked cases automatically if PubMed DOI is ignored whenever PubMed and Europe PMC agree on PMID/title but disagree on DOI and Crossref is non-confirmatory.
- Semantic Scholar may be worth demoting further in some title-only non-biomedical paths, but this needs separate evidence.

## Recommended next actions
1. Keep `arXiv` integration as currently scoped.
2. Keep `Europe PMC` integration, but only as narrowed biomedical bridge/fallback.
3. Add a DOI conflict suppression rule for cases where:
   - PubMed and Europe PMC share the same PMID/title
   - PubMed DOI disagrees
   - PubMed is not allowed to override DOI as a fallback-only source
4. Add explicit monetary estimation into `cost_event.estimated_cost_usd` using configurable provider pricing, even if many sources are effectively free, so reporting can distinguish time-cost from money-cost.
5. Preserve the replay workflow as a standard validation method for future enrichment-policy changes.

## Bottom line
On the same 249 normalized candidates, the current conditional-source strategy is a **real improvement**:
- more merged coverage
- more canonical papers
- substantially lower enrichment time burden
- useful arXiv gains
- useful but bounded Europe PMC contribution

The only newly introduced issue was `2` review-queue cases, and both appear to be legitimate DOI conflicts surfaced by improved source triangulation rather than careless regression.
