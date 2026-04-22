# Package 3 optimized 60-mail validation summary

## Date
2026-04-04

## Purpose
Validate the optimized Package 3 state on a larger 60-mail real-mailbox slice after:
- candidate DOI was properly wired into PubMed title-fallback rejection
- merge preference was adjusted to favor identifier-driven records over title-fallback identifier overrides
- Semantic Scholar was included as a conservative complementary provider

---

## Test database
- `data/mgap_pkg3_fix_60.db`

## Slice summary
- unread mails scanned: 60
- Scholar mails detected: 35
- normalized candidates: 135

---

## Aggregate metrics
- matched source records: 288
- merged proposals: 114
- proposals with conflicts: 46
- canonical papers: 101

### Provider matched breakdown
- Crossref: 112 / 135
- OpenAlex: 99 / 135
- PubMed: 60 / 135
- Semantic Scholar: 17 / 135

---

## Interpretation
This 60-mail run suggests that the main Package 3 fixes are materially improving the error profile.

### Positive signals
1. PubMed no longer dominates identifier choice in the same harmful way seen earlier.
2. DOI-driven Crossref/OpenAlex evidence now survives into merged proposals much more often.
3. A number of previously persistent DOI-conflict cases were resolved on the 30-mail slice and the 60-mail slice no longer appears dominated by the same class of obvious false overrides.
4. Semantic Scholar behaves as a conservative complementary provider rather than a high-recall replacement.

### Remaining hard-case classes
The remaining conflicts are more concentrated into harder cases:
1. candidate lacks DOI; title-based providers disagree on DOI
2. venue-label differences that are likely benign formatting or indexing variants
3. HTML / Unicode residue causing title conflicts
4. preprint / journal / review / version-like ambiguities
5. a smaller set of genuinely ambiguous records that likely need advanced fact checking or stricter merge grading

---

## Conclusion
The system is in a substantially better state than earlier Package-3 threshold-only attempts.

The remaining work is less about broad threshold tuning and more about:
- merge conflict grading
- normalization cleanup
- advanced review of ambiguous cases

This is an acceptable point to summarize representative hard cases for advanced fact checking.
