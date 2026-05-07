# Validation archive index

## Purpose

This index explains where archived validation materials now live after the 2026-05-07 cleanup.

The rule is simple:

- summary-level, still-canonical validation stays in `docs/validation/`
- raw replay files, intermediate controls/treatments, and superseded experiment notes live here in archive folders

## Archive groups

### 1. `raw-json-csv-artifacts-20260415-20260503/`

Contains bulky machine-readable replay outputs, including:

- control / treatment `.json`
- audit `.csv`
- residual refresh `.csv`
- raw comparison artifacts that support archived or summarized reports

Use this group when you need exact numeric artifacts rather than the human-readable decision memo.

### 2. `runtime-and-promotion-history-20260427-20260506/`

Contains superseded or intermediate runtime-optimization and promotion-history markdown files, including:

- day3 / day4 exploratory runtime notes
- detailed day8-day15 control/treatment writeups
- follow-up probes that were later consolidated
- extra large-fixed / medium60 experiment reports
- residual-decomposition side analyses

Use this group when you need the full experiment trail, not just the retained canonical summaries.

### 3. `package-and-mainline-history-20260415-20260422/`

Contains older package-era and early mainline validation artifacts that were no longer needed in the active validation root.

## Legacy archive folders retained

Older archive folders preserved for backward compatibility:

- `day3-runtime-optimization-20260427/`
- `legacy-validation-20260410/`
- `mainline-20260422/`
- `packageB-20260415-16/`
- `trackA-20260421/`
- `trackB-20260421-22/`

## Lookup rule

If you are looking for a missing validation file:

1. check whether a summary-level replacement remains in `docs/validation/`
2. if not, search the relevant archive group here
3. prefer the summary memo unless you specifically need raw replay details
