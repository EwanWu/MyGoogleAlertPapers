# Package 2 targeted validation

## Date
2026-04-03

## Scope
Validate two aspects after Package 2 first-pass cache hardening:
1. cache uniqueness and rerun stability on a fresh small real-mailbox slice
2. structured cache/status handling for error-path semantics in a controlled unit-style scenario

---

## Validation A: fresh 10-mail `issac` slice

### Test database
- `data/mgap_issac_10_cache_test.db`

### Workflow
- init-db
- scan-mailbox --limit 10 --unseen-only
- parse-mails --limit 50
- normalize-candidates --limit 100
- enrich-candidates --limit 100
- rerun enrich-candidates --limit 100

### Observed results
- candidate count after normalization: 14
- planned provider intents: 42
- duplicate cache keys before rerun: 0
- duplicate cache keys after rerun: 0
- cache row count before rerun: 33
- cache row count after rerun: 33
- rerun latency: ~0.12 s
- structured no-match cache rows observed: yes

### Interpretation
This supports the first-pass Package 2 claim that:
- cache rows no longer accumulate duplicate `(provider, query_type, query_key)` entries on the tested slice
- rerun remains stable and does not inflate cache size when no provider work remains

---

## Validation B: controlled error-path semantics check

### Test database
- `data/mgap_cache_errorpath_unit.db`

### Setup
A minimal DB was created and populated with:
- one provider-level status row for `cand_err` / `pubmed`
- one cached serialized `EnrichmentRecord` with `matched=False`
- raw payload indicating `status=error` and a synthetic error string

### Observed results
- cache row present for (`pubmed`, `title`, `Test Title`)
- cached payload decoded back into `EnrichmentRecord`
- decoded record remained `matched=False`
- provider status row remained `('pubmed', 'error', 'synthetic failure')`

### Interpretation
This confirms that the current Package 2 structure can represent error semantics coherently across:
- query cache payload
- decoded enrichment record
- provider-level status row

### Limitation
This was a controlled synthetic validation, not a live provider-network failure during a full enrichment run.
A future real-run failure case would still be useful for end-to-end confirmation.

---

## Conclusion
Package 2 first pass is effective enough to proceed:
- cache identity is materially stronger
- rerun stability is preserved
- duplicate-key inflation was not observed on the tested fresh slice
- structured error semantics are representable in the current model

This is sufficient to move on to Package 3 correctness work, while keeping one future validation item open:
- end-to-end real provider error-path exercise during a live run
