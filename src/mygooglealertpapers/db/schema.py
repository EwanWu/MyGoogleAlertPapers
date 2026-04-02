from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
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
"""


ALTERS = [
    "ALTER TABLE paper_candidate ADD COLUMN scholar_wrapper_url TEXT",
    "ALTER TABLE paper_candidate ADD COLUMN target_url TEXT",
    "ALTER TABLE paper_candidate ADD COLUMN resource_type_hint TEXT",
    "ALTER TABLE paper_candidate ADD COLUMN venue_guess TEXT",
    "ALTER TABLE paper_candidate ADD COLUMN year_guess TEXT",
]


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    for stmt in ALTERS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass
    conn.commit()


def create_schema_at_default_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        create_schema(conn)
