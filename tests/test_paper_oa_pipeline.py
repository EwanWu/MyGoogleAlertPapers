from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.enrich.base import EnrichmentRecord, enrichment_record_to_json
from mygooglealertpapers.pipeline.paper_oa import enrich_paper_oa, build_paper_oa_stats


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


def test_enrich_paper_oa_writes_snapshot_from_live_query(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO canonical_paper (
                paper_id, canonical_title, canonical_title_key, canonical_doi
            ) VALUES (?, ?, ?, ?)
            ''',
            ('paper_live', 'Live OA Paper', 'live oa paper', '10.1000/live'),
        )
        conn.commit()

    def fake_query_unpaywall(candidate_id: str, *, doi: str | None, email: str | None = None, **kwargs):
        assert candidate_id == 'paper_live'
        assert doi == '10.1000/live'
        payload = {
            'doi': doi,
            'is_oa': True,
            'oa_status': 'gold',
            'best_oa_location': {
                'url': 'https://example.org/live.pdf',
                'host_type': 'publisher',
                'version': 'publishedVersion',
                'license': 'cc-by',
            },
        }
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='unpaywall',
            query_type='doi',
            query_string=doi,
            matched=True,
            match_score=1.0,
            external_id=doi,
            title='Live OA Paper',
            authors_json=None,
            abstract=None,
            venue=None,
            year='2026',
            publication_type='journal-article',
            doi=doi,
            pmid=None,
            pmcid=None,
            url='https://example.org/live.pdf',
            raw_payload_json=json.dumps(payload),
            latency_ms=123,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.paper_oa.query_unpaywall', fake_query_unpaywall)
    enrich_paper_oa(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            '''
            SELECT provider, doi, is_oa, oa_status, best_oa_url, best_oa_host_type, best_oa_version, license
            FROM paper_open_access
            WHERE paper_id = ?
            ''',
            ('paper_live',),
        ).fetchone()
        assert row == ('unpaywall', '10.1000/live', 1, 'gold', 'https://example.org/live.pdf', 'publisher', 'publishedVersion', 'cc-by')
        status_row = conn.execute(
            'SELECT status, cache_hit, latency_ms FROM paper_oa_enrichment_status WHERE paper_id = ?',
            ('paper_live',),
        ).fetchone()
        assert status_row == ('ok', 0, 123)

    report = build_paper_oa_stats(db_path)
    assert 'canonical papers with DOI: 1' in report
    assert 'best_oa_url filled rows: 1' in report
    assert 'gold: 1' in report


def test_enrich_paper_oa_reuses_query_cache(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    cached = EnrichmentRecord(
        candidate_id='candidate_old',
        source_name='unpaywall',
        query_type='doi',
        query_string='10.1000/cached',
        matched=True,
        match_score=1.0,
        external_id='10.1000/cached',
        title='Cached OA Paper',
        authors_json=None,
        abstract=None,
        venue=None,
        year='2026',
        publication_type='journal-article',
        doi='10.1000/cached',
        pmid=None,
        pmcid=None,
        url='https://example.org/cached.pdf',
        raw_payload_json=json.dumps({
            'doi': '10.1000/cached',
            'is_oa': True,
            'oa_status': 'hybrid',
            'best_oa_location': {
                'url': 'https://example.org/cached.pdf',
                'host_type': 'repository',
                'version': 'acceptedVersion',
                'license': 'cc-by-nc',
            },
        }),
        latency_ms=77,
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO canonical_paper (
                paper_id, canonical_title, canonical_title_key, canonical_doi
            ) VALUES (?, ?, ?, ?)
            ''',
            ('paper_cached', 'Cached OA Paper', 'cached oa paper', '10.1000/cached'),
        )
        conn.execute(
            '''
            INSERT INTO query_cache (provider, query_type, query_key, response_json)
            VALUES (?, ?, ?, ?)
            ''',
            ('unpaywall', 'doi', '10.1000/cached', enrichment_record_to_json(cached)),
        )
        conn.commit()

    def fail_query(*args, **kwargs):
        raise AssertionError('live Unpaywall query should not run when cache exists')

    monkeypatch.setattr('mygooglealertpapers.pipeline.paper_oa.query_unpaywall', fail_query)
    enrich_paper_oa(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            'SELECT oa_status, best_oa_url, best_oa_host_type, best_oa_version, license FROM paper_open_access WHERE paper_id = ?',
            ('paper_cached',),
        ).fetchone()
        assert row == ('hybrid', 'https://example.org/cached.pdf', 'repository', 'acceptedVersion', 'cc-by-nc')
        status_row = conn.execute(
            'SELECT status, cache_hit, latency_ms FROM paper_oa_enrichment_status WHERE paper_id = ?',
            ('paper_cached',),
        ).fetchone()
        assert status_row == ('ok', 1, 0)
