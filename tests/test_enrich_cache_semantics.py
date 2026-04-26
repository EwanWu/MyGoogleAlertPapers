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
