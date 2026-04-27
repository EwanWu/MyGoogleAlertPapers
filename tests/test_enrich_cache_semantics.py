from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.enrich.base import EnrichmentRecord
from mygooglealertpapers.pipeline.enrich import enrich_candidates


def _make_settings(db_path: Path) -> Settings:
    profile = PolicyProfile(
        name='test_profile',
        path=None,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': False},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
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
        crossref_mailto='unit@test.example',
        openalex_email=None,
        semantic_scholar_api_key=None,
        unpaywall_email=None,
        policy_profile=profile,
    )


def test_enrich_candidates_retries_after_transient_provider_error(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            ('cand_retry', 'Retryable Paper', 'retryable paper', 'Wu', 'Nature', '2026'),
        )
        conn.commit()

    calls = {'count': 0}

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['count'] += 1
        if calls['count'] == 1:
            raise RuntimeError('temporary upstream failure')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string='Retryable Paper',
            matched=True,
            match_score=0.99,
            external_id='crossref:retryable',
            title='Retryable Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/retryable',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/retryable',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/retryable'}, ensure_ascii=False),
            latency_ms=42,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        status_row = conn.execute(
            'SELECT status, attempt_count FROM candidate_enrichment_status WHERE candidate_id = ? AND provider = ?',
            ('cand_retry', 'crossref'),
        ).fetchone()
        assert status_row == ('error', 1)
        cache_row = conn.execute(
            'SELECT cache_status, error_type FROM query_cache WHERE provider = ? AND query_type = ? AND query_key = ?',
            ('crossref', 'title', 'Retryable Paper'),
        ).fetchone()
        assert cache_row == ('transient_error', 'provider_error')

    enrich_candidates(settings, limit=10)

    assert calls['count'] == 2
    with sqlite3.connect(db_path) as conn:
        status_row = conn.execute(
            'SELECT status, attempt_count, cache_hit FROM candidate_enrichment_status WHERE candidate_id = ? AND provider = ?',
            ('cand_retry', 'crossref'),
        ).fetchone()
        assert status_row == ('ok', 2, 0)
        cache_row = conn.execute(
            'SELECT cache_status, error_type FROM query_cache WHERE provider = ? AND query_type = ? AND query_key = ?',
            ('crossref', 'title', 'Retryable Paper'),
        ).fetchone()
        assert cache_row == ('positive_match', None)
        source_count = conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ? AND source_name = ?',
            ('cand_retry', 'crossref'),
        ).fetchone()[0]
        assert source_count == 1


def test_enrich_candidates_dispatch_dedups_identical_title_queries(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand_dup1', 'Duplicate Title Paper', 'duplicate title paper', 'Wu', 'Nature', '2026'),
                ('cand_dup2', 'Duplicate Title Paper', 'duplicate title paper', 'Wu', 'Nature', '2026'),
            ],
        )
        conn.commit()

    calls = {'count': 0}

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['count'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string='Duplicate Title Paper',
            matched=True,
            match_score=0.99,
            external_id='crossref:dup',
            title='Duplicate Title Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/dup',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/dup',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/dup'}, ensure_ascii=False),
            latency_ms=42,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    assert calls['count'] == 1
    with sqlite3.connect(db_path) as conn:
        statuses = conn.execute(
            '''
            SELECT candidate_id, status, cache_hit, latency_ms
            FROM candidate_enrichment_status
            WHERE provider = 'crossref'
            ORDER BY candidate_id
            '''
        ).fetchall()
        assert statuses == [
            ('cand_dup1', 'ok', 0, 42),
            ('cand_dup2', 'ok', 0, 0),
        ]
        source_count = conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE source_name = ?',
            ('crossref',),
        ).fetchone()[0]
        assert source_count == 2
        cache_row = conn.execute(
            'SELECT cache_status FROM query_cache WHERE provider = ? AND query_type = ? AND query_key = ?',
            ('crossref', 'title', 'Duplicate Title Paper'),
        ).fetchone()
        assert cache_row == ('positive_match',)
        total_latency = conn.execute(
            'SELECT COALESCE(SUM(latency_ms), 0) FROM cost_event WHERE provider = ?',
            ('crossref',),
        ).fetchone()[0]
        assert total_latency == 42


def test_enrich_candidates_uses_context_aware_cache_keys_for_mismatched_title_context(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand_ctx1', 'Shared But Context-Sensitive Title', 'shared but context-sensitive title', 'Wu', 'Nature', '2026'),
                ('cand_ctx2', 'Shared But Context-Sensitive Title', 'shared but context-sensitive title', 'Li', 'Nature', '2025'),
            ],
        )
        conn.commit()

    calls = {'count': 0}

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['count'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string='Shared But Context-Sensitive Title',
            matched=True,
            match_score=0.99,
            external_id='crossref:ctx',
            title='Shared But Context-Sensitive Title',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/ctx',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/ctx',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/ctx'}, ensure_ascii=False),
            latency_ms=42,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    assert calls['count'] == 2
    with sqlite3.connect(db_path) as conn:
        statuses = conn.execute(
            '''
            SELECT candidate_id, status, cache_hit, latency_ms
            FROM candidate_enrichment_status
            WHERE provider = 'crossref'
            ORDER BY candidate_id
            '''
        ).fetchall()
        assert statuses == [
            ('cand_ctx1', 'ok', 0, 42),
            ('cand_ctx2', 'ok', 0, 42),
        ]
        cache_key_count = conn.execute(
            '''
            SELECT COUNT(DISTINCT field_set_hash)
            FROM query_cache
            WHERE provider = ? AND query_type = ? AND query_key = ?
            ''',
            ('crossref', 'title', 'Shared But Context-Sensitive Title'),
        ).fetchone()[0]
        assert cache_key_count == 2
