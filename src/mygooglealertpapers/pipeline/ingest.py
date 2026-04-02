from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.mail.candidate_extractor import extract_candidates
from mygooglealertpapers.mail.imap_client import ImapMailboxClient
from mygooglealertpapers.mail.message_parser import ParsedEmail, parse_raw_email
from mygooglealertpapers.mail.scholar_detector import detect_google_scholar_alert

logger = logging.getLogger(__name__)


def _write_snapshot_file(settings: Settings, mail_uid: str, parsed: ParsedEmail) -> str:
    snapshot_dir = settings.workspace_root / "data" / "raw_mail_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"{mail_uid}.json"
    payload = {
        "mail_uid": mail_uid,
        "message_id": parsed.message_id,
        "subject": parsed.subject,
        "from_address": parsed.from_address,
        "headers": parsed.headers,
        "body_text": parsed.body_text,
        "body_html": parsed.body_html,
        "body_hash": parsed.body_hash,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def scan_and_store_messages(settings: Settings, *, limit: int, unseen_only: bool) -> None:
    if not settings.imap_host or not settings.imap_username or not settings.imap_password:
        raise RuntimeError("IMAP credentials are missing. Set IMAP_HOST, IMAP_USERNAME, and IMAP_PASSWORD.")

    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    client = ImapMailboxClient(
        host=settings.imap_host,
        port=settings.imap_port,
        username=settings.imap_username,
        password=settings.imap_password,
        mailbox=settings.imap_mailbox,
    )
    client.connect()
    try:
        stubs = client.fetch_message_metadata(limit=limit, unseen_only=unseen_only)
        logger.info("Fetched %s message(s) from mailbox=%s unseen_only=%s", len(stubs), settings.imap_mailbox, unseen_only)
        with repo.connect() as conn:
            for stub in stubs:
                started = time.perf_counter()
                parsed = parse_raw_email(stub.raw_message)
                detection = detect_google_scholar_alert(parsed)
                snapshot_path = _write_snapshot_file(settings, stub.uid, parsed)
                repo.insert_mail_ingestion_record(
                    conn,
                    mail_uid=stub.uid,
                    message_id=parsed.message_id,
                    mailbox=settings.imap_mailbox,
                    internal_date=stub.internal_date,
                    from_address=parsed.from_address,
                    subject=parsed.subject,
                    is_unseen_at_scan=("\\Seen" not in stub.flags),
                    scan_mode="readonly+BODY.PEEK",
                    is_google_scholar_alert=detection.is_match,
                    parse_status="parsed",
                    num_candidates_extracted=None,
                    wall_time_ms=int((time.perf_counter() - started) * 1000),
                )
                repo.insert_raw_mail_snapshot(conn, mail_uid=stub.uid, parsed_email=parsed, snapshot_path=snapshot_path)
                tracker.record_stage_cost(conn, stage="scan", status="ok", mail_uid=stub.uid, notes=detection.reason)
            conn.commit()
    finally:
        client.close()


def parse_and_extract_candidates(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    with repo.connect() as conn:
        uids = repo.list_unparsed_scholar_mail_uids(conn, limit=limit)
        logger.info("Found %s unparsed Scholar mail(s)", len(uids))
        for uid in uids:
            snapshot = repo.get_raw_mail_snapshot_by_uid(conn, uid)
            if snapshot is None:
                tracker.record_stage_cost(conn, stage="extract_candidates", status="missing_snapshot", mail_uid=uid)
                continue
            body_text, body_html = snapshot
            parsed_email = ParsedEmail(
                message_id=None,
                subject=None,
                from_address=None,
                headers={},
                body_text=body_text or "",
                body_html=body_html or "",
                body_hash="",
            )
            candidates = extract_candidates(parsed_email, mail_uid=uid)
            if candidates:
                repo.insert_paper_candidates(conn, candidates)
                repo.update_mail_candidate_count(conn, mail_uid=uid, num_candidates_extracted=len(candidates))
                tracker.record_stage_cost(conn, stage="extract_candidates", status="ok", mail_uid=uid, notes=f"count={len(candidates)}")
            else:
                repo.update_mail_candidate_count(conn, mail_uid=uid, num_candidates_extracted=0)
                tracker.record_stage_cost(conn, stage="extract_candidates", status="no_candidates", mail_uid=uid)
        conn.commit()
