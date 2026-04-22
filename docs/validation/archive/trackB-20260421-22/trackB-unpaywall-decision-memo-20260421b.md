# Track B Unpaywall Decision Memo

**Run tag:** 20260421b
**Date:** 2026-04-22
**Status:** Experiment complete — do not promote as-is

---

## Summary numbers

| Metric | Control (v2) | Treatment (v2+Unpaywall) | Delta |
|---|---|---|---|
| canonical_paper_count | 292 | 290 | **-2** |
| merge_review_queue_count | 4 | 7 | **+3** |
| normalized_only_fallback | 35 | 45 | +10 |
| matched_source_record | 781 | 724 | -57 |
| unpaywall matched | — | 140/161 | — |

---

## What happened

### The `url` field bug (found mid-analysis)
Unpaywall correctly fetched `best_oa_location.url` but **did not write it to the `url` field** of `EnrichmentRecord` — the field was returning `None` for all records. Root cause: `best_oa_url = payload.get("best_oa_url")` at the top-level was returning `None` because Unpaywall's API puts the OA PDF URL under `best_oa_location.url`, not at the top level. Fixed in `unpaywall.py` to `best_oa_location = payload.get("best_oa_location") or {}; best_oa_url = best_oa_location.get("url")`. However, this fix was applied **after** this replay run, so the treatment run has 0 OA URLs despite Unpaywall having them.

### Canonical paper overlap (same title+doi+authors)
- **281 papers** are canonical in both control and treatment — fully stable
- **11 papers** lost canonical standing in treatment
- **9 papers** gained canonical standing in treatment
- **Net -2** canonical papers

### 15 candidates had different preferred metadata
15 candidates merged differently (different preferred_title, preferred_doi, or preferred_authors) between control and treatment. This drove all 11 losses and 9 gains.

**Root cause of the merge differences is mixed:**
1. **Unpaywall's source priority = 0** — by design it should never override bibliographic authority, but it may have influenced merge tie-breaking in edge cases
2. **Live provider re-run variability** — the treatment arm ran full `enrich` against live APIs (Crossref, OpenAlex, etc.), so provider responses could differ from the control arm which re-used the v2 source_records DB. This is the more likely cause of the DOI conflicts and metadata differences.

### New merge_review_queue candidates (3 new)
- `cand_3a6f282d35458d76` — severe_conflict:doi,venue (same candidate ID as `cand_380600011de29f8b`)
- `cand_380600011de29f8b` — severe_conflict:doi,venue
- `cand_717d757a4fb5f19e` — severe_conflict:doi

These 3 appear to be candidates where live Crossref/OpenAlex returned slightly different metadata than what was cached in the v2 baseline DB, pushing them into conflict.

### normalized_only_fallback +10 increase
From 35 to 45 — 10 additional candidates fell through to the `normalized_only` fallback path. This suggests Unpaywall may be introducing unmatched source_records that displace previously-matched records in the merge, pushing more candidates into the fallback path.

---

## Is Unpaywall the cause of canonical loss?

**Partially — but not directly.** The evidence:

1. Unpaywall has `SOURCE_PRIORITY = 0` so it should never win bibliographic field selection
2. The 15 merge-difference candidates all had provider responses from Crossref/OpenAlex/PubMed/etc. in both arms — Unpaywall only fires on DOI-positive candidates
3. The **live enrich re-run** (not Unpaywall directly) is the more likely driver of the merge differences — live API responses vary between runs
4. However, Unpaywall's source_records may have displaced other providers' source_records in the merge, contributing to the fallback count increase

**Unpaywall's OA URL value cannot be assessed yet** — the `url` field bug means the actual OA URL coverage is unknown. Once the bug is fixed and replay re-run, OA URL fill rate should be measurable.

---

## Recommendations

### 1. Fix + Re-run is required before evaluation
The `url` field bug means this replay does not reflect real Unpaywall OA URL coverage. Fix the bug, then re-run the treatment arm.

### 2. For the re-run: compare `--stages merge dedup` only
To isolate Unpaywall's effect from live provider variability, the treatment arm should reuse source_records from a fresh v2 baseline (via `--reuse-source-records-from`) and run only `merge dedup` stages. This eliminates live API variability.

### 3. If after fix+re-run canonical still drops
Unpaywall should be downgraded to a **pure reporting-only provider** — add it to merge only when it provides a URL that no other provider supplies, and only as a tie-breaker for OA status reporting, not for any bibliographic field.

### 4. If canonical is flat after fix+re-run
Unpaywall can be used as an opt-in OA-enhancement provider. Primary value: `is_oa`, `oa_status`, `best_oa_location.url` for OA coverage reporting.

---

## Code changes made this session

1. **`unpaywall.py` — proxy support added:** `_get_proxy_opener()` reads `http_proxy/https_proxy` from environment so Unpaywall calls work behind the corporate proxy
2. **`unpaywall.py` — URL field bug fixed:** Changed `best_oa_url = payload.get("best_oa_url")` to read from `best_oa_location.url` — this fix applies to all future runs
3. **`conditional_sources_v2_unpaywall.yaml` — YAML syntax fix:** Removed multi-line `>` string that was causing ScannerError and hiding the Unpaywall provider rule

---

## Next step

Fix applied. Re-run Track B treatment arm with:
- `--stages merge dedup` only (reuse v2 source_records)
- Or fix the `url` field and do a full `enrich merge dedup` re-run

Then measure:
1. OA URL fill rate: `SELECT COUNT(*) FROM source_record WHERE source_name='unpaywall' AND url IS NOT NULL`
2. Canonical delta with isolated Unpaywall effect
3. Whether the review queue growth stops
