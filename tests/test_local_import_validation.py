from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.pipeline.local_import import import_local_body_snapshots, validate_local_body_input


def _make_settings(db_path: Path) -> Settings:
    profile = PolicyProfile(
        name='test_profile',
        path=None,
        provider_rules={},
        merge_rules={},
        replay_defaults={},
        raw={},
    )
    return Settings(
        imap_host=None,
        imap_port=993,
        imap_username=None,
        imap_password=None,
        imap_mailbox='INBOX',
        sqlite_path=db_path,
        log_level='INFO',
        workspace_root=db_path.parent,
        config_source='test',
        imap_account=None,
        crossref_mailto=None,
        openalex_email=None,
        semantic_scholar_api_key=None,
        unpaywall_email='unit@test.example',
        policy_profile=profile,
    )


def test_validate_local_body_input_writes_quarantine_for_corrupt_jsonl(tmp_path: Path):
    input_path = tmp_path / 'artifact.jsonl'
    quarantine_path = tmp_path / 'quarantine.jsonl'
    input_path.write_text(
        '\n'.join([
            json.dumps({'mail_uid': 'ok_1', 'body_text': 'body 1'}, ensure_ascii=False),
            '{bad json',
            json.dumps({'mail_uid': 'ok_2', 'body_text': 'body 2'}, ensure_ascii=False),
        ]) + '\n',
        encoding='utf-8',
    )

    summary = validate_local_body_input(input_path, quarantine_path=quarantine_path)

    assert summary['resolved_input_path'] == str(input_path)
    assert summary['valid_records'] == 2
    assert summary['invalid_lines'] == 1
    assert summary['invalid_line_numbers'] == [2]
    assert summary['invalid_jsonl_path'] == str(quarantine_path)

    quarantine_rows = [json.loads(line) for line in quarantine_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(quarantine_rows) == 1
    assert quarantine_rows[0]['line_no'] == 2
    assert '{bad json' in quarantine_rows[0]['raw_line']


def test_import_local_body_snapshots_skips_corrupt_jsonl_lines_and_imports_valid_rows(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)
    input_path = tmp_path / 'artifact.jsonl'
    quarantine_path = tmp_path / 'artifact_invalid.jsonl'
    input_path.write_text(
        '\n'.join([
            json.dumps({
                'mail_uid': 'ok_1',
                'message_id': '<ok1@test>',
                'subject': 'New articles related to MRI',
                'from_address': 'scholaralerts-noreply@google.com',
                'body_text': 'body 1',
                'body_html': '<p>body 1</p>',
            }, ensure_ascii=False),
            '\x00\x00\x00',
            json.dumps({
                'mail_uid': 'ok_2',
                'message_id': '<ok2@test>',
                'subject': 'New articles related to MRI',
                'from_address': 'scholaralerts-noreply@google.com',
                'body_text': 'body 2',
                'body_html': '<p>body 2</p>',
            }, ensure_ascii=False),
        ]) + '\n',
        encoding='utf-8',
    )

    result = import_local_body_snapshots(
        settings,
        input_path=input_path,
        limit=None,
        mailbox='LOCAL_163',
        scan_mode='local_json_import',
        quarantine_path=quarantine_path,
    )

    assert result['processed'] == 2
    assert result['valid_records'] == 2
    assert result['invalid_lines'] == 1
    assert result['invalid_line_numbers'] == [2]
    assert result['invalid_jsonl_path'] == str(quarantine_path)
    assert result['imported'] == 2
    assert result['skipped'] == 0

    with sqlite3.connect(db_path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM mail_ingestion_record').fetchone()[0] == 2
        assert conn.execute('SELECT COUNT(*) FROM raw_mail_snapshot').fetchone()[0] == 2


def test_import_local_body_snapshots_prefers_reconciled_jsonl_when_present(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)
    raw_path = tmp_path / 'scholar_body_fetch_20260424_full.jsonl'
    reconciled_path = tmp_path / 'scholar_body_fetch_20260424_full_reconciled.jsonl'

    raw_path.write_text(
        json.dumps({'mail_uid': 'raw_only', 'body_text': 'raw body'}, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    reconciled_path.write_text(
        json.dumps({
            'mail_uid': 'reconciled_only',
            'message_id': '<reconciled@test>',
            'subject': 'New articles related to MRI',
            'from_address': 'scholaralerts-noreply@google.com',
            'body_text': 'reconciled body',
            'body_html': '<p>reconciled body</p>',
        }, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )

    result = import_local_body_snapshots(
        settings,
        input_path=raw_path,
        limit=None,
        mailbox='LOCAL_163',
        scan_mode='local_json_import',
    )

    assert result['requested_input_path'] == str(raw_path)
    assert result['resolved_input_path'] == str(reconciled_path)
    assert result['used_reconciled_input'] is True
    assert result['canonical_reconciled_path'] == str(reconciled_path)
    assert result['processed'] == 1
    assert result['imported'] == 1

    with sqlite3.connect(db_path) as conn:
        row = conn.execute('SELECT mail_uid FROM mail_ingestion_record').fetchone()
        assert row == ('reconciled_only',)
