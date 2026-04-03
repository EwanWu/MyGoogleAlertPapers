# Implementation Blueprint

## Goal
Translate the planning documents into a code-ready structure for the first implementation pass.

## Initial implementation target
Deliver a minimal but auditable pipeline that can:
1. connect to one IMAP mailbox in read-only mode
2. fetch sampled messages without changing unread state
3. identify Google Scholar alert emails
4. extract paper candidates from message content
5. persist data to SQLite
6. emit structured logs for debugging and cost accounting scaffolding

## Proposed repository structure

```text
MyGoogleAlertPapers/
├─ README.md
├─ docs/
├─ .gitignore
├─ pyproject.toml
├─ src/
│  └─ mygooglealertpapers/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ logging_utils.py
│     ├─ cli.py
│     ├─ db/
│     │  ├─ __init__.py
│     │  ├─ schema.py
│     │  ├─ models.py
│     │  └─ repository.py
│     ├─ mail/
│     │  ├─ __init__.py
│     │  ├─ imap_client.py
│     │  ├─ message_parser.py
│     │  ├─ scholar_detector.py
│     │  └─ candidate_extractor.py
│     ├─ normalize/
│     │  ├─ __init__.py
│     │  ├─ title.py
│     │  ├─ authors.py
│     │  └─ identifiers.py
│     ├─ enrich/
│     │  ├─ __init__.py
│     │  ├─ base.py
│     │  ├─ crossref.py
│     │  ├─ openalex.py
│     │  ├─ semanticscholar.py
│     │  ├─ pubmed.py
│     │  └─ europepmc.py
│     ├─ dedup/
│     │  ├─ __init__.py
│     │  ├─ rules.py
│     │  └─ versioning.py
│     ├─ pipeline/
│     │  ├─ __init__.py
│     │  ├─ ingest.py
│     │  ├─ enrich.py
│     │  └─ evaluate.py
│     └─ cost/
│        ├─ __init__.py
│        └─ tracker.py
├─ scripts/
│  └─ bootstrap_db.py
├─ data/
│  ├─ .gitkeep
│  ├─ raw_mail_snapshots/
│  ├─ exports/
│  ├─ eval/
│  └─ logs/
└─ tests/
   ├─ test_scholar_detector.py
   ├─ test_title_normalization.py
   └─ test_identifier_extraction.py
```

## Configuration model
Use environment variables via `.env` for local configuration. For IMAP credentials, prefer reuse when available.

Configuration loading order for IMAP phase-1 work:
1. project `.env`
2. `~/.config/imap-smtp-email/.env` compatibility fallback
3. defaults where safe

For multi-account skill config, `IMAP_ACCOUNT=<name>` can be used to select a prefixed account such as `GMAIL_`.

Suggested variables:
- IMAP_HOST
- IMAP_PORT
- IMAP_USERNAME
- IMAP_PASSWORD
- IMAP_MAILBOX
- SQLITE_PATH
- LOG_LEVEL
- OPENALEX_EMAIL (optional polite pool)
- CROSSREF_MAILTO (optional)
- SEMANTIC_SCHOLAR_API_KEY (optional)
- NCBI_API_KEY (optional)

## CLI entrypoints (initial)

### `mgap init-db`
Create SQLite schema.

### `mgap scan-mailbox`
Scan mailbox in read-only mode and persist mail records/raw snapshots.
Current supported options:
- `--limit`
- `--unseen-only`

Planned later options:
- `--since`
- `--uid-file`

### `mgap parse-mails`
Parse stored raw snapshots into candidate records.

### `mgap normalize-candidates`
Normalize extracted candidates and extract basic identifiers.

### `mgap enrich-candidates`
Run enrichment for selected normalized candidates.

### `mgap report-batch`
Summarize ingestion batch statistics and costs.

### `mgap report-normalization`
Summarize normalization coverage such as DOI/PMID extraction and canonical URL domains.

### `mgap report-enrichment`
Summarize provider coverage and source_record match counts.

## SQLite schema bootstrap plan
The first pass can create these tables:
- mail_ingestion_record
- raw_mail_snapshot
- paper_candidate
- paper_candidate_normalized
- cost_event

Tables for enrichment and dedup can be added in phase 2:
- source_record
- merged_metadata_proposal
- canonical_paper
- paper_version_link

## Initial module interfaces

### `config.py`
- `load_settings() -> Settings`

### `mail/imap_client.py`
- `class ImapMailboxClient`
- `connect()`
- `fetch_message_metadata(limit: int, unseen_only: bool) -> list[MessageStub]`
- `fetch_message_body(uid: str) -> RawMessage`

### `mail/message_parser.py`
- `parse_raw_email(raw_bytes: bytes) -> ParsedEmail`

### `mail/scholar_detector.py`
- `detect_google_scholar_alert(parsed_email: ParsedEmail) -> DetectionResult`

### `mail/candidate_extractor.py`
- `extract_candidates(parsed_email: ParsedEmail) -> list[PaperCandidateRaw]`

### `db/schema.py`
- `create_schema(conn)`

### `db/repository.py`
- `insert_mail_ingestion_record(...)`
- `insert_raw_mail_snapshot(...)`
- `insert_paper_candidates(...)`
- `insert_cost_event(...)`
- query helpers for next pipeline stage

### `pipeline/ingest.py`
- `scan_and_store_messages(settings, limit, unseen_only)`
- `parse_and_extract_candidates(settings, limit)`

### `cost/tracker.py`
- `record_stage_cost(...)`
- lightweight no-op-friendly interface for early phases

## Data flow for first coding phase
1. CLI loads settings
2. CLI initializes DB if needed
3. scan-mailbox fetches UIDs and message bodies read-only
4. parser decodes message into structured fields
5. detector decides whether mail is Scholar-related
6. repository stores metadata + raw snapshot
7. parse-mails extracts candidate blocks for Scholar mails
8. candidates written to DB
9. cost/logging scaffolding records stage metrics

## Read-only safety rule
The IMAP client must make read-only behavior explicit in code and logs:
- mailbox selected with readonly semantics
- message body fetched with peek semantics
- no flag mutation methods present in phase 1 code path

## What can start coding immediately
Enough planning exists to begin phase 1 implementation.
No external scholarly API registration is required to start the mailbox, parser, storage, and extraction skeleton.

## API registration status by priority
### Not required for phase 1 skeleton
- Crossref
- OpenAlex
- PubMed
- Europe PMC

### Nice to have later
- Semantic Scholar API key
- NCBI API key

## Documentation maintenance rule
When architecture, schema, pipeline behavior, or constraints change during implementation, update the relevant docs in `docs/` in the same work cycle whenever practical.

## Current implementation state update (2026-04-03)
The project is no longer only a skeleton.
It now includes:
- a working mailbox → candidate → normalize → enrich → merge → dedup pipeline
- batch timing and cost reporting
- provider request shaping improvements such as Crossref `mailto` support and OpenAlex DOI batching helper
- a first Package-1 implementation pass for provider-level enrichment resumability

### What Package 1 first pass now provides
- `candidate_enrichment_status` table for provider-level progress
- provider-intent planning in enrichment instead of candidate-level coarse completion logic
- explicit provider outcomes (`ok`, `no_match`, `error`)
- rerun selection based on provider status
- compatibility bootstrapping from existing `source_record` data

### Current limitation after Package 1 first pass
The system is now structurally resumable at provider-selection level, but not yet a finest-grained durable checkpoint system under hard-kill interruption; an in-flight transaction may still roll back before partial provider work is durably committed.

### Recommended next implementation focus
1. complete and consolidate query-cache authority and uniqueness semantics
2. decide whether finer transaction/checkpoint durability is needed beyond the current provider-selection resumability model
3. strengthen title-fallback acceptance and merge-side conflict grading
4. improve normalization/detail cleanup (including HTML residue and stronger title/venue harmonization)
5. only then expand more aggressive optimization or scale-up runs

### Package 2 first-pass state update (2026-04-03 night)
The first cache-hardening pass has been validated on a small fresh `issac` slice.
Observed results:
- duplicate cache keys dropped to zero on the tested run
- cache row counts remained stable across rerun
- rerun latency remained very low when no provider work remained

This supports continuing with cache-focused consolidation before moving into deeper correctness work.
