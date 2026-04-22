# Package 3 validation: PubMed title-fallback DOI suppression

## Date
2026-04-09

## Purpose
Validate a targeted merge-time rule:
- when non-PubMed sources establish a DOI consensus,
- and PubMed `query_type=title` returns a conflicting DOI,
- suppress the PubMed DOI before conflict grading and canonical promotion.

Motivation:
Earlier blocked-case analysis showed a recurring pattern:
- `Crossref == OpenAlex != PubMed(title-fallback DOI)`

That suggested PubMed title-fallback DOI should not be trusted as strongly as identifier-first or cross-provider DOI consensus.

---

## Rule implemented
At merge time:
1. inspect matched source rows for the candidate
2. if at least two non-PubMed providers agree on the same DOI
3. and a PubMed title-query row carries a different DOI
4. suppress only the PubMed DOI signal
5. keep the rest of the PubMed record, including PMID, title, venue, and year

The suppression is recorded in:
- merge proposal trace
- conflict assessment `suppressed_signals`

---

## Validation datasets
### 30-mail slice
- source DB: `data/mgap_pkg3_fix_30.db`
- rerun DB: `data/mgap_pkg3_guardrail_pubmedfix_30.db`

### 60-mail slice
- source DB: `data/mgap_pkg3_fix_60.db`
- rerun DB: `data/mgap_pkg3_guardrail_pubmedfix_60.db`

For each rerun DB, reset before rerun:
- `merged_metadata_proposal`
- `candidate_paper_link`
- `canonical_paper`
- `merge_review_queue`

Then rerun merge + dedup only.

---

## Results

## 30-mail slice
### Before PubMed DOI suppression
From guardrail-only run:
- proposals with conflicts: 23
- canonical-blocked proposals: 3
- canonical papers: 42
- blocked-for-review: 3

### After PubMed DOI suppression
- proposals with conflicts: 22
- canonical-blocked proposals: 1
- canonical papers: 44
- blocked-for-review: 1

### Interpretation
- review queue shrank from `3 -> 1`
- canonical papers recovered from `42 -> 44`
- one blocked DOI-conflict case still remains and appears to be a more genuine ambiguity

---

## 60-mail slice
### Before PubMed DOI suppression
From guardrail-only run:
- proposals with conflicts: 43
- canonical-blocked proposals: 12
- canonical papers: 92
- blocked-for-review: 12

### After PubMed DOI suppression
- proposals with conflicts: 37
- canonical-blocked proposals: 3
- canonical papers: 99
- blocked-for-review: 3

### Interpretation
- review queue shrank from `12 -> 3`
- canonical papers recovered from `92 -> 99`
- conflict count also decreased (`43 -> 37`)

This is a strong positive result.

---

## What this means
The earlier blocked-case pattern was real and actionable.
A large fraction of severe DOI conflicts were not true multi-provider ambiguity.
They were PubMed title-fallback DOI noise conflicting against stronger non-PubMed DOI consensus.

The new rule improves the system in the desired direction:
- fewer false severe conflicts
- fewer unnecessary review cases
- more canonical recovery without relaxing the conservative posture too broadly

---

## Remaining blocked cases
### 30-mail slice
- 1 blocked case remains

### 60-mail slice
- 3 blocked cases remain

These are likely better candidates for actual review, because the easy PubMed DOI-noise class has mostly been removed.

---

## Current judgment
This targeted rule should stay.

It appears to be:
- high-value
- low-risk
- well-aligned with the conservative main-store policy

---

## Recommended next move
1. keep PubMed title-fallback DOI suppression enabled
2. inspect the remaining 1 / 3 blocked cases manually
3. consider whether PubMed title-fallback PMCID should also receive similar skepticism in some cases
4. avoid broad title-threshold changes until the remaining hard cases are characterized
