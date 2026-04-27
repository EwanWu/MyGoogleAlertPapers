# Day 2 benchmark baseline command set (2026-04-26)

This note freezes the **reproducible baseline entrypoints** for post-Day-1 / pre-Day-3 comparison work.

Current mainline profile:

- `config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml`

## Standard entrypoint

Use the CLI wrapper instead of hand-assembling replay commands:

```bash
PYTHONPATH=src python3 -m mygooglealertpapers.cli benchmark-baseline --preset <small-fixed|large-fixed|fresh-like>
```

Add `--execute` to actually run the preset. Without `--execute`, the command prints the resolved manifest and exact replay command.

## Presets

### 1) Small fixed slice

Fast comparison loop from the validated slice150 seed:

```bash
PYTHONPATH=src python3 -m mygooglealertpapers.cli benchmark-baseline --preset small-fixed --run-tag baseline
```

- source DB: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- limit: `60`
- stages: `enrich -> merge -> dedup`

### 2) Large fixed slice

Full current fixed-seed comparison:

```bash
PYTHONPATH=src python3 -m mygooglealertpapers.cli benchmark-baseline --preset large-fixed --run-tag baseline
```

- source DB: `data/mgap_pkgB_large_slice150_seed_20260416_slice150.db`
- limit: `1000000` (effectively full slice)
- stages: `enrich -> merge -> dedup`

### 3) Fresh-like cached slice

Best currently available fresh-like cached comparison path:

```bash
PYTHONPATH=src python3 -m mygooglealertpapers.cli benchmark-baseline --preset fresh-like --run-tag baseline
```

- source DB: `data/mgap_fresh30_20260410.db`
- limit: `1000000` (effectively full slice)
- stages: `enrich -> merge -> dedup`

## Output convention

For preset `<preset>` and run tag `<tag>`:

- replay DB: `data/benchmark/day2_baseline_<preset>_<tag>.db`
- JSON report: `docs/validation/day2-baseline-<preset>-<tag>.json`
- Markdown report: `docs/validation/day2-baseline-<preset>-<tag>.md`

## Minimum comparison fields

Each replay report must at least preserve:

- candidate count
- provider intent count
- canonical count
- review queue count
- severe DOI conflict count
- provider latency summary
- rerun/cache behavior as reflected in the replay DB and report tables
