# Package 3 iterative fix validation on 30-mail slice

## Date
2026-04-04

## Purpose
Validate the next targeted Package 3 iteration after the initial threshold-tightening experiment failed to materially improve suspicious merge outcomes.

This iteration applied two more targeted changes:
1. pass candidate DOI into PubMed title-fallback acceptance so DOI contradiction rules can actually fire
2. reweight merge preference so DOI/PMID fields favor identifier-driven records over title-fallback records, with PubMed no longer treated as globally highest-priority for identifiers

---

## Test database
- `data/mgap_pkg3_fix_30.db`

## Shared slice
- mailbox: `issac`
- scan size: 30 unread mails
- Scholar mails detected: 16
- normalized candidates: 59

---

## Aggregate metrics
- matched source records: 139
- merged proposals: 51
- proposals with conflicts: 24
- canonical papers: 45

### Provider matched breakdown
- Crossref: 48 / 59
- OpenAlex: 47 / 59
- PubMed: 24 / 59
- Semantic Scholar: 20 / 59

---

## Comparison against earlier treatment pass
Relative to the earlier stricter-threshold treatment (`mgap_pkg3_treat2_30.db`):
- matched source records improved (`130 -> 139`)
- merged proposals decreased slightly (`52 -> 51`)
- conflict count improved substantially (`34 -> 24`)
- canonical papers decreased slightly (`46 -> 45`), consistent with a more conservative main-store posture
- PubMed matched fewer records (`32 -> 24`), indicating a more selective title-fallback path
- Semantic Scholar matched more records (`10 -> 20`), increasing usefulness as a conservative complementary source

---

## Representative corrected cases
The following persistent suspicious DOI-conflict cases were substantially improved:

### `cand_b098eb3ba9e5dd46`
- candidate DOI: `10.1007/s00392-026-02878-7`
- preferred DOI after fix: `10.1007/s00392-026-02878-7`
- PubMed title result still existed but became `matched=0`
- conflict flags cleared

### `cand_b1967575531ec006`
- candidate DOI: `10.1007/s00234-026-03918-9`
- preferred DOI after fix: `10.1007/s00234-026-03918-9`
- PubMed contradictory DOI result became `matched=0`
- conflict flags cleared

### `cand_7b97f8abac8fb730`
- candidate DOI: `10.1007/s12975-026-01427-8`
- preferred DOI after fix: `10.1007/s12975-026-01427-8`
- PubMed contradictory DOI result became `matched=0`
- conflict flags cleared

### `cand_2901cc65f3f3a280`
- candidate DOI: `10.1007/s40477-026-01146-8`
- preferred DOI after fix: `10.1007/s40477-026-01146-8`
- PubMed contradictory DOI result became `matched=0`
- conflict flags cleared

---

## Remaining hard case
### `cand_5755410c2959d9d4`
This case remains difficult because:
- the candidate lacks an extracted DOI
- Crossref title path and OpenAlex title path agree on one DOI (`10.3174/ajnr.a9072`)
- PubMed title path returns a different DOI (`10.1161/jaha.122.025853`)
- PMID agreement complicates the interpretation

This is a good candidate for:
- advanced fact checking
- merge conflict grading
- later severe-conflict policy design

---

## Interpretation
This targeted iteration appears genuinely useful.

The improvement did **not** come from a generic threshold change alone.
It came from wiring the correct evidence into acceptance/merge decisions:
- candidate DOI awareness in PubMed title-fallback rejection
- identifier-aware merge preference that no longer lets title-fallback PubMed identifiers automatically dominate DOI-driven Crossref/OpenAlex evidence

---

## Conclusion
Package 3 is now producing meaningful improvement on the 30-mail slice.
This is a reasonable point to proceed to a larger 60-mail validation, while also preparing representative cases for advanced fact checking.
