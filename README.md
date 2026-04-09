# MyGoogleAlertPapers

A local-first pipeline for ingesting Google Scholar alert emails, extracting paper candidates, enriching metadata, conservatively deduplicating records, and building a structured paper store for downstream analysis.

## Status

Working prototype validated on real mailbox slices. Current focus is hardening:
- enrichment resumability
- authoritative query cache behavior
- conservative merge / canonical correctness
- reproducible validation environment

## Current pipeline

Implemented CLI stages:
- `init-db`
- `scan-mailbox`
- `parse-mails`
- `normalize-candidates`
- `enrich-candidates`
- `merge-metadata`
- `dedup-candidates`
- reporting commands for batch / normalization / enrichment / merge / dedup / cost

## Validation environment

Quick setup options:

### Option A: conda
```bash
conda env create -f environment.yml
conda activate mgap-dev
make test
```

### Option B: existing Python environment
```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make test
```

If you prefer not to install the package in editable mode, you can still run:
```bash
PYTHONPATH=src python -m pytest tests
```

## Initial goals

- Read Google Scholar alert emails safely in read-only mode
- Do not change unread state during testing
- Extract paper candidates from alert emails
- Enrich metadata via external scholarly APIs
- Deduplicate conservatively
- Track token / API / time consumption for cost estimation
- Validate on ~100 emails before scaling toward ~8000 emails

## Repo structure

- `src/` core pipeline and provider code
- `tests/` parser / normalization unit tests
- `docs/` architecture, roadmap, package plans, validation reports
- `data/` local SQLite DBs and run artifacts

Recommended reading order:
1. `docs/07-implementation-roadmap.md`
2. `docs/11-enrichment-reliability-plan.md`
3. `docs/validation/`

## Notes

- The project currently targets Python 3.10+.
- Validation docs now reflect the real implementation state better than older status notes.
