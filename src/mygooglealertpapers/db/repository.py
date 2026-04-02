from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.mail.candidate_extractor import PaperCandidateRaw
from mygooglealertpapers.mail.message_parser import ParsedEmail


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

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
            INSERT INTO mail_ingestion_record (
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
            INSERT INTO raw_mail_snapshot (mail_uid, header_json, body_text, body_html, body_hash, snapshot_path)
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
            (num_candidates_extracted, "candidates_extracted", mail_uid),
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
