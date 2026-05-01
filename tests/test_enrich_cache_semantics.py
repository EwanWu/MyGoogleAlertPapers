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


def test_enrich_candidates_records_title_lane_reason_and_provider_stats(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True, 'title_payload_reuse_enabled': True},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={'same_batch_clustering_enabled': True, 'library_prelink_enabled': False},
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, pmid_extracted, pmcid_extracted,
                arxiv_id_extracted, first_author_family, venue_guess, year_guess,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand_plain', 'Plain Residual Title', 'plain residual title', None, None, None, 'Wu', 'Nature', '2026', None, None),
                ('cand_pmid', 'PMID Residual Title', 'pmid residual title', '123456', None, None, 'Wu', 'Nature', '2026', None, None),
                ('cand_pmcid', 'PMCID Residual Title', 'pmcid residual title', None, 'PMC123456', None, 'Wu', 'Nature', '2026', None, None),
                ('cand_url', 'URL Residual Title', 'url residual title', None, None, None, 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only', None),
                ('cand_scholar', 'Scholar Residual Title', 'scholar residual title', None, None, None, 'Wu', 'Nature', '2026', None, 'https://scholar.google.com/scholar?cluster=1234567890'),
                ('cand_arxiv', 'Arxiv Residual Title', 'arxiv residual title', None, None, '2401.12345', 'Wu', 'Nature', '2026', None, None),
                ('cand_mixed', 'Mixed Residual Title', 'mixed residual title', '555555', None, None, 'Wu', 'Nature', '2026', 'https://example.org/paper/mixed', None),
                ('cand_leader', 'Cluster Residual Leader', 'cluster residual leader', None, None, None, 'Wu', 'Nature', '2026', 'https://example.org/paper/cluster', None),
                ('cand_follower', 'Cluster Residual Follower', 'cluster residual follower', None, None, None, 'Wu', 'Nature', '2026', 'https://example.org/paper/cluster', None),
            ],
        )
        conn.commit()

    def fake_query_crossref(candidate_id: str, **kwargs):
        title = kwargs.get('title') or 'unknown'
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string=title,
            matched=True,
            match_score=0.99,
            external_id=f'crossref:{candidate_id}',
            title=title,
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi=f'10.1000/{candidate_id}',
            pmid=kwargs.get('pmid'),
            pmcid=None,
            url=f'https://doi.org/10.1000/{candidate_id}',
            raw_payload_json=json.dumps({'status': 'ok', 'provider': 'crossref'}, ensure_ascii=False),
            latency_ms=31,
        )

    def fake_fetch_crossref_title_item(title: str, *, mailto: str | None = None):
        item = {
            'DOI': '10.1000/cluster-shared',
            'title': [title],
            'author': [{'given': 'Yue', 'family': 'Wu'}],
            'container-title': ['Nature'],
            'published-print': {'date-parts': [[2026]]},
            'type': 'journal-article',
            'URL': 'https://doi.org/10.1000/cluster-shared',
        }
        return item, json.dumps(item, ensure_ascii=False), 41

    def fake_query_openalex(candidate_id: str, **kwargs):
        title = kwargs.get('title') or 'unknown'
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string=title,
            matched=True,
            match_score=0.98,
            external_id=f'openalex:{candidate_id}',
            title=title,
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi=f'10.2000/{candidate_id}',
            pmid=kwargs.get('pmid'),
            pmcid=None,
            url=f'https://openalex.org/{candidate_id}',
            raw_payload_json=json.dumps({'status': 'ok', 'provider': 'openalex'}, ensure_ascii=False),
            latency_ms=19,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.fetch_crossref_title_item', fake_fetch_crossref_title_item)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)

    enrich_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['same_batch_clustering_enabled'] is True
        assert stats['same_batch_cluster_group_count'] == 1
        assert stats['title_lane_group_count'] == 16
        assert stats['title_lane_request_count'] == 16
        assert stats['title_lane_post_prelink_residual_group_count'] == 16
        assert stats['title_lane_post_prelink_residual_request_count'] == 16
        assert stats['title_lane_group_counts_by_reason'] == {
            'no_identifier_available': 2,
            'identifier_present_but_not_sufficient_for_provider_path': 12,
            'cluster_leader_path': 2,
        }
        assert stats['title_lane_request_counts_by_reason'] == {
            'no_identifier_available': 2,
            'identifier_present_but_not_sufficient_for_provider_path': 12,
            'cluster_leader_path': 2,
        }
        assert stats['title_lane_group_counts_by_provider'] == {'crossref': 8, 'openalex': 8}
        assert stats['title_lane_request_counts_by_provider'] == {'crossref': 8, 'openalex': 8}
        assert stats['title_lane_identifier_gap_group_counts_by_subreason'] == {
            'pmid_without_doi': 2,
            'pmcid_only': 2,
            'url_canonical_only': 2,
            'scholar_cluster_only': 2,
            'arxiv_only': 2,
            'mixed_non_doi_identifier': 2,
        }
        assert stats['title_lane_identifier_gap_request_counts_by_subreason'] == {
            'pmid_without_doi': 2,
            'pmcid_only': 2,
            'url_canonical_only': 2,
            'scholar_cluster_only': 2,
            'arxiv_only': 2,
            'mixed_non_doi_identifier': 2,
        }
        assert stats['title_lane_identifier_gap_group_counts_by_provider_subreason'] == {
            'crossref': {
                'pmid_without_doi': 1,
                'pmcid_only': 1,
                'url_canonical_only': 1,
                'scholar_cluster_only': 1,
                'arxiv_only': 1,
                'mixed_non_doi_identifier': 1,
            },
            'openalex': {
                'pmid_without_doi': 1,
                'pmcid_only': 1,
                'url_canonical_only': 1,
                'scholar_cluster_only': 1,
                'arxiv_only': 1,
                'mixed_non_doi_identifier': 1,
            },
        }
        assert stats['title_lane_request_counts_by_provider_reason'] == {
            'crossref': {
                'no_identifier_available': 1,
                'identifier_present_but_not_sufficient_for_provider_path': 6,
                'cluster_leader_path': 1,
            },
            'openalex': {
                'no_identifier_available': 1,
                'identifier_present_but_not_sufficient_for_provider_path': 6,
                'cluster_leader_path': 1,
            },
        }
        assert stats['shared_title_reuse_request_savings'] == 1
        assert stats['shared_title_reuse_request_savings_by_provider'] == {'crossref': 1}


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


def test_enrich_candidates_can_experimentally_skip_crossref_url_only_title_fallback(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'title_lane_skip_subreasons_by_provider': {
                'crossref': ['url_canonical_only'],
            },
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_url_only', 'URL Only Paper', 'url only paper', 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only'),
        )
        conn.commit()

    calls = {'crossref': 0, 'openalex': 0}

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['crossref'] += 1
        raise AssertionError('crossref url-only title fallback should be experimentally skipped')

    def fake_query_openalex(candidate_id: str, **kwargs):
        calls['openalex'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string='URL Only Paper',
            matched=True,
            match_score=0.99,
            external_id='openalex:url-only',
            title='URL Only Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/url-only',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/url-only',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/url-only'}, ensure_ascii=False),
            latency_ms=17,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)

    enrich_candidates(settings, limit=10)

    assert calls == {'crossref': 0, 'openalex': 1}
    with sqlite3.connect(db_path) as conn:
        providers = conn.execute(
            'SELECT provider FROM candidate_enrichment_status ORDER BY provider'
        ).fetchall()
        assert providers == [('openalex',)]
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['pre_experimental_runnable_provider_intents'] == 2
        assert stats['experimental_skipped_provider_intents'] == 1
        assert stats['runnable_provider_intents'] == 1
        assert stats['pre_experimental_dispatch_group_count'] == 2
        assert stats['dispatch_group_count'] == 1
        assert stats['experimental_title_skip_subreasons_by_provider'] == {'crossref': ['url_canonical_only']}
        assert stats['experimental_skipped_group_counts_by_provider'] == {'crossref': 1}
        assert stats['experimental_skipped_group_counts_by_title_subreason'] == {'url_canonical_only': 1}
        assert stats['title_lane_request_counts_by_provider'] == {'openalex': 1}



def test_enrich_candidates_can_post_openalex_skip_crossref_url_only_after_openalex_doi_match(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'title_lane_post_openalex_skip_subreasons_by_provider': {
                'crossref': ['url_canonical_only'],
            },
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_url_only_post', 'URL Only Post-OpenAlex Paper', 'url only post openalex paper', 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only-post'),
        )
        conn.commit()

    calls = {'crossref': 0, 'openalex': 0}

    def fake_query_openalex(candidate_id: str, **kwargs):
        calls['openalex'] += 1
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string='URL Only Post-OpenAlex Paper',
            matched=True,
            match_score=0.99,
            external_id='openalex:url-only-post',
            title='URL Only Post-OpenAlex Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/url-only-post',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/url-only-post',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/url-only-post'}, ensure_ascii=False),
            latency_ms=17,
        )

    def fake_query_crossref(candidate_id: str, **kwargs):
        calls['crossref'] += 1
        raise AssertionError('crossref should be dynamically suppressed after DOI-bearing openalex title match')

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    assert calls == {'crossref': 0, 'openalex': 1}
    with sqlite3.connect(db_path) as conn:
        providers = conn.execute(
            'SELECT provider FROM candidate_enrichment_status ORDER BY provider'
        ).fetchall()
        assert providers == [('openalex',)]
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['runnable_provider_intents'] == 2
        assert stats['processed_runnable_intents'] == 2
        assert stats['dispatch_request_count'] == 1
        assert stats['title_lane_request_counts_by_provider'] == {'openalex': 1}
        assert stats['experimental_post_openalex_skip_subreasons_by_provider'] == {'crossref': ['url_canonical_only']}
        assert stats['post_openalex_suppressed_group_count'] == 1
        assert stats['post_openalex_suppressed_group_counts_by_provider'] == {'crossref': 1}
        assert stats['post_openalex_suppressed_group_counts_by_title_subreason'] == {'url_canonical_only': 1}



def test_enrich_candidates_keeps_crossref_url_only_when_openalex_does_not_recover_doi(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'title_lane_post_openalex_skip_subreasons_by_provider': {
                'crossref': ['url_canonical_only'],
            },
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_url_only_rescue', 'URL Only Rescue Paper', 'url only rescue paper', 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only-rescue'),
        )
        conn.commit()

    call_order: list[str] = []

    def fake_query_openalex(candidate_id: str, **kwargs):
        call_order.append('openalex')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string='URL Only Rescue Paper',
            matched=False,
            match_score=None,
            external_id=None,
            title=None,
            authors_json=None,
            abstract=None,
            venue=None,
            year=None,
            publication_type=None,
            doi=None,
            pmid=None,
            pmcid=None,
            url=None,
            raw_payload_json=json.dumps({'status': 'no_match'}, ensure_ascii=False),
            latency_ms=11,
        )

    def fake_query_crossref(candidate_id: str, **kwargs):
        call_order.append('crossref')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string='URL Only Rescue Paper',
            matched=True,
            match_score=0.99,
            external_id='crossref:url-only-rescue',
            title='URL Only Rescue Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/url-only-rescue',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/url-only-rescue',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/url-only-rescue'}, ensure_ascii=False),
            latency_ms=19,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    assert call_order == ['openalex', 'crossref']
    with sqlite3.connect(db_path) as conn:
        doi = conn.execute(
            "SELECT doi FROM source_record WHERE candidate_id = ? AND source_name = 'crossref' ORDER BY id DESC LIMIT 1",
            ('cand_url_only_rescue',),
        ).fetchone()[0]
        assert doi == '10.1000/url-only-rescue'
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['dispatch_request_count'] == 2
        assert stats['title_lane_request_counts_by_provider'] == {'openalex': 1, 'crossref': 1}
        assert stats['post_openalex_suppressed_group_count'] == 0
        assert stats['post_openalex_unsuppressed_targeted_group_count'] == 1
        assert stats['post_openalex_unsuppressed_targeted_group_counts_by_reason'] == {'openalex_title_unmatched': 1}
        assert stats['post_openalex_unsuppressed_targeted_group_counts_by_title_subreason'] == {'url_canonical_only': 1}


def test_enrich_candidates_records_post_openalex_unsuppressed_reason_when_match_has_no_doi(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'title_lane_post_openalex_skip_subreasons_by_provider': {
                'crossref': ['url_canonical_only'],
            },
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_url_only_no_doi', 'URL Only No DOI Paper', 'url only no doi paper', 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only-no-doi'),
        )
        conn.commit()

    call_order: list[str] = []

    def fake_query_openalex(candidate_id: str, **kwargs):
        call_order.append('openalex')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string='URL Only No DOI Paper',
            matched=True,
            match_score=0.91,
            external_id='openalex:url-only-no-doi',
            title='URL Only No DOI Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi=None,
            pmid=None,
            pmcid=None,
            url='https://openalex.org/W-no-doi',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': None}, ensure_ascii=False),
            latency_ms=13,
        )

    def fake_query_crossref(candidate_id: str, **kwargs):
        call_order.append('crossref')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='title',
            query_string='URL Only No DOI Paper',
            matched=True,
            match_score=0.99,
            external_id='crossref:url-only-no-doi',
            title='URL Only No DOI Paper',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/url-only-no-doi',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/url-only-no-doi',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/url-only-no-doi'}, ensure_ascii=False),
            latency_ms=21,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)

    enrich_candidates(settings, limit=10)

    assert call_order == ['openalex', 'crossref']
    with sqlite3.connect(db_path) as conn:
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['post_openalex_suppressed_group_count'] == 0
        assert stats['post_openalex_unsuppressed_targeted_group_count'] == 1
        assert stats['post_openalex_unsuppressed_targeted_group_counts_by_reason'] == {'openalex_title_match_without_doi': 1}
        assert stats['post_openalex_unsuppressed_targeted_group_counts_by_title_subreason'] == {'url_canonical_only': 1}


def test_enrich_candidates_can_raise_openalex_title_per_page_for_url_only(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': False},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'openalex_title_per_page_by_subreason': {
                'url_canonical_only': 5,
            },
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_url_only_topk', 'URL Only TopK Paper', 'url only topk paper', 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only-topk'),
        )
        conn.commit()

    seen: dict[str, object] = {}

    def fake_query_openalex(candidate_id: str, **kwargs):
        seen['candidate_id'] = candidate_id
        seen['title_per_page'] = kwargs.get('title_per_page')
        seen['title_pick_best_accepted'] = kwargs.get('title_pick_best_accepted')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string='URL Only TopK Paper',
            matched=False,
            match_score=None,
            external_id=None,
            title=None,
            authors_json=None,
            abstract=None,
            venue=None,
            year=None,
            publication_type=None,
            doi=None,
            pmid=None,
            pmcid=None,
            url=None,
            raw_payload_json=json.dumps({'status': 'no_match'}, ensure_ascii=False),
            latency_ms=11,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)

    enrich_candidates(settings, limit=10)

    assert seen == {
        'candidate_id': 'cand_url_only_topk',
        'title_per_page': 5,
        'title_pick_best_accepted': False,
    }
    with sqlite3.connect(db_path) as conn:
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['openalex_title_per_page_by_subreason'] == {'url_canonical_only': 5}
        assert stats['openalex_title_pick_best_accepted_subreasons'] is None


def test_enrich_candidates_can_enable_openalex_pick_best_for_url_only(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': False},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={
            'enabled_lanes': ['title_core'],
            'openalex_title_per_page_by_subreason': {
                'url_canonical_only': 5,
            },
            'openalex_title_pick_best_accepted_subreasons': ['url_canonical_only'],
        },
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_url_only_pick_best', 'URL Only Pick Best Paper', 'url only pick best paper', 'Wu', 'Nature', '2026', 'https://example.org/paper/url-only-pick-best'),
        )
        conn.commit()

    seen: dict[str, object] = {}

    def fake_query_openalex(candidate_id: str, **kwargs):
        seen['candidate_id'] = candidate_id
        seen['title_per_page'] = kwargs.get('title_per_page')
        seen['title_pick_best_accepted'] = kwargs.get('title_pick_best_accepted')
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='title',
            query_string='URL Only Pick Best Paper',
            matched=False,
            match_score=None,
            external_id=None,
            title=None,
            authors_json=None,
            abstract=None,
            venue=None,
            year=None,
            publication_type=None,
            doi=None,
            pmid=None,
            pmcid=None,
            url=None,
            raw_payload_json=json.dumps({'status': 'no_match'}, ensure_ascii=False),
            latency_ms=11,
        )

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)

    enrich_candidates(settings, limit=10)

    assert seen == {
        'candidate_id': 'cand_url_only_pick_best',
        'title_per_page': 5,
        'title_pick_best_accepted': True,
    }
    with sqlite3.connect(db_path) as conn:
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['openalex_title_per_page_by_subreason'] == {'url_canonical_only': 5}
        assert stats['openalex_title_pick_best_accepted_subreasons'] == ['url_canonical_only']
