# Package 2 Spec: Authoritative Query Cache Hardening

## Purpose
Build on Package 1 provider-level resumability by making `query_cache` more canonical, less duplicative, and more authoritative for repeated provider lookups.

Package 2 focuses on reducing repeated external provider requests and making cache semantics explicit enough to support reliable reruns and future scale-up.

---

## 1. Problems targeted

### 1.1 Duplicate cache rows
Earlier validation showed repeated cache rows for the same:
- provider
- query_type
- query_key

This weakens cache authority and makes request-reduction metrics harder to trust.

### 1.2 Query-key normalization is inconsistent
Current enrichment paths normalize some keys (for example DOI in some OpenAlex paths) but not others in a unified way.

### 1.3 Cached result classes are not explicit enough
The cache currently stores serialized enrichment payloads, but repeated execution benefits from treating these result classes explicitly:
- matched result
- no-match result
- error result

### 1.4 Provider-level status and cache are not yet fully aligned
Package 1 introduced provider-level status. Package 2 should make cache behavior work more predictably with that status model.

---

## 2. Package-2 goals

1. Enforce uniqueness of cache rows by `(provider, query_type, query_key)`.
2. Normalize query keys through a shared policy before lookup and write.
3. Replace append-only cache insertion with upsert behavior.
4. Persist cache payloads for matched, no-match, and error outcomes in a consistent way.
5. Reduce repeated provider calls in repeated validation runs.

### Non-goals
- no full cache invalidation TTL system yet
- no provider-specific freshness policy yet
- no merge/canonical correctness redesign yet
- no checkpoint durability redesign yet

---

## 3. Proposed schema adjustment

## 3.1 Unique index for cache
Add a unique index on:
- `(provider, query_type, query_key)`

This turns `query_cache` into a one-row-per-normalized-query store.

## 3.2 No required table split yet
Package 2 can keep the current `response_json` column instead of introducing a more complex cache schema.

---

## 4. Canonical query-key policy

## 4.1 DOI
- lowercase
- strip whitespace
- strip `https://doi.org/` prefix if present
- reuse DOI cleanup logic already introduced in normalization path where applicable

## 4.2 PMID / PMCID
- trimmed canonical literal form only

## 4.3 Title
- trimmed normalized title string for now
- future package may strengthen this into a dedicated title-key policy if needed

## 4.4 Batch DOI handling
For OpenAlex DOI batch use:
- cache rows should still be keyed by provider=`openalex`, query_type=`doi`, query_key=`<normalized doi>`
- batch retrieval is only a transport optimization; the cache identity should remain per DOI query

---

## 5. Cache result classes

The cache should store serialized `EnrichmentRecord` payloads consistently for these outcomes:

### matched
- `matched=True`
- includes provider payload and identifiers where available

### no_match
- `matched=False`
- includes minimal structured payload indicating query intent and no-match outcome

### error
- `matched=False`
- includes minimal structured payload capturing error summary

Package 2 should make it possible for reruns to distinguish these cases from cached payload content.

---

## 6. Repository behavior changes

## 6.1 Lookup
`get_query_cache(...)` remains, but should assume keys are already canonicalized.

## 6.2 Write
`put_query_cache(...)` should become upsert-based so the latest normalized result replaces the prior row rather than creating duplicates.

Recommended SQLite behavior:
- `INSERT ... ON CONFLICT(provider, query_type, query_key) DO UPDATE SET ...`

---

## 7. Pipeline behavior changes

## 7.1 Shared key normalization
Enrichment should use one shared canonical key function before:
- cache lookup
- status recording
- cache write

## 7.2 Cache writes for no-match and error outcomes
When a provider returns no match or errors in a recoverable way:
- write a consistent cache payload
- align status update with that payload class

## 7.3 Expected benefit
Repeated runs should show:
- fewer duplicate cache rows
- more predictable cache-hit counts
- less repeated provider traffic

---

## 8. Validation plan

Use a fresh small `issac` validation DB.

Measure before/after Package 2 on repeated runs:
- number of cache rows
- number of duplicate cache keys
- cache-hit counts
- total enrichment runtime on rerun
- provider request counts on rerun

### Success criteria
1. duplicate cache-key count drops to zero for the new run
2. repeated runs rely on upserted canonical cache rows rather than accumulating duplicates
3. rerun latency remains very low when no provider work is needed
4. external requests decrease for repeated query patterns within the run and across reruns

### Initial validation status (2026-04-03 night)
Validated on a fresh 10-mail `issac` slice:
- duplicate cache-key count was `0` after the run
- duplicate cache-key count remained `0` after rerun
- cache row count remained stable across rerun (`33 -> 33`)
- rerun remained fast (`~0.12 s`) when provider-level status already indicated no work
- structured `no_match` payloads were observed in cache rows

Not yet fully validated:
- explicit provider error-path behavior has code support for structured cached error payloads, but a real small-slice run has not yet exercised that path materially
- title-key normalization is still intentionally conservative and may need strengthening in a later package

---

## 9. Decision summary
Package 2 is the next practical step after provider-level resumability.

Its first pass appears effective: the cache no longer accumulates duplicate rows on the tested slice, and rerun behavior remains stable. This should make the existing cache trustworthy enough to support larger validation slices before moving on to deeper correctness work such as title-fallback tightening and merge conflict grading.
