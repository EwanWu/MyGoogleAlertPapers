from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.db.schema import configure_connection, create_schema
from mygooglealertpapers.mail.candidate_extractor import PaperCandidateRaw
from mygooglealertpapers.mail.message_parser import ParsedEmail


_SCHEMA_READY_PATHS: set[str] = set()


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        configure_connection(conn)
        resolved = str(self.db_path.resolve())
        if resolved not in _SCHEMA_READY_PATHS:
            create_schema(conn)
            _SCHEMA_READY_PATHS.add(resolved)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_mail_ingestion_record(
        self,
        conn: sqlite3.Connection,
        *,
        mail_uid: str,
        message_id: str | None,
        mailbox: str,
        internal_date: str | None,
        from_address: str | None,
        subject: str | None,
        is_unseen_at_scan: bool,
        scan_mode: str,
        is_google_scholar_alert: bool | None,
        parse_status: str | None,
        num_candidates_extracted: int | None,
        wall_time_ms: int | None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO mail_ingestion_record (
                mail_uid, message_id, mailbox, internal_date, from_address, subject,
                is_unseen_at_scan, scan_mode, is_google_scholar_alert, parse_status,
                num_candidates_extracted, wall_time_ms, error_code, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mail_uid,
                message_id,
                mailbox,
                internal_date,
                from_address,
                subject,
                int(is_unseen_at_scan),
                scan_mode,
                None if is_google_scholar_alert is None else int(is_google_scholar_alert),
                parse_status,
                num_candidates_extracted,
                wall_time_ms,
                error_code,
                error_message,
            ),
        )

    def insert_raw_mail_snapshot(self, conn: sqlite3.Connection, *, mail_uid: str, parsed_email: ParsedEmail, snapshot_path: str | None = None) -> None:
        conn.execute(
            """
            INSERT OR IGNORE INTO raw_mail_snapshot (mail_uid, header_json, body_text, body_html, body_hash, snapshot_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                mail_uid,
                json.dumps(parsed_email.headers, ensure_ascii=False),
                parsed_email.body_text,
                parsed_email.body_html,
                parsed_email.body_hash,
                snapshot_path,
            ),
        )

    def update_mail_candidate_count(self, conn: sqlite3.Connection, *, mail_uid: str, num_candidates_extracted: int) -> None:
        conn.execute(
            """
            UPDATE mail_ingestion_record
            SET num_candidates_extracted = ?, parse_status = ?
            WHERE id = (
                SELECT id FROM mail_ingestion_record
                WHERE mail_uid = ?
                ORDER BY id DESC
                LIMIT 1
            )
            """,
            (num_candidates_extracted, 'candidates_extracted', mail_uid),
        )

    def insert_paper_candidates(self, conn: sqlite3.Connection, candidates: list[PaperCandidateRaw]) -> None:
        conn.executemany(
            """
            INSERT INTO paper_candidate (
                candidate_id, mail_uid, candidate_index_in_mail, raw_title, raw_authors,
                raw_source_text, raw_link, raw_snippet, parser_confidence,
                template_variant, extraction_notes, scholar_wrapper_url,
                target_url, resource_type_hint, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    c.candidate_id,
                    c.mail_uid,
                    c.candidate_index_in_mail,
                    c.raw_title,
                    c.raw_authors,
                    c.raw_source_text,
                    c.raw_link,
                    c.raw_snippet,
                    c.parser_confidence,
                    c.template_variant,
                    c.extraction_notes,
                    c.scholar_wrapper_url,
                    c.target_url,
                    c.resource_type_hint,
                    c.venue_guess,
                    c.year_guess,
                )
                for c in candidates
            ],
        )

    def insert_source_record(self, conn: sqlite3.Connection, rec) -> None:
        conn.execute(
            """
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched,
                match_score, external_id, title, authors_json, abstract, venue, year,
                publication_type, doi, pmid, pmcid, url, raw_payload_json, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec.candidate_id, rec.source_name, rec.query_type, rec.query_string, int(rec.matched),
                rec.match_score, rec.external_id, rec.title, rec.authors_json, rec.abstract, rec.venue, rec.year,
                rec.publication_type, rec.doi, rec.pmid, rec.pmcid, rec.url, rec.raw_payload_json, rec.latency_ms
            ),
        )

    def insert_cost_event(
        self,
        conn: sqlite3.Connection,
        *,
        stage: str,
        status: str,
        mail_uid: str | None = None,
        candidate_id: str | None = None,
        provider: str | None = None,
        request_count: int | None = None,
        tokens_prompt: int | None = None,
        tokens_completion: int | None = None,
        tokens_total: int | None = None,
        estimated_cost_usd: float | None = None,
        latency_ms: int | None = None,
        notes: str | None = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO cost_event (
                mail_uid, candidate_id, stage, provider, request_count,
                tokens_prompt, tokens_completion, tokens_total, estimated_cost_usd,
                latency_ms, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mail_uid,
                candidate_id,
                stage,
                provider,
                request_count,
                tokens_prompt,
                tokens_completion,
                tokens_total,
                estimated_cost_usd,
                latency_ms,
                status,
                notes,
            ),
        )

    def list_unparsed_scholar_mail_uids(self, conn: sqlite3.Connection, limit: int) -> list[str]:
        rows = conn.execute(
            """
            SELECT DISTINCT mir.mail_uid
            FROM mail_ingestion_record mir
            LEFT JOIN paper_candidate pc ON pc.mail_uid = mir.mail_uid
            WHERE mir.is_google_scholar_alert = 1
              AND pc.id IS NULL
            ORDER BY mir.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [row[0] for row in rows]

    def get_raw_mail_snapshot_by_uid(self, conn: sqlite3.Connection, mail_uid: str) -> tuple[str | None, str | None] | None:
        row = conn.execute(
            """
            SELECT body_text, body_html
            FROM raw_mail_snapshot
            WHERE mail_uid = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (mail_uid,),
        ).fetchone()
        return None if row is None else (row[0], row[1])

    def start_batch_run(self, conn: sqlite3.Connection, *, run_id: str, stage: str, requested_limit: int | None, notes: str | None = None) -> None:
        conn.execute(
            """
            INSERT INTO batch_run (run_id, stage, requested_limit, status, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, stage, requested_limit, 'running', notes),
        )

    def update_batch_run_progress(self, conn: sqlite3.Connection, *, run_id: str, duration_ms: int, processed_count: int, notes: str | None = None) -> None:
        conn.execute(
            """
            UPDATE batch_run
            SET duration_ms = ?,
                processed_count = ?,
                notes = CASE WHEN ? IS NULL THEN notes ELSE ? END
            WHERE run_id = ?
            """,
            (duration_ms, processed_count, notes, notes, run_id),
        )

    def finish_batch_run(self, conn: sqlite3.Connection, *, run_id: str, duration_ms: int, processed_count: int, status: str, notes: str | None = None) -> None:
        conn.execute(
            """
            UPDATE batch_run
            SET finished_at = CURRENT_TIMESTAMP,
                duration_ms = ?,
                processed_count = ?,
                status = ?,
                notes = CASE WHEN ? IS NULL THEN notes ELSE ? END
            WHERE run_id = ?
            """,
            (duration_ms, processed_count, status, notes, notes, run_id),
        )

    def get_query_cache(self, conn: sqlite3.Connection, *, provider: str, query_type: str, query_key: str, field_set_hash: str = 'default', include_transient: bool = False):
        clauses = [
            'provider = ?',
            'query_type = ?',
            'query_key = ?',
            'field_set_hash = ?',
            '(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)',
        ]
        params: list[object] = [provider, query_type, query_key, field_set_hash]
        if not include_transient:
            clauses.append("cache_status IN ('positive_match', 'permanent_no_match')")
        return conn.execute(
            f"SELECT response_json, cache_status, http_status, error_type, expires_at, field_set_hash FROM query_cache WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT 1",
            params,
        ).fetchone()

    def put_query_cache(
        self,
        conn: sqlite3.Connection,
        *,
        provider: str,
        query_type: str,
        query_key: str,
        response_json: str,
        cache_status: str,
        http_status: int | None = None,
        error_type: str | None = None,
        expires_at: str | None = None,
        field_set_hash: str = 'default',
    ) -> None:
        conn.execute(
            '''
            INSERT INTO query_cache (
                provider, query_type, query_key, response_json,
                cache_status, http_status, error_type, expires_at, field_set_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider, query_type, query_key, field_set_hash) DO UPDATE SET
                response_json = excluded.response_json,
                cache_status = excluded.cache_status,
                http_status = excluded.http_status,
                error_type = excluded.error_type,
                expires_at = excluded.expires_at,
                created_at = CURRENT_TIMESTAMP
            ''',
            (provider, query_type, query_key, response_json, cache_status, http_status, error_type, expires_at, field_set_hash),
        )

    def get_enrichment_status(self, conn: sqlite3.Connection, *, candidate_id: str, provider: str):
        return conn.execute(
            '''
            SELECT id, status, query_type, query_key, source_record_id, cache_hit, attempt_count,
                   last_started_at, last_finished_at, latency_ms, error_summary, notes
            FROM candidate_enrichment_status
            WHERE candidate_id = ? AND provider = ?
            LIMIT 1
            ''',
            (candidate_id, provider),
        ).fetchone()

    def start_enrichment_status(self, conn: sqlite3.Connection, *, candidate_id: str, provider: str, query_type: str | None, query_key: str | None, notes: str | None = None) -> None:
        conn.execute(
            '''
            INSERT INTO candidate_enrichment_status (
                candidate_id, provider, status, query_type, query_key, cache_hit,
                attempt_count, last_started_at, notes, updated_at
            ) VALUES (?, ?, 'pending', ?, ?, 0, 1, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(candidate_id, provider) DO UPDATE SET
                status='pending',
                query_type=excluded.query_type,
                query_key=excluded.query_key,
                attempt_count=candidate_enrichment_status.attempt_count + 1,
                last_started_at=CURRENT_TIMESTAMP,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            ''',
            (candidate_id, provider, query_type, query_key, notes),
        )

    def finish_enrichment_status(self, conn: sqlite3.Connection, *, candidate_id: str, provider: str, status: str, source_record_id: int | None = None, cache_hit: bool = False, latency_ms: int | None = None, error_summary: str | None = None, notes: str | None = None) -> None:
        conn.execute(
            '''
            UPDATE candidate_enrichment_status
            SET status = ?,
                source_record_id = ?,
                cache_hit = ?,
                last_finished_at = CURRENT_TIMESTAMP,
                latency_ms = ?,
                error_summary = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE candidate_id = ? AND provider = ?
            ''',
            (status, source_record_id, int(cache_hit), latency_ms, error_summary, notes, candidate_id, provider),
        )

    def existing_source_record_for_provider(self, conn: sqlite3.Connection, *, candidate_id: str, provider: str):
        return conn.execute(
            '''
            SELECT id, matched
            FROM source_record
            WHERE candidate_id = ? AND source_name = ?
            ORDER BY id DESC
            LIMIT 1
            ''',
            (candidate_id, provider),
        ).fetchone()

    def bootstrap_enrichment_status_from_source_record(self, conn: sqlite3.Connection, *, candidate_id: str, provider: str) -> None:
        existing = self.existing_source_record_for_provider(conn, candidate_id=candidate_id, provider=provider)
        if existing is None:
            return
        source_record_id, matched = existing
        status = 'ok' if matched else 'no_match'
        conn.execute(
            '''
            INSERT INTO candidate_enrichment_status (
                candidate_id, provider, status, source_record_id, cache_hit,
                attempt_count, last_started_at, last_finished_at, updated_at
            ) VALUES (?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(candidate_id, provider) DO NOTHING
            ''',
            (candidate_id, provider, status, source_record_id),
        )

    def upsert_candidate_paper_link(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
        paper_id: str,
        relation_type: str,
        confidence: float,
        evidence_json: str,
    ) -> None:
        conn.execute(
            '''
            INSERT INTO candidate_paper_link (
                candidate_id, paper_id, relation_type, confidence, evidence_json
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(candidate_id, paper_id, relation_type) DO UPDATE SET
                confidence = excluded.confidence,
                evidence_json = excluded.evidence_json,
                created_at = CURRENT_TIMESTAMP
            ''',
            (candidate_id, paper_id, relation_type, confidence, evidence_json),
        )

    def upsert_candidate_resolution_status(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
        resolution_stage: str,
        resolution_rule: str | None,
        paper_id: str | None,
        leader_candidate_id: str | None,
        status: str,
        evidence_json: str | None,
    ) -> None:
        conn.execute(
            '''
            INSERT INTO candidate_resolution_status (
                candidate_id, resolution_stage, resolution_rule, paper_id,
                leader_candidate_id, status, evidence_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(candidate_id) DO UPDATE SET
                resolution_stage = excluded.resolution_stage,
                resolution_rule = excluded.resolution_rule,
                paper_id = excluded.paper_id,
                leader_candidate_id = excluded.leader_candidate_id,
                status = excluded.status,
                evidence_json = excluded.evidence_json,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (candidate_id, resolution_stage, resolution_rule, paper_id, leader_candidate_id, status, evidence_json),
        )

    def find_canonical_paper_by_field(self, conn: sqlite3.Connection, *, field_name: str, field_value: str):
        if field_name not in {'canonical_doi', 'canonical_pmid', 'canonical_pmcid'}:
            raise ValueError(f'unsupported canonical field lookup: {field_name}')
        return conn.execute(
            f'''SELECT paper_id FROM canonical_paper WHERE {field_name} = ? LIMIT 1''',
            (field_value,),
        ).fetchone()

    def find_paper_by_identity_alias(self, conn: sqlite3.Connection, *, alias_type: str, alias_key: str):
        return conn.execute(
            '''
            SELECT paper_id, confidence, source_stage
            FROM paper_identity_alias
            WHERE alias_type = ? AND alias_key = ?
            LIMIT 1
            ''',
            (alias_type, alias_key),
        ).fetchone()

    def upsert_paper_identity_alias(
        self,
        conn: sqlite3.Connection,
        *,
        paper_id: str,
        alias_type: str,
        alias_key: str,
        confidence: float,
        source_stage: str,
    ) -> None:
        conn.execute(
            '''
            INSERT INTO paper_identity_alias (
                paper_id, alias_type, alias_key, confidence, source_stage, updated_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(alias_type, alias_key) DO UPDATE SET
                confidence = CASE
                    WHEN paper_identity_alias.paper_id = excluded.paper_id THEN excluded.confidence
                    ELSE paper_identity_alias.confidence
                END,
                source_stage = CASE
                    WHEN paper_identity_alias.paper_id = excluded.paper_id THEN excluded.source_stage
                    ELSE paper_identity_alias.source_stage
                END,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (paper_id, alias_type, alias_key, confidence, source_stage),
        )

    def refresh_paper_identity_aliases_from_links(self, conn: sqlite3.Connection) -> int:
        rows = conn.execute(
            '''
            SELECT cpl.paper_id, pcn.doi_extracted, pcn.pmid_extracted, pcn.pmcid_extracted,
                   pcn.arxiv_id_extracted, pcn.url_canonical, pcn.scholar_cluster_hint
            FROM candidate_paper_link cpl
            JOIN paper_candidate_normalized pcn ON pcn.candidate_id = cpl.candidate_id
            '''
        ).fetchall()
        inserted = 0
        for row in rows:
            paper_id = row[0]
            alias_rows = [
                ('doi', row[1], 1.0),
                ('pmid', row[2], 1.0),
                ('pmcid', row[3], 1.0),
                ('arxiv', row[4], 0.99),
                ('url_canonical', row[5], 0.97),
                ('scholar_cluster', row[6], 0.98),
            ]
            for alias_type, alias_key, confidence in alias_rows:
                if alias_key is None or not str(alias_key).strip():
                    continue
                self.upsert_paper_identity_alias(
                    conn,
                    paper_id=paper_id,
                    alias_type=alias_type,
                    alias_key=str(alias_key).strip(),
                    confidence=confidence,
                    source_stage='dedup_backfill',
                )
                inserted += 1
        return inserted

    def get_paper_oa_status(self, conn: sqlite3.Connection, *, paper_id: str, provider: str):
        return conn.execute(
            '''
            SELECT id, status, query_type, query_key, cache_hit, attempt_count,
                   last_started_at, last_finished_at, latency_ms, error_summary, notes
            FROM paper_oa_enrichment_status
            WHERE paper_id = ? AND provider = ?
            LIMIT 1
            ''',
            (paper_id, provider),
        ).fetchone()

    def start_paper_oa_status(self, conn: sqlite3.Connection, *, paper_id: str, provider: str, query_type: str | None, query_key: str | None, notes: str | None = None) -> None:
        conn.execute(
            '''
            INSERT INTO paper_oa_enrichment_status (
                paper_id, provider, status, query_type, query_key, cache_hit,
                attempt_count, last_started_at, notes, updated_at
            ) VALUES (?, ?, 'pending', ?, ?, 0, 1, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(paper_id, provider) DO UPDATE SET
                status='pending',
                query_type=excluded.query_type,
                query_key=excluded.query_key,
                attempt_count=paper_oa_enrichment_status.attempt_count + 1,
                last_started_at=CURRENT_TIMESTAMP,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            ''',
            (paper_id, provider, query_type, query_key, notes),
        )

    def finish_paper_oa_status(self, conn: sqlite3.Connection, *, paper_id: str, provider: str, status: str, cache_hit: bool = False, latency_ms: int | None = None, error_summary: str | None = None, notes: str | None = None) -> None:
        conn.execute(
            '''
            UPDATE paper_oa_enrichment_status
            SET status = ?,
                cache_hit = ?,
                last_finished_at = CURRENT_TIMESTAMP,
                latency_ms = ?,
                error_summary = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE paper_id = ? AND provider = ?
            ''',
            (status, int(cache_hit), latency_ms, error_summary, notes, paper_id, provider),
        )

    def upsert_paper_open_access(
        self,
        conn: sqlite3.Connection,
        *,
        paper_id: str,
        provider: str,
        doi: str | None,
        is_oa: bool | None,
        oa_status: str | None,
        best_oa_url: str | None,
        best_oa_host_type: str | None,
        best_oa_version: str | None,
        license: str | None,
        raw_payload_json: str | None,
    ) -> None:
        conn.execute(
            '''
            INSERT INTO paper_open_access (
                paper_id, provider, doi, is_oa, oa_status, best_oa_url,
                best_oa_host_type, best_oa_version, license, raw_payload_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(paper_id) DO UPDATE SET
                provider=excluded.provider,
                doi=excluded.doi,
                is_oa=excluded.is_oa,
                oa_status=excluded.oa_status,
                best_oa_url=excluded.best_oa_url,
                best_oa_host_type=excluded.best_oa_host_type,
                best_oa_version=excluded.best_oa_version,
                license=excluded.license,
                raw_payload_json=excluded.raw_payload_json,
                updated_at=CURRENT_TIMESTAMP
            ''',
            (
                paper_id,
                provider,
                doi,
                None if is_oa is None else int(is_oa),
                oa_status,
                best_oa_url,
                best_oa_host_type,
                best_oa_version,
                license,
                raw_payload_json,
            ),
        )
