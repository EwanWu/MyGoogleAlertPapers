# Track B Unpaywall integration status (updated 2026-04-22)

## Current status

Track B is now **decision-closed**.

The final conclusion is:
- Unpaywall should **not** be promoted as a normal candidate-level enrich provider for production use
- Unpaywall should be kept as a **post-dedup OA enhancement module**
- recommended production position: **`post_dedup`**

Canonical decision memo:
- `docs/validation/trackB-unpaywall-decision-memo-20260422.md`

Canonical corrected experiment artifact:
- `docs/validation/unpaywall-position-batch50-summary-20260422_batch50-corrected.json`

## What remains valid from the original implementation work

These points still stand:
- `src/mygooglealertpapers/enrich/unpaywall.py` is the correct DOI-only Unpaywall client
- Unpaywall's value is OA metadata, especially `oa_status` and `best_oa_location.url`
- `SOURCE_PRIORITY['unpaywall']=0` is still the right safety rule when running controlled comparisons
- Unpaywall must never be treated as a bibliographic authority for title, authors, venue, year, or DOI selection

## What changed after the corrected placement experiment

Earlier Track B work established that candidate-level Unpaywall at priority 0 does not perturb canonical correctness.

The new batch50 placement experiment added the missing operational question:

> if Unpaywall is useful, where should it live in the pipeline?

Corrected answer:
- candidate-level is safe but coverage-limited
- post-merge and post-dedup capture far more DOI-bearing records for OA URL filling
- post-dedup is the preferred production point because coverage is effectively the same as post-merge, while the semantics are cleaner

## Production implementation state

The project now has a dedicated post-dedup OA step:
- CLI: `mgap enrich-paper-oa --limit ...`
- report: `mgap report-paper-oa`
- storage tables:
  - `paper_open_access`
  - `paper_oa_enrichment_status`

Recommended production flow:
1. `scan-mailbox`
2. `parse-mails`
3. `normalize-candidates`
4. `enrich-candidates`
5. `merge-metadata`
6. `dedup-candidates`
7. `enrich-paper-oa`

## Historical / experimental path retained

The earlier candidate-level Unpaywall wiring is retained only for controlled comparison and replay provenance.

It should be read as:
- useful for experiments
- not the preferred production architecture

## Constraint encountered during this round

Live IMAP selection for older mailbox data failed with:
- `EXAMINE Unsafe Login. Please contact kefu@188.com for help`

Therefore the decisive placement experiment used the oldest locally cached 50-mail Scholar batch rather than freshly selected older mail.
