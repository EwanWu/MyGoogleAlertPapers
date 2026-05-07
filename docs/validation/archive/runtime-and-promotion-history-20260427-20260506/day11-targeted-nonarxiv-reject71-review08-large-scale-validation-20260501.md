# Day11 targeted non-arXiv reject71 + review08: large-scale stable replay validation

## Objective
Turn the day11 `targeted_nonarxiv_review08` truth-audit result into a more operational policy candidate:

- **reject** the strongest non-arXiv post-openalex residual normalized-only fallback mismatches at `<= 0.71`
- **review** only the remaining borderline subgroup at `(0.71, 0.80]`

This is intended to reduce known false-positive canonicalizations without reopening a broad review queue.

## Code / profile artifacts
- Merge logic: `src/mygooglealertpapers/pipeline/merge.py`
- Tests: `tests/test_policy_and_merge_fallback.py`
- New profile: `config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08.yaml`

## Deterministic rule
Within the subgroup:
- normalized-only fallback
- `post_openalex_status = openalex_title_unmatched`
- `title_lane_subreason = url_canonical_only`
- **non-arXiv** (`arxiv_id_extracted` missing)
- not same-batch cluster leader/follower exception

apply:
- `<= 0.71` → `reject`
- `(0.71, 0.80]` → `review`

## Verification before replay
### Tests passed
```bash
PYTHONPATH=src python3 -m pytest tests/test_policy_and_merge_fallback.py -q
PYTHONPATH=src python3 -m pytest tests/test_post_openalex_residual_audit.py tests/test_fallback_author_blob_identifier_aware.py -q
```

## Replay setup
All runs reused existing donor `source_record` state and reran **merge + dedup only**.
No provider replay, no new enrich.

### Slices
1. `large_fixed`
   - source: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
   - donor: `data/benchmark/day11_final_promotion_gate_large_fixed_control_20260501.db`
   - output: `data/benchmark/day11_large_fixed_targeted_nonarxiv_reject71_review08_20260501.db`
   - report: `docs/validation/day11-large-fixed-targeted-nonarxiv-reject71-review08-20260501.json`

2. `fresh30`
   - source: `data/mgap_fresh30_20260410.db`
   - donor: `data/benchmark/day11_final_promotion_gate_fresh30_control_20260501.db`
   - output: `data/benchmark/day11_fresh30_targeted_nonarxiv_reject71_review08_20260501.db`
   - report: `docs/validation/day11-fresh30-targeted-nonarxiv-reject71-review08-20260501.json`

3. `pkg3_guardrail100`
   - source: `data/mgap_pkg3_guardrail_100.db`
   - donor: `data/benchmark/day11_final_promotion_gate_pkg3_guardrail100_control_20260501.db`
   - output: `data/benchmark/day11_pkg3_guardrail100_targeted_nonarxiv_reject71_review08_20260501.db`
   - report: `docs/validation/day11-pkg3-guardrail100-targeted-nonarxiv-reject71-review08-20260501.json`

4. `issac100`
   - source: `data/mgap_issac_100.db`
   - donor: `data/benchmark/day11_final_promotion_gate_issac100_control_20260501.db`
   - output: `data/benchmark/day11_issac100_targeted_nonarxiv_reject71_review08_20260501.db`
   - report: `docs/validation/day11-issac100-targeted-nonarxiv-reject71-review08-20260501.json`

### Residual audit exports
- `docs/validation/day11-large-fixed-targeted-nonarxiv-reject71-review08-audit-20260501.csv`
- `docs/validation/day11-fresh30-targeted-nonarxiv-reject71-review08-audit-20260501.csv`
- `docs/validation/day11-pkg3-guardrail100-targeted-nonarxiv-reject71-review08-audit-20260501.csv`
- `docs/validation/day11-issac100-targeted-nonarxiv-reject71-review08-audit-20260501.csv`

## Results

### Per-slice metric deltas vs current control
| slice | canonical papers | review queue | normalized-only fallback proposals | merged proposals |
|---|---:|---:|---:|---:|
| `large_fixed` | `292 -> 283` (`-9`) | `2 -> 2` (`0`) | `46 -> 37` (`-9`) | `367 -> 358` (`-9`) |
| `fresh30` | `75 -> 72` (`-3`) | `0 -> 0` (`0`) | `23 -> 20` (`-3`) | `95 -> 92` (`-3`) |
| `pkg3_guardrail100` | `203 -> 195` (`-8`) | `2 -> 2` (`0`) | `41 -> 33` (`-8`) | `248 -> 240` (`-8`) |
| `issac100` | `213 -> 207` (`-6`) | `3 -> 4` (`+1`) | `31 -> 26` (`-5`) | `243 -> 238` (`-5`) |

### Aggregate delta across 4 slices
- canonical papers: `783 -> 757` (`-26`)
- review queue: `7 -> 8` (`+1`)
- normalized-only fallback proposals: `141 -> 116` (`-25`)
- merged proposals: `953 -> 928` (`-25`)
- matched source records: unchanged (`1322 -> 1322`)

## Changed-case concentration
Only **10 unique candidates** changed across all four slices:
- `cand_03bde6287d0d1683`
- `cand_054270b0fef2b17a`
- `cand_3c0daf67a3c4f756`
- `cand_505b2326b7b8f0e5`
- `cand_693adeec78169f65`
- `cand_8c0fcffbabdce4e6`
- `cand_cc340e92866d3360`
- `cand_d64f1ad2ee228fa9`
- `cand_e4783c70fe9603a2`
- `cand_f241c280253095ad`

### Important concentration fact
- **9 / 10** unique changed candidates are already inside the day11 truth-audited bad-match set.
- The only new unique candidate is **`cand_f241c280253095ad`**, and it was **not rejected**; it moved to **review**.

## Borderline case retained in review
### `cand_f241c280253095ad`
- `norm_title`: `Long-Term Outcomes of Left Bundle-Branch Pacing vs Biventricular Pacing in Heart Failure: The HeartSync-LBBP Randomized Clinical Trial`
- `crossref_title`: `Long-Term Outcomes of Left Bundle-Branch Pacing vs Biventricular Pacing in Heart Failure`
- `crossref_doi`: `10.1001/jamacardio.2026.0083`
- `crossref_title_similarity`: `0.7928`
- treatment outcome: `review`, **not reject**
- review reason: `fallback_guardrail:targeted_post_openalex_url_only_non_arxiv_low_source_title_similarity`

Interpretation:
- this is exactly the kind of case the two-stage policy is meant to preserve for operator review;
- a pure reject-at-0.80 policy would have been too aggressive here.

## Known
- The new route removes **25 merged normalized-only fallback proposals** and converts exactly **1 additional case** into review.
- The changed set is highly concentrated: almost entirely the already-audited bad-match subgroup.
- The replay effect is stable across four materially different slices (`368 + 95 + 249 + 244 = 956` candidates total).

## Inferred
- `reject71 + review08` is much more production-shaped than `review08` alone.
- It captures nearly all already-audited bad canonicals as deterministic rejects.
- It avoids collapsing the borderline tail into silent reject; instead, it leaves a narrow operator-review channel.

## Speculative
- There may still be room to push the reject threshold slightly above `0.71`, but only if we explicitly audit the `0.71-0.80` band first.
- If desired, the next micro-iteration could use title/URL/document-type cues to pull some review-band cases into deterministic reject without widening false negatives.

## Recommendation
### Main recommendation
Treat `openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_targeted_nonarxiv_reject71_review08` as the current **best operational candidate** for this route.

### Why
Because it achieves the desired shape:
- large removal of already-audited false-positive canonicals
- almost no review-queue inflation (`+1` only)
- no broad spillover into other residual buckets

### Promotion posture
I would describe this as:
- **strong validation evidence**, but
- still one step short of unconditional default promotion memo language.

Reason:
- the semantic confidence is excellent for the 9 already-audited bad cases;
- the remaining uncertainty is now concentrated in a very small tail rather than spread across the route.

## Bottom line
This route now looks real.

The day11 truth audit was not just descriptive: once converted into a deterministic `reject71 + review08` policy, it scales cleanly across four slices and behaves exactly like a targeted cleanup path should behave:

- **25 known-bad canonical fallbacks removed**
- **only 1 new borderline review introduced**
- **effect concentrated in 10 unique candidates total**
