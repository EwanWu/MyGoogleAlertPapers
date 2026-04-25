from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.mail.message_parser import ParsedEmail
from mygooglealertpapers.mail.scholar_detector import detect_google_scholar_alert

logger = logging.getLogger(__name__)


def _iter_input_records(input_path: Path) -> Iterable[dict[str, Any]]:
    if input_path.suffix.lower() == '.jsonl':
        for line_no, line in enumerate(input_path.read_text(encoding='utf-8').splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f'invalid JSONL at line {line_no}: {exc}') from exc
            if not isinstance(payload, dict):
                raise ValueError(f'line {line_no} is not a JSON object')
            yield payload
        return

    payload = json.loads(input_path.read_text(encoding='utf-8'))
    if isinstance(payload, dict):
        records = payload.get('records')
        if isinstance(records, list):
            for item in records:
                if not isinstance(item, dict):
                    raise ValueError('records array must contain JSON objects')
                yield item
            return
        yield payload
        return
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError('JSON array input must contain objects')
            yield item
        return
    raise ValueError('unsupported input format, expected JSON object/list or JSONL object lines')


def _coerce_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _record_mail_uid(record: dict[str, Any]) -> str:
    explicit = _coerce_text(record.get('mail_uid'))
    if explicit:
        return explicit
    identity_parts = [
        _coerce_text(record.get('message_id')),
        _coerce_text(record.get('mail_key')),
        _coerce_text(record.get('subject')),
        _coerce_text(record.get('internal_date')),
        _coerce_text(record.get('date_text')),
    ]
    identity = '|'.join(part for part in identity_parts if part)
    if not identity:
        identity = json.dumps(
            {
                'subject': record.get('subject'),
                'body_text': record.get('body_text'),
                'body_html': record.get('body_html'),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    digest = hashlib.sha1(identity.encode('utf-8')).hexdigest()[:16]
    return f'local_{digest}'


def _record_headers(record: dict[str, Any]) -> dict[str, str]:
    headers = record.get('headers')
    if isinstance(headers, dict):
        return {str(k): str(v) for k, v in headers.items()}
    result: dict[str, str] = {}
    for key in ['message_id', 'subject', 'from_address', 'internal_date', 'date_text', 'url', 'mail_key']:
        value = _coerce_text(record.get(key))
        if value:
            result[key] = value
    return result


def _record_body_hash(body_text: str | None, body_html: str | None) -> str:
    payload = json.dumps({'body_text': body_text or '', 'body_html': body_html or ''}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _snapshot_payload(mail_uid: str, record: dict[str, Any], parsed_email: ParsedEmail) -> dict[str, Any]:
    return {
        'mail_uid': mail_uid,
        'message_id': parsed_email.message_id,
        'subject': parsed_email.subject,
        'from_address': parsed_email.from_address,
        'headers': parsed_email.headers,
        'body_text': parsed_email.body_text,
        'body_html': parsed_email.body_html,
        'body_hash': parsed_email.body_hash,
        'source_record': {
            'mail_key': record.get('mail_key'),
            'page_no': record.get('page_no'),
            'row_index': record.get('row_index'),
            'date_text': record.get('date_text'),
            'url': record.get('url'),
            'snapshot_path': record.get('snapshot_path') or record.get('source_path'),
        },
    }


def _write_import_snapshot(settings: Settings, mail_uid: str, record: dict[str, Any], parsed_email: ParsedEmail) -> str:
    snapshot_dir = settings.workspace_root / 'data' / 'raw_mail_snapshots' / 'local_import'
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f'{mail_uid}.json'
    path.write_text(json.dumps(_snapshot_payload(mail_uid, record, parsed_email), ensure_ascii=False, indent=2), encoding='utf-8')
    return str(path)


def _already_imported(conn, *, mail_uid: str, message_id: str | None) -> bool:
    row = conn.execute(
        'SELECT 1 FROM mail_ingestion_record WHERE mail_uid = ? ORDER BY id DESC LIMIT 1',
        (mail_uid,),
    ).fetchone()
    if row is not None:
        return True
    if message_id:
        row = conn.execute(
            'SELECT 1 FROM mail_ingestion_record WHERE message_id = ? ORDER BY id DESC LIMIT 1',
            (message_id,),
        ).fetchone()
        if row is not None:
            return True
    return False


def import_local_body_snapshots(
    settings: Settings,
    *,
    input_path: Path,
    limit: int | None,
    mailbox: str,
    scan_mode: str,
) -> dict[str, int]:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'import_local_bodies_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    imported = 0
    skipped = 0
    no_body = 0

    records = list(_iter_input_records(input_path))
    if limit is not None:
        records = records[:limit]

    with repo.connect() as conn:
        repo.start_batch_run(
            conn,
            run_id=run_id,
            stage='import_local_bodies',
            requested_limit=limit,
            notes=f'input={input_path}',
        )
        for record in records:
            subject = _coerce_text(record.get('subject'))
            from_address = _coerce_text(record.get('from_address') or record.get('sender'))
            message_id = _coerce_text(record.get('message_id'))
            internal_date = _coerce_text(record.get('internal_date') or record.get('date_text'))
            body_text = _coerce_text(record.get('body_text')) or ''
            body_html = _coerce_text(record.get('body_html')) or ''
            mail_uid = _record_mail_uid(record)

            if not body_text and not body_html:
                no_body += 1
                tracker.record_stage_cost(conn, stage='import_local_bodies', status='no_body', mail_uid=mail_uid)
                continue

            parsed_email = ParsedEmail(
                message_id=message_id,
                subject=subject,
                from_address=from_address,
                headers=_record_headers(record),
                body_text=body_text,
                body_html=body_html,
                body_hash=_record_body_hash(body_text, body_html),
            )
            detection = detect_google_scholar_alert(parsed_email)

            if _already_imported(conn, mail_uid=mail_uid, message_id=parsed_email.message_id):
                skipped += 1
                tracker.record_stage_cost(conn, stage='import_local_bodies', status='duplicate_skip', mail_uid=mail_uid, notes=detection.reason)
                continue

            snapshot_path = _write_import_snapshot(settings, mail_uid, record, parsed_email)
            repo.insert_mail_ingestion_record(
                conn,
                mail_uid=mail_uid,
                message_id=parsed_email.message_id,
                mailbox=mailbox,
                internal_date=internal_date,
                from_address=from_address,
                subject=subject,
                is_unseen_at_scan=bool(record.get('is_unread', True)),
                scan_mode=scan_mode,
                is_google_scholar_alert=detection.is_match,
                parse_status='parsed',
                num_candidates_extracted=None,
                wall_time_ms=None,
            )
            repo.insert_raw_mail_snapshot(conn, mail_uid=mail_uid, parsed_email=parsed_email, snapshot_path=snapshot_path)
            tracker.record_stage_cost(conn, stage='import_local_bodies', status='ok', mail_uid=mail_uid, notes=detection.reason)
            imported += 1

        repo.finish_batch_run(
            conn,
            run_id=run_id,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            processed_count=len(records),
            status='ok',
            notes=f'imported={imported}; skipped={skipped}; no_body={no_body}',
        )
        conn.commit()

    logger.info(
        'Local body import finished: input=%s processed=%s imported=%s skipped=%s no_body=%s',
        input_path,
        len(records),
        imported,
        skipped,
        no_body,
    )
    return {
        'processed': len(records),
        'imported': imported,
        'skipped': skipped,
        'no_body': no_body,
    }
