# Day13 decision: should truncated-title salvage be integrated into the current default? (2026-05-02)

## Short answer
**Yes — keep it in the current default code path.**

But the justification should be:
- **semantic / routing improvement**
- **not** live wall-time improvement on the rerun

Also, this is **not** a YAML-profile promotion decision in the narrow sense. The patch lives in:
- `src/mygooglealertpapers/enrich/base.py`

So the real question is:
> should the current mainline default runtime keep this acceptance rule enabled in the shared `accept_result(...)` path?

My answer is **yes**.

---

## What changed
Patch added a narrow salvage branch in `accept_result(...)`:
- title is below normal acceptance threshold but still `sim >= 0.84`
- source title looks truncated (`. .`, `…`, or trailing `...`)
- `first_author_matches(...) is True`
- `venue_hint_matches(...) is True`
- no year conflict

This is intentionally much narrower than a generic similarity-threshold relaxation.

---

## Where the current default actually binds
Current mainline default profile remains:
- builtin runtime default in `src/mygooglealertpapers/config.py`
- baseline helper default in `src/mygooglealertpapers/benchmark_baseline.py`
- profile path:
  `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml`

Important detail:
- the current default runtime uses only
  - `identifier_fastpath`
  - `title_core`
- biomedical fallback lanes are disabled in the default profile

Therefore, in practice, this patch mainly affects the current default's title-core acceptance path, especially OpenAlex/Crossref title results, rather than broadly re-opening fallback behavior.

---

## Evidence base
### 1. Targeted tests passed
Artifact:
- `tests/test_title_normalization.py`

Command:
```bash
pytest -q tests/test_title_normalization.py
```

Added coverage includes:
- truncation detector
- positive salvage case
- negative case when author / venue support is missing

### 2. Medium60 result was narrow and clean
Treatment effect vs the retained URL-identity DOI recovery baseline:
- `matched_source_record_count 87 -> 88`
- `dispatch_request_count 73 -> 72`
- one concrete rescue:
  - `cand_89794a7e8282a9b7`

Interpretation:
- not broad behavior drift
- exactly the kind of residual-tail salvage this patch was designed for

### 3. Large-fixed rerun confirmed it was not a one-off
Completed validation memo:
- `docs/validation/day13-large-fixed-truncated-title-salvage-rerun-validation-20260502.md`

Durable large-fixed deltas vs `day13_large_fixed_url_identity_doi_20260502`:
- `matched_source_record_count 543 -> 547` `(+4)`
- `dispatch_request_count 407 -> 403` `(-4)`
- `title_lane_request_count 253 -> 249` `(-4)`
- `merge_review_queue_count 2 -> 2`
- `severe_doi_conflict_count 2 -> 2`

Four stable rescued candidates:
- `cand_20f8d5e121253c15`
- `cand_89794a7e8282a9b7`
- `cand_ba178f768ff6ab00`
- `cand_ebc2f5c1d2ce68ca`

These are the strongest integration argument.

---

## What the patch does **not** prove
### It does not prove a stable runtime speedup
Live rerun wall time moved the wrong way:
- `total_batch_duration_ms 665839 -> 724093`
- `total_provider_latency_ms 654373 -> 712795`

But request counts improved in the expected direction.

Interpretation:
- provider/network drift dominated realized latency on this rerun
- so runtime should be treated as **noisy / inconclusive**
- the retention case should be made on semantic and routing grounds, not on this rerun's wall-time

### It does not justify broad threshold relaxation
This patch should **not** be generalized into:
- lower global title thresholds
- venue-veto removal
- wide acceptance of `sim 0.84+`
- broad non-OpenAlex / fallback loosening

The only reason it is acceptable is that the rule is jointly constrained by:
- truncation signal
- author agreement
- venue agreement
- no year conflict

---

## Important caution: one non-durable live-drift signal
In the rerun there was an extra `canonical +1`, but this should **not** be used as the core reason to promote the patch.

Reason:
- candidate `cand_8994637b2b637b39` appears to reflect live provider drift rather than the truncation-salvage mechanism itself
- rerun produced a new low-confidence normalized-only proposal unrelated to the four stable truncated-title rescues

So the durable evidence should be restricted to:
- `matched_source_record +4`
- `dispatch_request_count -4`
- `title_lane_request_count -4`
- no review/conflict regression

---

## Decision
### Recommendation
**Keep truncated-title salvage in the current default code path.**

### Why
Because it satisfies all of the following:
1. **Narrow mechanism** — not a broad accept-anything relaxation
2. **Stable rescue signal** — four clean large-fixed rescues after the medium60 proof case
3. **No observed safety regression** in current default evaluation:
   - no review-queue growth
   - no DOI-conflict growth
4. **Routing benefit** — fewer residual title requests in the exact path we are trying to harden

### What “integrate into current default” means operationally
- **No profile YAML change is required**
- The correct action is simply to **retain this code-level rule in `accept_result(...)`** as part of the default mainline runtime

---

## Final posture
### Known
- current default profile is already the promoted day13 mainline profile
- this patch sits below that profile at the shared acceptance layer
- medium60 and large-fixed both show narrow positive signal
- no review/conflict regression was observed

### Inferred
- for the current default runtime, this patch is safe enough to keep because the active path is title-core only and the acceptance rule is tightly constrained

### Speculative
- if a future profile re-enables broader fallback lanes, this rule could touch a wider provider surface than what was exercised here; if that happens, it may deserve a fresh fallback-specific audit

---

## Recommendation to Ewan
If the decision point is simply:
> keep or revert the truncated-title salvage patch in current mainline default?

My recommendation is:
> **keep it**.

But describe it as a **precision-preserving residual-tail acceptance fix**, not as a runtime-speed optimization.
