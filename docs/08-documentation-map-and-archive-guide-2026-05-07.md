# Documentation map and archive guide (2026-05-07)

## Purpose

This document defines the post-cleanup documentation layout.

Goal:

- keep `docs/` top level small and readable;
- keep only major, curated documents in the main directory;
- push transitional, superseded, and temporary material into archive folders;
- leave clear indexes so historical files remain discoverable.

## What belongs in `docs/` root

Only **major project documents** should remain in the top-level `docs/` directory.

Current root set:

1. `00-project-charter.md`
2. `01-architecture-overview.md`
3. `02-data-model.md`
4. `03-validation-protocol.md`
5. `04-dedup-and-versioning.md`
6. `05-enrichment-strategy.md`
7. `06-cost-accounting.md`
8. `07-current-project-state-and-library-closure-2026-05-07.md`
9. `08-documentation-map-and-archive-guide-2026-05-07.md`
10. `README.md`

Interpretation:

- `00-06` are the curated foundational layer;
- `07` is the current project-status / closure layer;
- `08` is the structure-and-lookup layer;
- `README.md` is the short entry point.

## What no longer belongs in `docs/` root

The following kinds of files should not stay in the top-level directory:

- temporary plans;
- next-step notes;
- dated transition memos;
- superseded decision checkpoints;
- closure intermediates that were later consolidated;
- historical reports that are no longer the main entry point.

These now live under `docs/archive/`.

## Archive layout

### `docs/archive/phase-and-decision-history-20260415-20260507/`

Use for:

- historical package decisions;
- promotion memos;
- phase-transition reasoning;
- dated major reports that explain how the project evolved.

### `docs/archive/plans-and-working-notes-20260415-20260507/`

Use for:

- next-step plans;
- temporary working notes;
- open-question snapshots;
- documents that were important during execution but are not final references.

### `docs/archive/closure-intermediates-20260507/`

Use for:

- the detailed 2026-05-07 closure memos that were later consolidated into the current-state document.

## Validation layer

The `docs/validation/` directory is now treated similarly:

- only **active / canonical validation summaries** remain at the top level;
- bulky JSON / CSV replay artifacts and superseded intermediate memos are archived under `docs/validation/archive/`.

See:

- `docs/validation/README.md`
- `docs/validation/archive/README.md`

## Maintenance rule going forward

When adding a new document, decide first whether it is:

1. **foundational** → keep in `docs/` root;
2. **current canonical state** → keep in `docs/` root or `docs/validation/` root;
3. **historical but still useful** → put in the appropriate archive folder with index coverage;
4. **temporary / transitional / working** → do not leave it in the main root once it is superseded.

## Bottom line

Top-level `docs/` should answer only three questions:

- what the project is;
- how it works;
- what the current state is.

Everything else should be reachable by index, not left as clutter in the main directory.
