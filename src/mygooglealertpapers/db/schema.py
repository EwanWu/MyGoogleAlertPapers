from __future__ import annotations

import sqlite3
from pathlib import Path


def configure_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


SCHEMA_SQL = """

CREATE TABLE IF NOT EXISTS batch_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    duration_ms INTEGER,
    requested_limit INTEGER,
    processed_count INTEGER,
    status TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS mail_ingestion_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_uid TEXT NOT NULL,
    message_id TEXT,
    mailbox TEXT NOT NULL,
    internal_date TEXT,
    from_address TEXT,
    subject TEXT,
    is_unseen_at_scan INTEGER,
    scan_mode TEXT NOT NULL,
    is_google_scholar_alert INTEGER,
    parse_status TEXT,
    num_candidates_extracted INTEGER,
    processing_started_at TEXT,
    processing_finished_at TEXT,
    wall_time_ms INTEGER,
    error_code TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_mail_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_uid TEXT NOT NULL,
    header_json TEXT,
    body_text TEXT,
    body_html TEXT,
    body_hash TEXT,
    snapshot_path TEXT,
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_candidate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    mail_uid TEXT NOT NULL,
    candidate_index_in_mail INTEGER,
    raw_title TEXT,
    raw_authors TEXT,
    raw_source_text TEXT,
    raw_link TEXT,
    raw_snippet TEXT,
    parser_confidence REAL,
    template_variant TEXT,
    extraction_notes TEXT,
    scholar_wrapper_url TEXT,
    target_url TEXT,
    resource_type_hint TEXT,
    venue_guess TEXT,
    year_guess TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_candidate_normalized (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    norm_title TEXT,
    norm_title_key TEXT,
    norm_authors_json TEXT,
    first_author_family TEXT,
    year_guess TEXT,
    venue_guess TEXT,
    doi_extracted TEXT,
    pmid_extracted TEXT,
    pmcid_extracted TEXT,
    arxiv_id_extracted TEXT,
    url_canonical TEXT,
    scholar_cluster_hint TEXT,
    normalized_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS query_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    query_type TEXT NOT NULL,
    query_key TEXT NOT NULL,
    response_json TEXT,
    cache_status TEXT NOT NULL DEFAULT 'positive_match',
    http_status INTEGER,
    error_type TEXT,
    expires_at TEXT,
    field_set_hash TEXT NOT NULL DEFAULT 'default',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_query_cache_provider_type_key
ON query_cache(provider, query_type, query_key, field_set_hash);

CREATE TABLE IF NOT EXISTS source_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    query_type TEXT,
    query_string TEXT,
    matched INTEGER,
    match_score REAL,
    external_id TEXT,
    title TEXT,
    authors_json TEXT,
    abstract TEXT,
    venue TEXT,
    year TEXT,
    publication_type TEXT,
    doi TEXT,
    pmid TEXT,
    pmcid TEXT,
    url TEXT,
    raw_payload_json TEXT,
    latency_ms INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_enrichment_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    query_type TEXT,
    query_key TEXT,
    source_record_id INTEGER,
    cache_hit INTEGER DEFAULT 0,
    attempt_count INTEGER DEFAULT 0,
    last_started_at TEXT,
    last_finished_at TEXT,
    latency_ms INTEGER,
    error_summary TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_enrichment_status_candidate_provider
ON candidate_enrichment_status(candidate_id, provider);

CREATE TABLE IF NOT EXISTS merged_metadata_proposal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    preferred_title TEXT,
    preferred_authors_json TEXT,
    preferred_abstract TEXT,
    preferred_venue TEXT,
    preferred_year TEXT,
    preferred_doi TEXT,
    preferred_pmid TEXT,
    preferred_publication_type TEXT,
    version_status TEXT,
    source_priority_trace TEXT,
    conflict_flags_json TEXT,
    merge_confidence REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS canonical_paper (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    canonical_title TEXT,
    canonical_title_key TEXT,
    canonical_authors_json TEXT,
    canonical_abstract TEXT,
    canonical_venue TEXT,
    canonical_year TEXT,
    canonical_doi TEXT,
    canonical_pmid TEXT,
    canonical_pmcid TEXT,
    publication_type TEXT,
    first_author_family TEXT,
    version_preference TEXT,
    influence_metrics_json TEXT,
    topic_signals_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_paper_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    paper_id TEXT NOT NULL,
    relation_type TEXT,
    confidence REAL,
    evidence_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_resolution_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    resolution_stage TEXT NOT NULL,
    resolution_rule TEXT,
    paper_id TEXT,
    leader_candidate_id TEXT,
    status TEXT NOT NULL,
    evidence_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_identity_alias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    alias_type TEXT NOT NULL,
    alias_key TEXT NOT NULL,
    confidence REAL,
    source_stage TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merge_review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL UNIQUE,
    reason TEXT,
    assessment_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_open_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    doi TEXT,
    is_oa INTEGER,
    oa_status TEXT,
    best_oa_url TEXT,
    best_oa_host_type TEXT,
    best_oa_version TEXT,
    license TEXT,
    raw_payload_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_oa_enrichment_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    query_type TEXT,
    query_key TEXT,
    cache_hit INTEGER DEFAULT 0,
    attempt_count INTEGER DEFAULT 0,
    last_started_at TEXT,
    last_finished_at TEXT,
    latency_ms INTEGER,
    error_summary TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_oa_enrichment_status_paper_provider
ON paper_oa_enrichment_status(paper_id, provider);

CREATE TABLE IF NOT EXISTS cost_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_uid TEXT,
    candidate_id TEXT,
    stage TEXT NOT NULL,
    provider TEXT,
    request_count INTEGER,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tokens_total INTEGER,
    estimated_cost_usd REAL,
    latency_ms INTEGER,
    status TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mail_ingestion_record_mail_uid
ON mail_ingestion_record(mail_uid);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mail_ingestion_record_message_id_nonempty
ON mail_ingestion_record(message_id)
WHERE message_id IS NOT NULL AND TRIM(message_id) != '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_mail_snapshot_mail_uid
ON raw_mail_snapshot(mail_uid);

CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_candidate_normalized_candidate_id
ON paper_candidate_normalized(candidate_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_merged_metadata_proposal_candidate_id
ON merged_metadata_proposal(candidate_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_paper_link_candidate_paper_relation
ON candidate_paper_link(candidate_id, paper_id, relation_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_resolution_status_candidate_id
ON candidate_resolution_status(candidate_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_identity_alias_type_key
ON paper_identity_alias(alias_type, alias_key);

CREATE INDEX IF NOT EXISTS idx_paper_identity_alias_paper_id
ON paper_identity_alias(paper_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_paper_doi_nonempty
ON canonical_paper(canonical_doi)
WHERE canonical_doi IS NOT NULL AND TRIM(canonical_doi) != '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_paper_pmid_nonempty
ON canonical_paper(canonical_pmid)
WHERE canonical_pmid IS NOT NULL AND TRIM(canonical_pmid) != '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_paper_pmcid_nonempty
ON canonical_paper(canonical_pmcid)
WHERE canonical_pmcid IS NOT NULL AND TRIM(canonical_pmcid) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_doi_extracted_nonempty
ON paper_candidate_normalized(doi_extracted)
WHERE doi_extracted IS NOT NULL AND TRIM(doi_extracted) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_pmid_extracted_nonempty
ON paper_candidate_normalized(pmid_extracted)
WHERE pmid_extracted IS NOT NULL AND TRIM(pmid_extracted) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_pmcid_extracted_nonempty
ON paper_candidate_normalized(pmcid_extracted)
WHERE pmcid_extracted IS NOT NULL AND TRIM(pmcid_extracted) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_arxiv_extracted_nonempty
ON paper_candidate_normalized(arxiv_id_extracted)
WHERE arxiv_id_extracted IS NOT NULL AND TRIM(arxiv_id_extracted) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_scholar_cluster_nonempty
ON paper_candidate_normalized(scholar_cluster_hint)
WHERE scholar_cluster_hint IS NOT NULL AND TRIM(scholar_cluster_hint) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_url_canonical_nonempty
ON paper_candidate_normalized(url_canonical)
WHERE url_canonical IS NOT NULL AND TRIM(url_canonical) != '';

CREATE INDEX IF NOT EXISTS idx_pcn_title_author_year
ON paper_candidate_normalized(norm_title_key, first_author_family, year_guess);
"""


ALTERS = [
    'ALTER TABLE paper_candidate ADD COLUMN scholar_wrapper_url TEXT',
    'ALTER TABLE paper_candidate ADD COLUMN target_url TEXT',
    'ALTER TABLE paper_candidate ADD COLUMN resource_type_hint TEXT',
    'ALTER TABLE paper_candidate ADD COLUMN venue_guess TEXT',
    'ALTER TABLE paper_candidate ADD COLUMN year_guess TEXT',
    "ALTER TABLE query_cache ADD COLUMN cache_status TEXT NOT NULL DEFAULT 'positive_match'",
    'ALTER TABLE query_cache ADD COLUMN http_status INTEGER',
    'ALTER TABLE query_cache ADD COLUMN error_type TEXT',
    'ALTER TABLE query_cache ADD COLUMN expires_at TEXT',
    "ALTER TABLE query_cache ADD COLUMN field_set_hash TEXT NOT NULL DEFAULT 'default'",
]


POST_ALTERS = [
    'DROP INDEX IF EXISTS idx_query_cache_provider_type_key',
    '''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_query_cache_provider_type_key
    ON query_cache(provider, query_type, query_key, field_set_hash)
    ''',
]


def create_schema(conn: sqlite3.Connection) -> None:
    configure_connection(conn)
    conn.executescript(SCHEMA_SQL)
    for stmt in ALTERS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass
    for stmt in POST_ALTERS:
        conn.execute(stmt)
    conn.commit()


def create_schema_at_default_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        configure_connection(conn)
        create_schema(conn)
