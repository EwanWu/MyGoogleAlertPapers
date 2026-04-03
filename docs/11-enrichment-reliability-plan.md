# Enrichment Reliability Plan

## Purpose
Turn the current enrichment stage from a runnable prototype into a reliable, resumable, conservative subsystem suitable for repeated validation runs and later scale-up.

This document is based on:
- the existing implementation state in `src/`
- prior 100-email validation artifacts
- a fresh 30-email run on the `issac` test mailbox performed on 2026-04-03

---

## 1. Current empirical findings

### 30-email `issac` recheck summary
- scanned mails: 30
- detected Scholar mails: 16
- extracted candidates: 59
- DOI extracted during normalization: 34
- enrichment source records: 177
- matched source records: 134
- merged proposals: 53
- merged proposals with conflicts: 34
- canonical papers after dedup scaffold: 47

### Runtime summary
- scan: ~38.2 s
- extract: ~0.06 s
- normalize: ~0.005 s
- merge: ~0.01 s
- dedup: ~0.004 s
- enrichment: ~342.2 s

### Provider latency summary
- OpenAlex: ~1.0 s/event average
- Crossref: ~1.5 s/event average
- PubMed: ~2.6 s/event average

### Immediate interpretation
1. The end-to-end pipeline is functional on real mailbox data.
2. Enrichment is the dominant runtime bottleneck by a large margin.
3. Conflict exposure remains high and is still the main threat to conservative canonicalization.
4. Cache exists and helps, but resumability is still too coarse.

---

## 2. Main problems identified

### P0. Enrichment completion is tracked too coarsely
Current `enrich_candidates` candidate selection treats a candidate as already enriched when *any* `source_record` exists.

This means a partial run can leave a candidate in an incomplete state:
- one provider succeeded
- one provider failed
- one provider never ran due to interruption

On rerun, that candidate may be skipped entirely.

### P0. Query cache exists but does not enforce strong uniqueness
Observed duplicate cache keys in `query_cache` for the same:
- provider
- query_type
- query_key

This indicates that cache is being used, but not yet hardened as the single authoritative lookup memory for provider requests.

### P0. High merge-conflict rate still threatens conservative canonical records
The 30-email run produced conflicts in about 64% of merged proposals.

Current conflict handling is useful diagnostically but not yet discriminative enough for safe canonicalization.

### P1. Title-based provider fallback remains too permissive
Several conflict examples indicate that title search can still attach metadata from the wrong paper, especially wrong DOI or mismatched legacy records.

### P1. Severe conflicts and superficial string differences are not sufficiently separated
Examples that should not carry equal weight:
- title punctuation differences
- venue capitalization variants
- conflicting DOI values
- conflicting PMID values

### P1. HTML/tag residue still leaks into normalized titles in some cases
Examples include embedded formatting remnants such as `<i>` or `<scp>` artifacts entering downstream merge logic.

### P2. There is no explicit provider-level enrichment status table
The system currently infers progress indirectly from `source_record` presence and cache rows, which is not robust enough for controlled reruns, retries, or failure analysis.

---

## 3. Priority order agreed for the next implementation cycle

### Highest priority: correctness + resumability
1. provider-level enrichment progress tracking
2. true checkpoint/resume behavior for interrupted enrichment runs
3. stricter title-fallback acceptance
4. severe-conflict protection before canonicalization

### Second priority: request reduction and cache hardening
5. normalize and deduplicate cache keys
6. make query cache authoritative for repeated provider lookups
7. avoid duplicate provider requests within and across runs
8. formalize handling of cached `no_match` and cached `error` states

### Third priority: judgment-system improvements
9. strengthen title and venue normalization
10. remove HTML residue earlier
11. replace crude conflict-count confidence with rule-based scoring
12. better separate version-link behavior from true metadata conflict

---

## 4. Concrete modification plan before code changes

## 4.1 Provider-level enrichment progress model

### Proposed new table
`candidate_enrichment_status`

Suggested fields:
- id
- candidate_id
- provider
- status (`pending`, `ok`, `no_match`, `error`, `skipped`)
- query_type
- query_key
- source_record_id
- cache_hit
- attempt_count
- last_started_at
- last_finished_at
- latency_ms
- error_summary
- batch_run_id
- updated_at

### Purpose
This table becomes the authoritative provider-level progress ledger.

It answers questions such as:
- Has this candidate been queried against PubMed yet?
- Did OpenAlex succeed or fail?
- Is Crossref pending because the process was interrupted?
- Was a result produced from cache or external request?

### Implementation behavior
For each candidate and provider:
1. compute normalized query intent
2. write or update status row as `pending`
3. attempt cache lookup
4. if cache hit, update status row accordingly
5. if external request runs, finalize row as `ok`, `no_match`, or `error`
6. link successful rows to inserted `source_record`

### Resume rule
A rerun should select work by provider-level status, not by candidate-level existence of any source record.

Initial rerun logic:
- run providers with no status row
- retry provider rows with `error` only if explicitly allowed or after cooldown
- do not re-run providers with `ok` or `no_match` unless forced

---

## 4.2 Query-cache hardening

### Proposed cache contract
`query_cache` should represent normalized provider-query results keyed by:
- provider
- query_type
- query_key

### Required changes
1. normalize cache keys before every lookup/write
2. add a unique index on `(provider, query_type, query_key)`
3. replace append-only insertion with upsert behavior
4. explicitly store result class:
   - matched payload
   - no-match payload
   - error payload
5. optionally store freshness metadata for future invalidation policy

### Query-key normalization rules
#### DOI
- lowercase
- stripped of `https://doi.org/`
- stripped of known suffix artifacts where appropriate

#### PMID / PMCID
- canonical stripped form only

#### Title
- use a stronger normalized title key rather than raw title string

### Immediate expected benefit
- fewer duplicate cache rows
- fewer repeated external requests
- more reliable reruns and measurements

---

## 4.3 Enrichment selection and resume algorithm

### Current weak point
Selection is currently candidate-level and only checks for absence of any `source_record`.

### Proposed replacement
For each candidate, build a provider worklist:
- PubMed if PMID exists or biomedical title path is allowed
- Crossref if DOI exists or title path is allowed
- OpenAlex if DOI exists or title path is allowed

Then, per provider:
- skip if status=`ok`
- skip if status=`no_match` unless force rerun
- retry if status=`error` and retry policy permits
- run if no status exists

### Partial completion safety
If a run is interrupted after Crossref succeeds but before PubMed runs, rerun should continue with only the missing provider work, not reprocess the whole candidate.

---

## 4.4 Title-fallback acceptance tightening

### Current issue
Title fallback still sometimes accepts wrong records, especially when provider top hit is semantically related but not the same paper.

### Proposed policy tightening
For title-based acceptance, require stronger agreement from a combination of:
- title similarity
- year compatibility
- first-author family compatibility
- venue compatibility when present

### Additional conservative rules
- if DOI from provider conflicts with a DOI-like signal already extracted from candidate, downgrade sharply
- if title match is moderate but author/year do not support it, reject
- for PubMed title fallback, only run on biomedical-leaning candidates or strong title evidence
- consider requiring a stronger threshold for title-only acceptance than currently used

---

## 4.5 Merge conflict grading and canonicalization guardrail

### Proposed conflict grades
#### Grade A: benign formatting conflict
Examples:
- punctuation
- capitalization
- minor Unicode dash differences
- trivial venue formatting variants

#### Grade B: moderate metadata divergence
Examples:
- year off by one in version-like situations
- venue family mismatch without DOI contradiction
- title truncation versus full title

#### Grade C: severe conflict
Examples:
- DOI disagreement
- PMID disagreement
- clearly different semantic title content
- provider outputs pointing to different conceptual works

### Canonicalization rule
If a merged proposal contains a Grade C conflict, it should not directly populate a high-confidence canonical paper.

Instead it should either:
- remain provisional
- be linked with reduced trust
- or require a stricter merge confidence pathway

This aligns with the agreed “conservative main store” policy.

---

## 4.6 Text-cleaning improvements

### Proposed additions
- strip HTML tags before title normalization if residual markup remains
- normalize special punctuation earlier
- preserve display text for provenance but use cleaner normalized forms for matching

### Goal
Reduce downstream false conflict counts caused by formatting artifacts rather than true metadata disagreement.

---

## 5. Suggested implementation sequence

### Package 1: resumability foundation
- add `candidate_enrichment_status`
- update schema and repository helpers
- change enrichment candidate selection to provider-level status logic
- support partial rerun safely

### Package 2: cache hardening
- normalize query keys centrally
- add unique index and upsert logic
- preserve `matched` / `no_match` / `error` payload classes consistently

### Package 3: stricter acceptance and merge grading
- tighten title-based acceptance
- classify conflicts into benign/moderate/severe
- block severe-conflict proposals from confident canonicalization

### Package 4: normalization cleanup
- strengthen title cleanup
- strip HTML residue earlier
- normalize venue/title conflict comparison further

---

## 6. Validation plan after implementation

### Immediate validation slice
Re-run a fresh 30-email `issac` batch in a new database.

### Required outputs to compare with baseline
- total runtime
- enrichment runtime
- provider latency summary
- cache-hit counts
- duplicate cache-key count
- merged proposal conflict rate
- severe-conflict rate
- number of candidates with partial provider completion after forced interruption test
- rerun time after interruption

### Success indicators
1. duplicate provider requests decrease materially
2. interrupted runs resume missing provider work correctly
3. severe DOI/PMID conflict examples decrease
4. canonical layer receives fewer clearly wrong DOI assignments
5. total enrichment wall-clock cost improves without sacrificing conservative behavior

---

## 7. Decision summary
The next coding cycle should not primarily add new providers or broaden scope.

It should first make enrichment:
- resumable
- cache-authoritative
- less repetitive
- more conservative in title-based acceptance
- safer for canonical paper construction

This is the highest-value path for turning the current prototype into a reliable literature-ingestion substrate.
