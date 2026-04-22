# Track A author-blob-only replay decision report

## Date
2026-04-21

## Objective
Test whether the `author_blob` reject rule alone is worth keeping as an ultra-narrow Track A patch, using the same fixed large-slice150 seed and comparing:
- control: `conditional_sources_v2`
- treatment: `conditional_sources_v2_author_blob_only`

## Run outcome
The replay completed successfully.
- log: `/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/logs/trackA_author_blob_only_large_slice150_20260421b.log`
- completed_at: `2026-04-21 15:04:35 +08:00`
- shell pid `10065`: no longer running

## Top-line metrics

### v2
- matched_source_record_count: `764`
- merged_metadata_proposal_count: `368`
- normalized_only_fallback_proposal_count: `36`
- canonical_paper_count: `292`
- merge_review_queue_count: `4`
- cost_event_count: `2141`
- total_batch_duration_ms: `1765776`
- total_provider_latency_ms: `1753939`

### author_blob_only
- matched_source_record_count: `763`
- merged_metadata_proposal_count: `367`
- normalized_only_fallback_proposal_count: `33`
- canonical_paper_count: `291`
- merge_review_queue_count: `4`
- cost_event_count: `2140`
- total_batch_duration_ms: `2008641`
- total_provider_latency_ms: `1997842`

### delta (author_blob_only minus v2)
- matched_source_record_count: `-1`
- merged_metadata_proposal_count: `-1`
- normalized_only_fallback_proposal_count: `-3`
- canonical_paper_count: `-1`
- merge_review_queue_count: `0`
- cost_event_count: `-1`
- total_batch_duration_ms: `+242865 ms`
- total_provider_latency_ms: `+243903 ms`

## Proposal-level diffs that actually changed output
There were 6 candidate-level proposal diffs, but only 4 unique title-level effects.

### 1) Good catch: one obvious garbage author blob was removed
Candidate `cand_400e144162689110`
- title in v2: `Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3`
- v2 behavior: accepted as `normalized_only` fallback with no DOI, no venue, no year, no authors
- author_blob_only behavior: dropped from merged proposals entirely

This is the clean positive result of the rule.

### 2) Improvement: one real paper gained a DOI, but it appeared 3 times
Candidates:
- `cand_84878dfc2c01995f`
- `cand_904fa5818a9712ae`
- `cand_9b521f03168d6572`

Title:
- `Left Bundle Branch Area Stylet-Driven Lead: Performance, Safety and Quality of Life at 12 Months Post Implant (The BIO-CONDUCT IDE Study)`

Effect:
- v2: fallback-only proposal, DOI missing
- author_blob_only: Semantic Scholar matched and supplied DOI `10.1016/j.hrthm.2026.03.1889`

This is a real gain, but it is the same paper repeated three times, not three independent wins.

### 3) Regression: one real paper lost a correct DOI
Candidate `cand_c487f1dd5fd44877`
- title: `Vascular and Hematologic Disorders`
- v2: Crossref matched with DOI `10.1016/j.nic.2026.01.001`
- author_blob_only: Crossref no longer matched, a different Crossref DOI appeared on the raw source row (`10.1007/978-3-642-67152-4_13`), and the final merged proposal fell back to normalized-only with no DOI

This is a real metadata downgrade.

### 4) Regression: one real paper lost a correct DOI despite still having PubMed support
Candidate `cand_ef45f083c154b55c`
- title: `Prevalence of heart failure with preserved ejection fraction in patients with ischemia and non-obstructive coronary arteries`
- v2: Crossref and PubMed supported DOI `10.1038/s41598-026-42032-x`
- author_blob_only: Crossref match disappeared, PubMed still matched, but final proposal still ended up with `preferred_doi = null`

This is also a real metadata downgrade, and it is more concerning because the identifier evidence still existed in the treatment run.

## Hidden churn behind the near-flat top line
For an allegedly ultra-narrow patch, internal source matching changed much more than the summary counts suggest.

Matched-source flips between runs:
- Crossref: `6` lost, `0` gained
- OpenAlex: `2` lost, `1` gained
- PubMed: `2` lost, `1` gained
- Semantic Scholar: `32` lost, `39` gained
- total matched-flag flips: `83`

So the patch is not behaving like a tiny local cleanup. It perturbs provider selection broadly, especially around Semantic Scholar.

## Interpretation
Observed benefit:
- removes one obviously bad author-blob fallback candidate
- recovers DOI for one repeated real-paper case

Observed cost:
- loses one canonical paper overall (`292 -> 291`)
- loses correct DOI coverage for at least two legitimate papers
- increases runtime by about `4.0` minutes of provider latency / wall time
- causes broad internal match churn (`83` flips), which is too much instability for a rule meant to be ultra-narrow

## Decision
My recommendation is **do not keep the current `author_blob_only` profile as a standalone Track A patch**.

Reason:
- it does catch the intended garbage shape,
- but the mechanism is not isolated enough,
- and the collateral churn is too large relative to the size of the win.

In short, this is not a clean “one bad case removed, everything else unchanged” rule.

## Better next move
Keep the intuition, but narrow the implementation further.

Best next refinement:
1. apply the author-blob rejection only at the final `normalized_only` fallback acceptance step
2. require the bad-shape pattern plus weak metadata, for example no DOI/PMID, no reliable venue/year, and low title evidence
3. avoid letting this rule change provider match selection globally

That would preserve the useful catch (`cand_400e144162689110`) without risking broad Crossref / Semantic Scholar churn.

## Bottom line
`author_blob` is directionally useful as a **fallback garbage filter**, but **not yet safe enough as a live matching-time Track A patch**.