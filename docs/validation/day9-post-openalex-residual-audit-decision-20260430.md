# Day9 residual audit decision memo (2026-04-30)

## Objective

Inspect the `openalex_title_unmatched` residual `crossref:url_canonical_only` groups after promotion of the narrow post-OpenAlex suppression rule, then decide whether the next one-factor ablation should target:

1. `cluster_leader_path`, or
2. `url_canonical_only` recall / normalization.

## Artifacts produced

### Export script
- `scripts/export_post_openalex_residual_audit.py`

### Candidate-level audit exports
- `docs/validation/day9-post-openalex-residual-audit-fixed150-20260430.csv`
- `docs/validation/day9-post-openalex-residual-audit-fresh30-20260430.csv`

## Known

### Residual structure from the replay summaries
- fixed150 residual `crossref` title requests: `94`
  - unsuppressed `url_canonical_only`: `50`
  - `cluster_leader_path`: `30`
  - `mixed_non_doi_identifier`: `14`
- fresh30 residual `crossref` title requests: `29`
  - unsuppressed `url_canonical_only`: `12`
  - `cluster_leader_path`: `11`
  - `mixed_non_doi_identifier`: `6`

### New non-suppression reason
Both slices reported only one targeted non-suppression reason:
- `openalex_title_unmatched`

### Audit export counts
- fixed150 exported rows: `50`
- fresh30 exported rows: `12`

### Heuristic bucket summary from exported rows
These buckets are descriptive aids for manual review, not promotion gates.

#### fixed150 (`n=50`)
- `likely_openalex_recall_gap`: `27`
- `possible_normalization_or_ranking_issue`: `9`
- `source_title_noise_or_crossref_cleanup`: `11`
- `mixed_or_unclear`: `3`

#### fresh30 (`n=12`)
- `likely_openalex_recall_gap`: `7`
- `possible_normalization_or_ranking_issue`: `1`
- `source_title_noise_or_crossref_cleanup`: `3`
- `mixed_or_unclear`: `1`

### High-confidence DOI rescue subset
Using `merge_confidence = 0.9` as the practical proxy for successful DOI-bearing rescue:

- fixed150 high-confidence subset: `30`
  - `likely_openalex_recall_gap`: `26`
  - `possible_normalization_or_ranking_issue`: `3`
  - `mixed_or_unclear`: `1`
- fresh30 high-confidence subset: `6`
  - `likely_openalex_recall_gap`: `6`

Combined high-confidence rescue signal: `36` cases total, of which `32` look most like **OpenAlex recall gap** rather than cluster-path overhead.

## Representative observations

### Strong recall-gap-like examples
These are cases where the candidate / Crossref title is already highly aligned, but OpenAlex surfaced an unrelated paper or failed match scoring:
- `cand_3c2e407353cf4446`
- `cand_ef45f083c154b55c`
- `cand_4940296152b16081`
- `cand_2c20e1235f3905bf`
- `cand_06d1dc8f00875dd8`
- `cand_017b4798ca98e797`

### Possible normalization / ranking issues
These are cases where OpenAlex returned the same or nearly the same title but still ended up unmatched, suggesting a query-shape / scoring / ranking problem worth targeted debugging:
- `cand_e6e0961ddf95e426`
- `cand_89794a7e8282a9b7`
- `cand_8994637b2b637b39`

### Source-title-noise / cleanup cases
These tend to have truncated PDF-derived titles, non-English strings, author-blob contamination, or incomplete thesis / preprint metadata. They look less like a clean suppression target and more like upstream title-cleaning work if worth pursuing at all.

## Inferred decision

The next one-factor ablation should preferentially target:

> **`url_canonical_only` recall / normalization**, not `cluster_leader_path`.

## Why

1. **It is still the largest residual subgroup on both slices.**
   - `50 > 30` on fixed150
   - `12 > 11` on fresh30

2. **The productive part of this subgroup is dominated by recall-gap-like cases.**
   The high-confidence DOI-bearing rescue subset is mostly not “junk cost”; it is mostly cases where Crossref succeeds and OpenAlex does not.

3. **The new observability isolates the mechanism cleanly.**
   The residual non-suppression reason is not mixed; it is consistently `openalex_title_unmatched`.

4. **`cluster_leader_path` remains important, but currently looks like the runner-up rather than the dominant mechanism.**
   It should stay as the likely next fallback target if the URL-only recall/normalization patch does not move the fixed+fresh-like metrics.

## Recommended next experiment

Run exactly one narrow experiment inside the `url_canonical_only` path, for example one of:

1. **title cleanup / normalization micro-patch** before OpenAlex title query
   - strip PDF/download suffix noise
   - normalize truncated punctuation patterns such as `. .`
   - collapse obvious author-tail contamination

2. **OpenAlex query-shape micro-ablation** for URL-only candidates
   - compare current title query vs a cleaned-title query only for `url_canonical_only`
   - keep Crossref fallback unchanged

3. **Do not broaden suppression.**
   The evidence here points to recovery failure, not redundant residual Crossref work.

## Not recommended as immediate next move

- broadening post-OpenAlex suppression beyond `crossref:url_canonical_only`
- switching the main effort to `cluster_leader_path` before trying a URL-only recall/normalization micro-patch
- bundling normalization + suppression + cluster-leader changes in the same treatment
