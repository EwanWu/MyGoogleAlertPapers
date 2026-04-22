# Metadata Enrichment Strategy

## Objective
Use low-cost, explainable API cascades to enrich paper candidates before deduplication and canonicalization.

## Identifier-first policy
If a candidate contains a strong identifier, prefer direct identifier lookups.

### DOI-first path
Suggested order:
1. Crossref
2. OpenAlex
3. Semantic Scholar
4. PubMed only as fallback when PMID/PMCID confirmation or missing biomedical fields are needed

### PMID-first path
Suggested order:
1. PubMed
2. Europe PMC
3. OpenAlex
4. Semantic Scholar

PubMed remains primary for PMID-led resolution.

## Title-based path
When no strong identifier is available, use title search.

### Biomedical-leaning candidates
Suggested order:
1. Crossref if DOI is available
2. OpenAlex
3. Semantic Scholar
4. PubMed as fallback for title-only biomedical candidates, or when PMID / abstract / PMCID is still missing
5. Europe PMC if added later

### General scholarly candidates
Suggested order:
1. Crossref
2. Semantic Scholar
3. OpenAlex

## Source confidence guidance
- PubMed / Europe PMC: strong biomedical fallback sources, especially for PMID, PMCID, and some abstracts, but should not be the default authority for DOI-led record establishment
- Crossref: strong for DOI-centered formal publication metadata
- OpenAlex: useful for broad discovery, IDs, linking, and often useful abstract coverage, but not sole abstract authority
- Semantic Scholar: useful for graph-style enrichment and search support

## Field-level merge policy
- Preferred record establishment should rely first on Crossref and OpenAlex when they agree on title, venue, DOI, and year.
- PubMed should be treated as fallback-only for `title`, `venue`, and `doi` during merge selection.
- PubMed remains eligible to supply `abstract`, `pmid`, and `pmcid`, and can still act as a last-resort source when no non-PubMed record exists.

## Validation status
Fresh-30 validation on `2026-04-10` showed that demoting PubMed to fallback reduced provider intents from `380` to `341` while keeping merged proposals at `73` and canonical papers at `56` in the tested slice.

## Merge behavior
Do not collapse all source outputs directly into a single truth record.
Instead:
1. retain source_record per provider
2. produce merged_metadata_proposal with explicit priority trace and conflict flags

## Enrichment strategy state update (2026-04-16)

The provider-order and field-confidence ideas above are still broadly useful, but recent work showed that enrichment strategy must now be read together with replay policy and orchestration behavior.

### What is now established
- provider behavior is controlled through policy profiles in real replay runs, not only by static strategy prose
- enrichment quality must be judged together with downstream merge behavior; more matched source records do not automatically imply better final canonical outcomes
- long-run enrich stages need explicit operational hardening such as timeout support, progress logging, and checkpoint-friendly execution

### What recent Package work clarified
- Package A established `conditional_sources_v2` as the current default baseline direction for policy-driven enrich/merge comparison
- Package B larger-slice replay showed that a policy can slightly increase matched source counts while still degrading final merge/canonical output
- therefore enrichment strategy evaluation should not stop at provider hit-rate or matched-source counts; it must terminate in proposal/review/canonical outcomes on a fixed seed

### Current operational reading rule
When evaluating enrichment changes:
1. compare on the same fixed normalized seed when possible
2. inspect downstream `merged_metadata_proposal`, `merge_review_queue`, and `canonical_paper` effects
3. treat smoke runs as execution checks, not final evidence
4. document orchestration limitations separately from policy-quality conclusions

### Current recommended companion docs
- `docs/21-packageA-implementation-and-replay-results-2026-04-15.md`
- `docs/34-packageB-phase-summary-and-archive-guide-2026-04-16.md`
- `docs/validation/packageB-large-slice150-summary-20260416_slice150.md`

## OA enrichment placement update (2026-04-22)

Unpaywall should now be treated as a **post-dedup OA enhancement step**, not as part of the core candidate-level bibliographic enrich cascade.

Operational rule:
1. use Crossref / OpenAlex / Semantic Scholar / PubMed / Europe PMC / arXiv to build bibliographic evidence
2. merge and deduplicate first
3. then run Unpaywall over canonical DOI to fill OA status and OA URL

Reason:
- Unpaywall does not replace bibliographic providers
- it adds latency rather than reducing it
- its main value is OA coverage on the final canonical paper set
- corrected placement analysis showed `post_dedup` gives much better OA URL coverage than candidate-level lookup, with cleaner semantics than `post_merge`

Recommended command-level shape:
- `mgap dedup-candidates`
- `mgap enrich-paper-oa`

