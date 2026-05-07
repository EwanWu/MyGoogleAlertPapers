# Day13 API config optimization experiment (2026-05-02)

## Objective
Test the previously identified runtime optimization ideas around OpenAlex and Crossref live calls on the representative `small-fixed / limit=60` benchmark slice.

## User-provided config now saved locally
Project-local `.env`:
- `OPENALEX_API_KEY` = configured
- `OPENALEX_EMAIL` = configured
- `CROSSREF_MAILTO` = configured

Implemented code support:
- load `OPENALEX_API_KEY` from environment
- pass OpenAlex registered email as `mailto=` (not `email=`)
- keep Crossref `mailto=` support active

## Important implementation finding
OpenAlex rejected `email=` and requires `mailto=`.
The first experiment attempt using `email=` was invalid and should not be treated as a meaningful performance result.

## Runs

### Reference baseline
- tag: `day13-new-default-medium60-20260502`
- report: `docs/validation/day2-baseline-small-fixed-day13-new-default-medium60-20260502.json`

### Attempt 1 — invalid OpenAlex email parameter
- tag: `day13-apiopt-medium60-20260502`
- report: `docs/validation/day2-baseline-small-fixed-day13-apiopt-medium60-20260502.json`
- status: invalid for decision-making
- reason: OpenAlex query param used `email=` instead of `mailto=`; this broke OpenAlex title-path behavior and destroyed post-OpenAlex suppression

### Attempt 2 — OpenAlex/Crossref select + OpenAlex mailto/api_key
- tag: `day13-apiopt-mailto-medium60-20260502`
- report: `docs/validation/day2-baseline-small-fixed-day13-apiopt-mailto-medium60-20260502.json`
- status: valid but not retained

### Attempt 3 — Crossref select retained, OpenAlex select reverted
- tag: `day13-apiopt-final-medium60-20260502`
- report: `docs/validation/day2-baseline-small-fixed-day13-apiopt-final-medium60-20260502.json`
- status: valid but not retained

### Attempt 4 — identity config only (OpenAlex api_key+mailto, Crossref mailto)
- tag: `day13-apikey-mailto-only-medium60-20260502`
- report: `docs/validation/day2-baseline-small-fixed-day13-apikey-mailto-only-medium60-20260502.json`
- status: final retained configuration

## Compact comparison

| run | valid | matched_source_record_count | canonical_paper_count | review_queue | total_batch_duration_ms | total_provider_latency_ms |
|---|---:|---:|---:|---:|---:|---:|
| baseline | yes | 83 | 48 | 2 | 156847 | 151028 |
| attempt1 invalid email | no | 35 | 48 | 0 | 156682 | 155626 |
| attempt2 select+mailto | yes | 64 | 48 | 2 | 158904 | 156191 |
| attempt3 crossref-select only | yes | 64 | 48 | 2 | 169841 | 162670 |
| attempt4 api_key+mailto only | yes | 83 | 48 | 2 | 156011 | 152968 |

## Interpretation

### 1. OpenAlex `email=` was the wrong parameter
This was the main bug found during implementation.
Using `email=` caused the title path to fail and inflated residual Crossref work.
Correct parameter is `mailto=`.

### 2. `select=` was not a good default here
Both select-based variants preserved top-level final paper counts in some runs, but they reduced `matched_source_record_count` and did not produce a reliable runtime gain.
So `select=` was tested and then rolled back for the retained configuration.

### 3. The safe retained win is config readiness, not measured speedup
The final retained run (`api_key + mailto only`) recovered the baseline semantic profile exactly on the headline output metrics:
- matched source records: `83` vs baseline `83`
- canonical papers: `48` vs baseline `48`
- review queue: `2` vs baseline `2`
- severe DOI conflicts: `2` vs baseline `2`

Runtime effect was basically neutral on this sample:
- wall time: `156847 ms -> 156011 ms` (~`0.8 s` faster, negligible)
- provider latency: `151028 ms -> 152968 ms` (~`1.9 s` slower, negligible)

### 4. Provider-level shape under retained config
Final retained run provider latency:
- Crossref: `77704 ms`
- OpenAlex: `71547 ms`
- EuropePMC: `2387 ms`
- PubMed: `1330 ms`

Compared with baseline:
- Crossref improved modestly (`82258 -> 77704 ms`)
- OpenAlex worsened modestly (`62726 -> 71547 ms`)
- total effect nearly canceled out

## Final retained decision
Keep:
- project-local saved credentials/config
- `OPENALEX_API_KEY` support in code
- OpenAlex registered email routed as `mailto=`
- Crossref `mailto=`

Do not keep as current default optimization:
- OpenAlex `select=` slimming
- Crossref `select=` slimming

## Bottom line
The user-provided API credentials are now saved and wired correctly.
The experiment shows:
- configuration support is correct and stable
- `select=` shrinking is not currently worth keeping
- on this representative medium60 live slice, API config alone does **not** yield a meaningful end-to-end runtime improvement

So the correct operator conclusion is:
> keep the credentials and polite/auth config, but do not claim a speed win from them yet.
