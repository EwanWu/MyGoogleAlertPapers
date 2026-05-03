# Day15 current-default residual refresh, review-band decomposition, and next-target recommendation (2026-05-03)

## Objective
After retaining the narrow OpenAlex repository-shadow topk retry in the current default runtime, refresh the **true current-default** residual tail and decide what the next coding target should be.

This pass explicitly checks whether the previously-open question — the surviving non-arXiv review band `(0.71, 0.80]` — is still large/coherent enough to justify a direct collapse rule.

---

## Artifacts produced now
- `docs/validation/day15-current-default-large-fixed-post-openalex-residual-refresh-20260503.csv`
- `docs/validation/day15-current-default-medium60-post-openalex-residual-refresh-20260503.csv`
- `docs/validation/day15-current-default-large-fixed-review-band-refresh-20260503.csv`
- `docs/validation/day15-current-default-medium60-review-band-refresh-20260503.csv`

Residual export commands:
```bash
PYTHONPATH=src python3 scripts/export_post_openalex_residual_audit.py \
  --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db \
  --results-db data/benchmark/day14_openalex_repo_shadow_large_fixed_20260503.db \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml \
  --out-csv docs/validation/day15-current-default-large-fixed-post-openalex-residual-refresh-20260503.csv \
  --slice-name day15_current_default_large_fixed \
  --reason openalex_title_unmatched

PYTHONPATH=src python3 scripts/export_post_openalex_residual_audit.py \
  --source-db data/mgap_pkgB_large_slice150_seed_20260416_slice150.db \
  --results-db data/benchmark/day14_openalex_repo_shadow_medium60_20260502.db \
  --policy-profile config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_targeted_nonarxiv_reject71_review08.yaml \
  --out-csv docs/validation/day15-current-default-medium60-post-openalex-residual-refresh-20260503.csv \
  --slice-name day15_current_default_medium60 \
  --reason openalex_title_unmatched
```

Review-band refresh used a direct export from `merged_metadata_proposal` for `0.71 < merge_confidence <= 0.80`.

---

## Known

### 1. The current default residual tail is still dominated by OpenAlex-local miss / Crossref-rescue anatomy
Large-fixed residual refresh (`n=47`):
- `likely_openalex_recall_gap = 29`
- `source_title_noise_or_crossref_cleanup = 12`
- `possible_normalization_or_ranking_issue = 3`
- `mixed_or_unclear = 3`
- `crossref_matched = 31 / 47`

Medium60 residual refresh (`n=11`):
- `likely_openalex_recall_gap = 5`
- `source_title_noise_or_crossref_cleanup = 4`
- `mixed_or_unclear = 2`
- `crossref_matched = 6 / 11`

Interpretation:
- the residual tail is still mostly **OpenAlex title miss followed by Crossref rescue / near-rescue**
- this is not primarily a merge-policy tail

### 2. The residual domains are strongly URL-anchored publisher pages
Top large-fixed residual domains:
- `www.sciencedirect.com = 10`
- `www.mdpi.com = 6`
- `www.nature.com = 3`
- `journals.lww.com = 2`
- `cardiovascular.elpub.ru = 2`
- `www.researchgate.net = 2`
- `xuebao.shsmu.edu.cn = 2`
- `books.google.com = 2`

This is consistent with a residual class where the candidate URL itself still carries article identity that the current default path does not fully exploit before title fanout.

### 3. The previously-open review band is now **almost empty as a residual-policy target**
Checking the refreshed **post-openalex residual** CSVs directly for `0.71 < crossref_title_similarity <= 0.80` leaves:
- `1 / 47` large-fixed residual row
- `1 / 11` medium60 residual row
- same candidate in both slices: `cand_f9eef1736c087be1`
- similarity: `0.7921`
- heuristic bucket: `source_title_noise_or_crossref_cleanup`
- `crossref_matched = 0`

So the true surviving residual review-band target is not a broad tail anymore. It is effectively a singleton.

### 4. The raw `merge_confidence <= 0.80` bucket is not the same thing as a live review-policy tail
A direct refresh of `merged_metadata_proposal` with `0.71 < merge_confidence <= 0.80` gave:
- `29` rows on large-fixed
- `3` rows on medium60

But these rows are all structurally the same:
- `canonical_blocked = false`
- `conflict_grade_max = A`
- raw conflict keys = only `venue`
- these are mostly journal-name surface alias differences such as:
  - `JACC` vs `Journal of the American College of Cardiology`
  - `Journal of Neurosurgery Case Lessons` vs `Journal of Neurosurgery: Case Lessons`
  - `Europace` vs long-form journal expansion

Interpretation:
- this bucket is **not** evidence of a large unresolved review queue
- it is mainly a confidence-shaping artifact from benign venue-string disagreement that already passes through to canonical output

### 5. The title-noise subgroup exists, but it is heterogeneous
The `source_title_noise_or_crossref_cleanup` large-fixed bucket (`n=12`) includes:
- non-English or mixed-language cases
- extraction-noise-heavy cases
- obvious source mismatch cases
- one near-boundary Lancet case (`cand_f9eef1736c087be1`)

This does **not** currently look like a clean multi-case deterministic patch family yet.

---

## Inferred

### A. The review-band collapse question should **not** be the next coding target
The project-phase map was right to flag the review band as the next open question at the time.
But after the current-default refresh, that tail is now too small and too unstructured to justify writing a new collapse rule first.

A singleton residual (`cand_f9eef1736c087be1`) is not enough basis for a default-policy patch.

### B. The next best target has shifted back to **pre-title identity recovery**, not merge-threshold tuning
Because:
1. residuals are still heavily URL-anchored publisher pages
2. `31 / 47` large-fixed residuals already have Crossref rescue signal
3. the review band is nearly exhausted
4. the remaining title-noise bucket is still too heterogeneous for an immediate general patch

### C. The most promising next workstream is a **narrow deterministic URL-origin DOI recovery expansion**
This is consistent with the earlier day13 operator memo, but the refreshed current-default evidence makes the priority clearer now.

The practical thesis is:
> if the current residual tail is still dominated by publisher URL pages where Crossref can later rescue identity, then the best next move is to recover DOI/article identity **before** OpenAlex/Crossref title fanout for a narrow set of deterministic URL shapes.

---

## Recommendation

### Recommended next coding target: URL-origin DOI recovery micro-expansion
Priority order:
1. re-audit the existing deterministic DOI recovery implementation against the current default path
2. identify exactly which of the current residual domains are recoverable by **safe URL-shape rules only**
3. implement only the smallest 1-2 domain rules with strong determinism
4. gate on medium60 before any large-fixed rerun

### Good first candidates
Based on current residual concentration, likely best starting domains are:
- `www.sciencedirect.com`
- `www.mdpi.com`
- `www.nature.com`

But only if the URL itself gives deterministic article identity / DOI extraction without requiring broad live HTML fetch.

### What not to do next
Do **not** start with:
- broad review-band collapse
- generic similarity-threshold lowering
- broad title-noise heuristics
- general HTML scraping across all residual domains

---

## Minimal next execution plan
1. inspect the current `url_identity_doi_recovery` runtime path in code
2. sample the large-fixed residual URLs from the top 2-3 domains
3. classify each as:
   - deterministic DOI recoverable from URL shape
   - deterministic landing-page normalization candidate
   - not safe / not deterministic
4. if at least `2-3` cases share one safe pattern, code that single micro-rule
5. test it on medium60 first

---

## Bottom line
The fresh current-default refresh changes the prioritization:

> **The surviving review band is no longer a substantial next-step target.**
> The next worthwhile coding target is a **narrow URL-origin DOI recovery expansion** for deterministic publisher-page residuals, because the residual tail is still dominated by URL-anchored OpenAlex miss / Crossref rescue cases rather than by a coherent unresolved review-policy band.
