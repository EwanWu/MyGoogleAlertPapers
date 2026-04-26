from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.pipeline.local_import import import_local_body_snapshots


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


def test_repository_connect_enforces_sqlite_pragmas(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    repo = Repository(db_path)

    with repo.connect() as conn:
        assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert conn.execute('PRAGMA busy_timeout').fetchone()[0] == 5000
        assert conn.execute('PRAGMA journal_mode').fetchone()[0].lower() == 'wal'


def test_local_import_rerun_is_idempotent(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)
    input_path = tmp_path / 'local.jsonl'
    input_path.write_text(
        json.dumps({
            'mail_uid': 'local_mail_1',
            'message_id': '<local-mail-1@test>',
            'subject': 'New articles related to MRI',
            'from_address': 'scholaralerts-noreply@google.com',
            'body_text': 'Example body',
            'body_html': '<p>Example body</p>',
            'is_unread': True,
        }, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )

    first = import_local_body_snapshots(settings, input_path=input_path, limit=None, mailbox='INBOX', scan_mode='local_test')
    second = import_local_body_snapshots(settings, input_path=input_path, limit=None, mailbox='INBOX', scan_mode='local_test')

    assert first == {'processed': 1, 'imported': 1, 'skipped': 0, 'no_body': 0}
    assert second == {'processed': 1, 'imported': 0, 'skipped': 1, 'no_body': 0}

    with sqlite3.connect(db_path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM mail_ingestion_record').fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM raw_mail_snapshot').fetchone()[0] == 1


def test_canonical_identity_indexes_reject_duplicate_nonempty_ids(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)

    duplicate_cases = [
        ('canonical_doi', '10.1000/dup-doi'),
        ('canonical_pmid', '123456'),
        ('canonical_pmcid', 'PMC123456'),
    ]

    with sqlite3.connect(db_path) as conn:
        for idx, (column, value) in enumerate(duplicate_cases, start=1):
            conn.execute(
                f'''
                INSERT INTO canonical_paper (
                    paper_id, canonical_title, canonical_title_key, {column}
                ) VALUES (?, ?, ?, ?)
                ''',
                (f'paper_{idx}_a', f'Paper {idx}A', f'paper {idx}a', value),
            )
            try:
                conn.execute(
                    f'''
                    INSERT INTO canonical_paper (
                        paper_id, canonical_title, canonical_title_key, {column}
                    ) VALUES (?, ?, ?, ?)
                    ''',
                    (f'paper_{idx}_b', f'Paper {idx}B', f'paper {idx}b', value),
                )
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError(f'duplicate {column} should be rejected for non-empty values')
