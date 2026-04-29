from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.enrich.base import EnrichmentRecord
from mygooglealertpapers.pipeline.enrich import enrich_candidates


def _make_settings(
    db_path: Path,
    *,
    provider_rules: dict[str, dict[str, object]] | None = None,
    runtime_rules: dict[str, object] | None = None,
) -> Settings:
    profile = PolicyProfile(
        name='test_profile',
        path=None,
        provider_rules=provider_rules or {
            'crossref': {'enabled': True},
            'openalex': {'enabled': False},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        merge_rules={},
        runtime_rules=runtime_rules or {},
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
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.PROGRESS_EVERY', 1)

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
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['dispatch_group_count'] == 1
        assert stats['dispatch_request_count'] == 1
        assert stats['request_savings_vs_runnable_intents'] == 1
        assert stats['shared_title_reuse_group_count'] == 0
        assert stats['shared_title_reuse_request_savings'] == 0


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


def test_experimental_title_payload_reuse_shares_request_without_relaxing_match(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)
    settings.policy_profile.provider_rules['crossref']['title_payload_reuse_enabled'] = True

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand_exp1', 'Experimental Shared Title', 'experimental shared title', 'Wu', 'Nature', '2026'),
                ('cand_exp2', 'Experimental Shared Title', 'experimental shared title', 'Li', 'Nature', '2025'),
            ],
        )
        conn.commit()

    calls = {'count': 0}

    def fake_fetch_crossref_title_item(title: str, *, mailto: str | None = None):
        calls['count'] += 1
        item = {
            'DOI': '10.1000/exp',
            'title': ['Experimental Shared Title'],
            'author': [{'given': 'Yue', 'family': 'Wu'}],
            'container-title': ['Nature'],
            'published-print': {'date-parts': [[2026]]},
            'type': 'journal-article',
            'URL': 'https://doi.org/10.1000/exp',
        }
        return item, json.dumps(item, ensure_ascii=False), 42

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.fetch_crossref_title_item', fake_fetch_crossref_title_item)

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
            ('cand_exp1', 'ok', 0, 42),
            ('cand_exp2', 'no_match', 0, 0),
        ]
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['dispatch_group_count'] == 1
        assert stats['dispatch_request_count'] == 1
        assert stats['request_savings_vs_runnable_intents'] == 1
        assert stats['shared_title_reuse_group_count'] == 1
        assert stats['shared_title_reuse_intent_count'] == 2
        assert stats['shared_title_reuse_request_count'] == 1
        assert stats['shared_title_reuse_request_savings'] == 1


def test_enrich_candidates_identifier_fastpath_lane_filters_slow_title_fallbacks(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': False},
            'semanticscholar': {'enabled': True},
            'pubmed': {'enabled': True},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['identifier_fastpath'],
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, doi_extracted, pmid_extracted,
                first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_lane', 'Lane Controlled Paper', 'lane controlled paper', '10.1000/lane', '123456', 'Wu', 'Nature', '2026'),
        )
        conn.commit()

    calls = {'crossref': 0, 'pubmed': 0, 'semanticscholar': 0}

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['crossref'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='doi',
            query_string='10.1000/lane',
            matched=True,
            match_score=1.0,
            external_id='crossref:lane',
            title='Lane Controlled Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/lane',
            pmid='123456',
            pmcid=None,
            url='https://doi.org/10.1000/lane',
            raw_payload_json=json.dumps({'status': 'ok'}, ensure_ascii=False),
            latency_ms=11,
        )

    def fake_query_pubmed(candidate_id: str, **kwargs):
        calls['pubmed'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='pubmed',
            query_type='pmid',
            query_string='123456',
            matched=True,
            match_score=1.0,
            external_id='pubmed:123456',
            title='Lane Controlled Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/lane',
            pmid='123456',
            pmcid=None,
            url='https://pubmed.ncbi.nlm.nih.gov/123456/',
            raw_payload_json=json.dumps({'status': 'ok'}, ensure_ascii=False),
            latency_ms=7,
        )

    def fake_query_semanticscholar(candidate_id: str, **kwargs):
        calls['semanticscholar'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='semanticscholar',
            query_type='doi',
            query_string='10.1000/lane',
            matched=True,
            match_score=1.0,
            external_id='s2:lane',
            title='Lane Controlled Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/lane',
            pmid='123456',
            pmcid=None,
            url='https://api.semanticscholar.org/lane',
            raw_payload_json=json.dumps({'status': 'ok'}, ensure_ascii=False),
            latency_ms=99,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_pubmed', fake_query_pubmed)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_semanticscholar', fake_query_semanticscholar)

    enrich_candidates(settings, limit=10)

    assert calls == {'crossref': 1, 'pubmed': 1, 'semanticscholar': 0}
    with sqlite3.connect(db_path) as conn:
        providers = conn.execute(
            'SELECT provider FROM candidate_enrichment_status ORDER BY provider'
        ).fetchall()
        assert providers == [('crossref',), ('pubmed',)]
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['enabled_lanes'] == ['identifier_fastpath']
        assert stats['lane_group_counts'] == {'identifier_fastpath': 2}
        assert stats['lane_processed_intents'] == {'identifier_fastpath': 2}


def test_enrich_candidates_stops_lane_after_request_budget(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': False},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'lane_request_budgets': {'title_core': 1},
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand_budget1', 'Budget Title One', 'budget title one', 'Wu', 'Nature', '2026'),
                ('cand_budget2', 'Budget Title Two', 'budget title two', 'Wu', 'Nature', '2026'),
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
            query_string='Budget Title One',
            matched=True,
            match_score=0.99,
            external_id='crossref:budget',
            title='Budget Title One',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/budget',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/budget',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/budget'}, ensure_ascii=False),
            latency_ms=42,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    assert calls['count'] == 1
    with sqlite3.connect(db_path) as conn:
        source_count = conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE source_name = ?',
            ('crossref',),
        ).fetchone()[0]
        assert source_count == 1
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['lane_request_budgets'] == {'title_core': 1}
        assert stats['lane_dispatch_request_count'] == {'title_core': 1}
        assert stats['lane_processed_intents'] == {'title_core': 1}
        assert stats['lane_stop_reasons'] == {'title_core': 'request_budget_exhausted'}
        assert stats['lane_skipped_group_count'] == {'title_core': 1}
        assert stats['lane_skipped_intents'] == {'title_core': 1}


def test_enrich_candidates_cache_hits_do_not_consume_lane_budget(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    base_settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            ('cand_cache_budget', 'Cached Budget Title', 'cached budget title', 'Wu', 'Nature', '2026'),
        )
        conn.commit()

    calls = {'count': 0}

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['count'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string='Cached Budget Title',
            matched=True,
            match_score=0.99,
            external_id='crossref:cached-budget',
            title='Cached Budget Title',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/cached-budget',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/cached-budget',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/cached-budget'}, ensure_ascii=False),
            latency_ms=42,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)
    enrich_candidates(base_settings, limit=10)
    assert calls['count'] == 1

    with sqlite3.connect(db_path) as conn:
        conn.execute('DELETE FROM candidate_enrichment_status WHERE candidate_id = ?', ('cand_cache_budget',))
        conn.execute('DELETE FROM source_record WHERE candidate_id = ?', ('cand_cache_budget',))
        conn.execute('DELETE FROM cost_event')
        conn.execute('DELETE FROM batch_run')
        conn.commit()

    budget_settings = _make_settings(
        db_path,
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'lane_request_budgets': {'title_core': 0},
        },
    )

    def unexpected_query_crossref(candidate_id: str, **kwargs):
        raise AssertionError('cache hit should not trigger a provider request')

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', unexpected_query_crossref)
    enrich_candidates(budget_settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        source_count = conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ? AND source_name = ?',
            ('cand_cache_budget', 'crossref'),
        ).fetchone()[0]
        assert source_count == 1
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['lane_request_budgets'] == {'title_core': 0}
        assert stats['lane_dispatch_request_count'] == {'title_core': 0}
        assert stats['dispatch_request_count'] == 0
        assert stats['cache_hit_group_count'] == 1
        assert stats['processed_runnable_intents'] == 1
        assert stats['lane_processed_intents'] == {'title_core': 1}
        assert stats['lane_stop_reasons'] == {}
