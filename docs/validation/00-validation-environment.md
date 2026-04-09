# Validation Environment

## Goal
Make local validation reproducible enough that a fresh shell can:
1. install dependencies
2. run unit tests
3. run a small smoke validation flow

---

## Recommended path

### Conda setup
```bash
conda env create -f environment.yml
conda activate mgap-dev
make test
```

### Existing Python environment
```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make test
```

If editable install is not desired, use:
```bash
PYTHONPATH=src python -m pytest tests
```

---

## What this environment currently guarantees

- Python 3.10 baseline
- installable package metadata via `pyproject.toml`
- explicit dev dependency set including `pytest`
- one-command test entry via `make test`
- one-command small smoke suite via `make smoke`

---

## Suggested validation routine

### 1. Unit / parser smoke
```bash
make smoke
```

### 2. Full unit test pass
```bash
make test
```

### 3. Pipeline smoke on a fresh DB
```bash
export SQLITE_PATH=data/mgap_smoke.db
mgap init-db
mgap report-batch
```

### 4. Real mailbox slice validation
Use a dedicated DB path for each run, for example:
```bash
export IMAP_ACCOUNT=issac
export SQLITE_PATH=data/mgap_issac_validation.db
mgap init-db
mgap scan-mailbox --limit 10 --unseen-only
mgap parse-mails --limit 50
mgap normalize-candidates --limit 100
mgap enrich-candidates --limit 100
mgap merge-metadata --limit 100
mgap dedup-candidates --limit 100
mgap report-batch
mgap report-normalization
mgap report-enrichment
mgap report-merge
mgap report-dedup
mgap report-cost
```

---

## Current limitations

- this is a reproducible local validation environment, not a locked production environment
- external provider/network behavior remains non-deterministic across runs
- IMAP and provider credentials still come from local environment or skill-managed config
- live-provider failure-path validation still needs more real-run coverage

---

## Immediate next improvements if needed

1. add CI smoke checks for unit tests
2. split pure unit tests from live-provider / mailbox validation scripts
3. add a small fixture-driven regression set for known bad merge cases
