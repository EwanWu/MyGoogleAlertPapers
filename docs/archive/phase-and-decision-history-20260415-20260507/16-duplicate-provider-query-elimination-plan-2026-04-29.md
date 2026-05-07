# Duplicate provider-query elimination memo (2026-04-29)

> Status update (2026-04-29 later): the Phase 1 exact library-first prelink part of this memo has now been implemented and validated. Treat this document as the blueprint / rationale layer, and read `docs/17-phase1-library-prelink-implementation-and-ablation-2026-04-29.md` for the implementation/archive layer.

## Goal

Answer two concrete questions:

1. How much duplicate provider traffic is still happening because dedup sits **after** enrich, while the same paper can recur across many mails inside the same batch?
2. How should the pipeline avoid re-querying providers when a later batch contains papers that were already fully processed and validated in the existing library?

This memo separates **Known**, **Inferred**, and **Proposed**.

---

## Known

### 1) The current pipeline already removes some duplicate provider traffic, but only at the **query-key** level

Current code paths already do the following:

- **Exact provider/query-key dedup inside one enrich run**
  - `src/mygooglealertpapers/pipeline/enrich.py`
  - `_build_dispatch_groups(...)` groups intents by `(provider, query_type, query_key)`.
  - This means repeated identical DOI/title/PMID queries inside the same run are already collapsed before dispatch.

- **OpenAlex DOI batching**
  - `src/mygooglealertpapers/pipeline/enrich.py`
  - OpenAlex DOI intents are grouped and sent in batched chunks instead of one-by-one.

- **Cross-run exact cache hits**
  - `query_cache` exists in schema and is consulted before provider dispatch.
  - `src/mygooglealertpapers/db/schema.py`
  - `src/mygooglealertpapers/db/repository.py#get_query_cache`
  - If the same DB already contains the same `(provider, query_type, query_key[, field_set_hash])`, the provider call is skipped.

- **Same candidate/provider rerun suppression**
  - `candidate_enrichment_status` prevents the same candidate/provider pair from being rerun unless the previous status was `error`.
  - This protects retries for the same candidate, but not new candidates representing the same paper.

- **Context-aware title cache separation**
  - Title cache keys are not naïvely shared across mismatched contexts.
  - `field_set_hash` is derived from title + DOI/PMID/arXiv + author/venue/year context.
  - Good for correctness; it also means some same-title cases will intentionally not collapse.

- **Experimental shared title payload reuse**
  - For enabled providers, one title fetch can be reused across multiple candidates while still re-evaluating match safety per candidate.
  - This is narrower than article-level dedup and still sits at provider-query level.

Relevant tests already exist:
- `tests/test_enrich_cache_semantics.py`
  - `test_enrich_candidates_dispatch_dedups_identical_title_queries`
  - `test_enrich_candidates_uses_context_aware_cache_keys_for_mismatched_title_context`
  - `test_experimental_title_payload_reuse_shares_request_without_relaxing_match`
  - cache/budget interaction regression tests

### 2) The current pipeline does **not** do article-level pre-enrich resolution against the existing library

What is missing today:

- No pre-enrich lookup against `canonical_paper` before provider fanout
- No pre-enrich lookup against existing `source_record` pools from already processed papers
- No article-level alias table that maps DOI / PMID / PMCID / arXiv / URL / Scholar cluster / normalized title key to an existing canonical paper
- No same-batch article clustering above the provider-query layer

In other words:
- current dedup is mostly **request dedup** and **post-enrich candidate dedup**,
- not **pre-enrich article dedup**.

### 3) On the fixed slice150 seed, duplicate opportunity is already large even before any new design

Artifact generated in this analysis:
- `docs/validation/day6-enrichment-duplicate-opportunity-slice150-20260429.md`

Using:
```bash
SQLITE_PATH=data/mgap_pkgB_large_slice150_seed_20260416_slice150.db \
PYTHONPATH=src python3 -m mygooglealertpapers.cli report-enrichment-plan \
  --limit 368 \
  --output docs/validation/day6-enrichment-duplicate-opportunity-slice150-20260429.md
```

Observed:
- `provider_intent_count = 1405`
- `unique_intent_count = 1149`
- `duplicate_intent_count = 256`
- `request_savings_vs_naive = 380`
- `request_savings_vs_dedup_only = 124`

Breakdown highlights:
- `crossref title`: `207 -> 171` unique (`36` duplicate intents)
- `openalex title`: `207 -> 171` unique (`36` duplicate intents)
- `semanticscholar title`: `207 -> 171` unique (`36` duplicate intents)
- `crossref doi`: `161 -> 127` unique (`34` duplicate intents)
- `openalex doi`: `161 -> 127` unique, and batching can shrink this to `3` batched requests

This proves the current corpus already contains many repeated article-level signals across mails.

### 4) If the same library DB is reused, exact query-cache reuse can already suppress a lot — sometimes all — of the repeated traffic

Ad-hoc replay analysis against an already processed library DB:

- candidate seed: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- existing processed library: `data/mgap_mainline_treat_20260422_mainline.db`
- profile shape: `openalex_batching_identifier_plus_title_core`

Observed for lane1+lane2 dispatch groups:
- `dispatch_groups_filtered = 613`
- `cache_hit_groups = 613`
- `cache_hit_intents = 755`
- exact cache-hit ratio at group level: `100%`

Interpretation:
- if the same article slice is re-run against a DB that already contains the exact provider query cache, the current cache layer can already suppress essentially all repeated provider calls.
- So the cache mechanism is real and strong.
- But this is an **upper-bound replay** against already processed data, not a fresh prospective batch.

### 5) Existing canonical-library overlap is also very large in principle

Using the same slice150 seed compared against `data/mgap_mainline_treat_20260422_mainline.db`, a hierarchical exact-match check gave:

- `doi_exact = 161`
- `pmid_exact = 5`
- `pmcid_exact = 3`
- `title_author_year = 179`
- `title_author = 10`

These tiers were counted hierarchically (first hit wins), so together they imply:
- `358 / 368` candidates could potentially be resolved from an existing canonical library under increasingly weaker rules.

Important caution:
- this is again an **upper-bound replay against an already processed corpus**, not proof that future fresh batches will always have that level of overlap.
- But it strongly supports the idea that **library-first resolution is worth building**.

### 6) The pipeline already stores strong pre-provider signals that are currently underused

Available normalized fields:
- `doi_extracted`
- `pmid_extracted`
- `pmcid_extracted`
- `arxiv_id_extracted`
- `url_canonical`
- `scholar_cluster_hint`
- `norm_title_key`
- `first_author_family`
- `year_guess`

These are enough to support a meaningful pre-enrich resolver.

---

## Inferred

### A. The real gap is not “lack of cache”; it is “lack of an article-level resolver above query cache”

Current cache answers:
- “Have I already asked **this exact provider query**?”

What the pipeline still cannot answer:
- “Have I already seen **this paper**?”
- “Is this candidate just another mail copy of an already canonicalized paper?”
- “Can I safely bypass provider fanout and directly attach this candidate to an existing paper?”

That is the missing layer.

### B. The two user-raised scenarios are related but not identical

#### Scenario 1 — same paper repeated within the current batch
Best framing:
- same-batch **candidate clustering** problem
- should be solved before provider fanout
- output should still preserve downstream semantics for all follower candidates

#### Scenario 2 — later batch repeats already validated papers from previous batches
Best framing:
- **library-first prelink** problem
- should be solved before enrich and ideally before merge
- strongest matches can bypass provider calls entirely

### C. The safest early win is not fuzzy title matching; it is exact-ID and stable-token prelinking

Strong signals:
- DOI exact
- PMID exact
- PMCID exact
- arXiv exact
- stable Scholar cluster token
- stable canonical URL token when trustworthy

Weaker signals:
- normalized title + first author + year
- normalized title + first author only

Recommendation:
- exact identifiers and stable URL/cluster tokens should be the first automatic short-circuit layer
- title-author-year should start as a **soft library hint / same-batch cluster cue**, not an immediate global auto-prelink rule

---

## Proposed plan

## Phase 0 — audit first, no behavior change

Goal:
- make duplicate opportunity visible before changing execution.

Actions:
1. keep `report-enrichment-plan` as the exact-query duplicate report
2. add a second report for **library-resolvable candidates**
3. record resolution opportunity counts by rule tier:
   - doi_exact
   - pmid_exact
   - pmcid_exact
   - arxiv_exact
   - scholar_cluster_exact
   - url_canonical_exact
   - title_author_year_exact
   - title_author_exact

Suggested output artifact:
- `docs/validation/dayX-library-resolution-opportunity-*.md`

Why first:
- this separates “there is overlap” from “this rule is safe enough to automate”.

## Phase 1 — exact library-first short-circuit (recommended first implementation)

### Behavior
Before provider enrich, attempt a high-confidence match against the existing canonical library.

Priority order:
1. `doi_exact`
2. `pmid_exact`
3. `pmcid_exact`
4. `arxiv_exact`
5. `scholar_cluster_exact`
6. `url_canonical_exact` (only where normalization is trusted)

If matched:
- directly create `candidate_paper_link`
- mark candidate as `library_prelinked`
- skip provider enrich for that candidate
- skip merge/dedup for that candidate

### Why this is the right first move
- high precision
- biggest likely query reduction per unit risk
- directly addresses the user’s second scenario
- does not require fuzzy article clustering on day 1

### Required pipeline change
`merge_metadata` currently processes every candidate lacking a merged proposal. It should also skip candidates already prelinked to a canonical paper.

---

## Phase 2 — same-batch candidate clustering above provider queries

### Behavior
Build same-batch candidate clusters before provider dispatch.

Cluster key priority:
1. DOI / PMID / PMCID / arXiv exact
2. Scholar cluster exact
3. trusted canonical URL exact
4. `norm_title_key + first_author_family + year_guess`
5. optionally `norm_title_key + first_author_family` as a soft hint only

For each cluster:
- choose a **leader candidate** with the richest metadata
- dispatch provider queries only from the leader when the cluster key is strong
- fan out leader results to follower candidates where safe

### Why this is different from current dispatch dedup
Current dedup says:
- same provider + same query key -> collapse

Clustering would say:
- these multiple candidates are probably the **same paper**, even if their provider query keys are not fully identical

That is a stronger and more useful abstraction.

### Caution
Do not start with fuzzy title-only collapse.
Start with strong deterministic keys only.

---

## Phase 3 — add a persistent article-identity alias layer

For scale, repeated SQL joins against `canonical_paper` and `source_record` will become awkward.

Recommended materialized table:

### `paper_identity_alias`
Suggested columns:
- `id`
- `paper_id`
- `alias_type`  
  (`doi`, `pmid`, `pmcid`, `arxiv`, `scholar_cluster`, `url_canonical`, `title_author_year`, `title_author`)
- `alias_key`
- `confidence`
- `source_stage` (`dedup`, `manual_review`, `library_import`, etc.)
- `created_at`
- `updated_at`

Unique key:
- `(alias_type, alias_key)` for high-confidence exact aliases

Benefits:
- fast library-first resolution
- explicit audit trail for why a candidate was prelinked
- future room for manual curation / blacklist / rollback

---

## Code blueprint

## 1) New schema / indexes

### A. `candidate_resolution_status`
Purpose:
- persist whether a candidate was resolved by cache, library prelink, same-batch cluster, or provider enrich

Suggested fields:
- `candidate_id`
- `resolution_stage` (`library_prelink`, `same_batch_cluster`, `provider_dispatch`, `cache_hit`)
- `resolution_rule` (`doi_exact`, `pmid_exact`, `cluster_exact`, etc.)
- `paper_id`
- `leader_candidate_id`
- `status`
- `evidence_json`
- timestamps

### B. `paper_identity_alias`
As above.

### C. useful indexes
On `paper_candidate_normalized`:
- `(doi_extracted)`
- `(pmid_extracted)`
- `(pmcid_extracted)`
- `(arxiv_id_extracted)`
- `(scholar_cluster_hint)`
- `(url_canonical)`
- `(norm_title_key, first_author_family, year_guess)`
- `(norm_title_key, first_author_family)`

On `source_record`:
- `(source_name, external_id)`
- `(doi)`
- `(pmid)`
- `(pmcid)`
- `(url)`

## 2) New repository helpers

Suggested additions in `src/mygooglealertpapers/db/repository.py`:

- `find_canonical_by_exact_ids(...)`
- `find_canonical_by_cluster_or_url(...)`
- `find_canonical_by_title_author_year(...)`
- `upsert_candidate_resolution_status(...)`
- `link_candidate_to_existing_paper(...)`
- `build_paper_identity_aliases_for_paper(...)`
- `refresh_identity_aliases(...)`

## 3) New pipeline module

Suggested new file:
- `src/mygooglealertpapers/pipeline/candidate_resolution.py`

Suggested entry points:
- `resolve_candidates_against_library(settings, limit)`
- `build_same_batch_candidate_clusters(settings, limit)`
- `choose_cluster_leader(cluster_rows)`

## 4) Integrate into current flow

### Recommended order
1. `normalize-candidates`
2. **new: `resolve-candidates`**
3. `enrich-candidates`
4. `merge-metadata`
5. `dedup-candidates`
6. `enrich-paper-oa`

### Minimal integration alternative
If adding a new CLI stage feels too disruptive at first:
- integrate the resolver as a prepass at the start of `enrich_candidates(...)`
- but still persist explicit resolution status so the behavior is inspectable

## 5) Merge / dedup adjustments

`merge_metadata` should exclude candidates already resolved via exact library prelink.

For example, its candidate-selection query should skip candidates that already have:
- `candidate_paper_link`, or
- `candidate_resolution_status.status in ('library_prelinked', 'cluster_follower_prelinked')`

This avoids wasting merge work on candidates whose target canonical paper is already known.

---

## Safety policy

### Safe for automatic short-circuit now
- DOI exact
- PMID exact
- PMCID exact
- arXiv exact
- trusted Scholar cluster exact
- trusted canonical URL exact

### Do not auto-short-circuit globally yet
- title only
- title + venue only
- title + author only without further validation

### Start as soft hints
- `norm_title_key + first_author_family + year_guess`
- `norm_title_key + first_author_family`

These are useful for:
- same-batch clustering
- ranking enrich leader candidates
- building operator review queues

But they should not be the first production library-prelink rule.

---

## Validation plan

## A. Exact-library prelink replay

Run on a fixed seed DB against a completed library DB.

Metrics:
- prelinked candidate count by rule
- provider_intent_count before/after
- dispatch_request_count before/after
- canonical_paper_count delta
- merge_review_queue_count delta
- false-prelink audit sample size

Success criterion:
- large request reduction with zero canonical drift on exact-ID rules

## B. Same-batch cluster replay

Construct a slice with repeated candidates for the same DOI / cluster / URL.

Metrics:
- cluster count
- leader/follower ratio
- provider dispatch count reduction
- source_record fanout correctness
- canonical output drift

## C. Guardrail tests to add

1. exact DOI prelink to existing canonical -> **0 provider requests**
2. exact PMID prelink -> **0 provider requests**
3. Scholar cluster exact hit -> **0 provider requests** if mapped to paper alias
4. title-author-year soft hit -> **must not auto-prelink** in v1
5. same-batch 4-candidate DOI duplicate -> one leader dispatch, all followers linked/fanned out correctly
6. already cached provider query + library prelink coexistence -> deterministic priority order

---

## Recommendation

### What I would build first

**First implementation target:** exact library-first short-circuit for already known papers.

Reason:
- highest precision
- directly addresses the largest obvious waste in later large-batch ingestion
- easier to validate than fuzzy same-batch clustering
- composes well with the current query-cache and lane architecture

### Then build second

After exact library prelink is stable:
- add same-batch candidate clustering using strong deterministic keys
- keep fuzzy title-based grouping out of automatic prelink until audited

---

## Bottom line

Yes — there is a real path to removing much more duplicate provider traffic.

But the right abstraction is **not just more cache**.
It is a new layer above cache:

- **query-level reuse** (already partly present)
- **article-level same-batch clustering** (missing)
- **library-first canonical prelink** (missing, and likely the highest-value next step)

The current project already has most of the raw signals needed.
What it lacks is an explicit resolver that turns those signals into a pre-enrich decision.
