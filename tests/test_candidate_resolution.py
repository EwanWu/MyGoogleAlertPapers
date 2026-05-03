from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.enrich.base import EnrichmentRecord
from mygooglealertpapers.pipeline.enrich import enrich_candidates
from mygooglealertpapers.pipeline.merge import build_merged_metadata
from mygooglealertpapers.normalize.identifiers import recover_doi_from_url_identity


def _make_settings(
    db_path: Path,
    *,
    provider_rules: dict[str, dict[str, object]] | None = None,
    merge_rules: dict[str, object] | None = None,
    runtime_rules: dict[str, object] | None = None,
) -> Settings:
    profile = PolicyProfile(
        name='test_profile',
        path=None,
        provider_rules=provider_rules or {},
        merge_rules=merge_rules or {'normalized_only_fallback': True},
        runtime_rules=runtime_rules or {'library_prelink_enabled': True},
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
        unpaywall_email=None,
        policy_profile=profile,
    )


def test_enrich_candidates_library_prelinks_exact_doi_and_skips_provider_dispatch(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO canonical_paper (
                paper_id, canonical_title, canonical_title_key, canonical_authors_json,
                canonical_year, canonical_doi, first_author_family,
                version_preference, influence_metrics_json, topic_signals_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'paper_known',
                'Known Paper',
                'known paper',
                '[]',
                '2026',
                '10.1000/known',
                'Wu',
                'unknown',
                '{}',
                '{}',
            ),
        )
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, venue_guess, doi_extracted
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_new', 'Known Paper', 'known paper', 'Wu', '2026', 'Nature', '10.1000/known'),
        )
        conn.commit()

    def unexpected_query(*args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError('library prelink should bypass provider dispatch')

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', unexpected_query)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', unexpected_query)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_semanticscholar', unexpected_query)

    enrich_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        link = conn.execute(
            'SELECT paper_id, relation_type FROM candidate_paper_link WHERE candidate_id = ?',
            ('cand_new',),
        ).fetchone()
        assert link == ('paper_known', 'library_prelinked')
        resolution = conn.execute(
            'SELECT resolution_stage, resolution_rule, paper_id, status FROM candidate_resolution_status WHERE candidate_id = ?',
            ('cand_new',),
        ).fetchone()
        assert resolution == ('library_prelink', 'doi_exact', 'paper_known', 'linked')
        assert conn.execute('SELECT COUNT(*) FROM source_record').fetchone()[0] == 0
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['library_prelinked_candidate_count'] == 1
        assert stats['library_prelink_rule_counts'] == {'doi_exact': 1}
        assert stats['dispatch_request_count'] == 0
        assert stats['prelink_skipped_provider_intents'] >= 1


def test_enrich_candidates_library_prelinks_by_arxiv_alias_from_existing_links(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO canonical_paper (
                paper_id, canonical_title, canonical_title_key, canonical_authors_json,
                canonical_year, first_author_family,
                version_preference, influence_metrics_json, topic_signals_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            ('paper_arxiv', 'Arxiv Paper', 'arxiv paper', '[]', '2026', 'Wu', 'unknown', '{}', '{}'),
        )
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, arxiv_id_extracted
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            ('cand_old', 'Arxiv Paper', 'arxiv paper', 'Wu', '2026', '2401.12345'),
        )
        conn.execute(
            '''
            INSERT INTO candidate_paper_link (candidate_id, paper_id, relation_type, confidence, evidence_json)
            VALUES (?, ?, ?, ?, ?)
            ''',
            ('cand_old', 'paper_arxiv', 'assigned', 0.95, '{}'),
        )
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, arxiv_id_extracted
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''',
            ('cand_new', 'Arxiv Paper', 'arxiv paper', 'Wu', '2026', '2401.12345'),
        )
        conn.commit()

    def unexpected_query(*args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError('arxiv alias prelink should bypass provider dispatch')

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_arxiv', unexpected_query)

    enrich_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        link = conn.execute(
            'SELECT paper_id, relation_type FROM candidate_paper_link WHERE candidate_id = ?',
            ('cand_new',),
        ).fetchone()
        assert link == ('paper_arxiv', 'library_prelinked')
        resolution = conn.execute(
            'SELECT resolution_rule FROM candidate_resolution_status WHERE candidate_id = ?',
            ('cand_new',),
        ).fetchone()
        assert resolution == ('arxiv_exact',)
        assert conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ?',
            ('cand_new',),
        ).fetchone()[0] == 0


def test_merge_skips_library_prelinked_candidates(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO canonical_paper (
                paper_id, canonical_title, canonical_title_key, canonical_authors_json,
                canonical_year, canonical_doi, first_author_family,
                version_preference, influence_metrics_json, topic_signals_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'paper_known',
                'Known Paper',
                'known paper',
                '[]',
                '2026',
                '10.1000/known',
                'Wu',
                'unknown',
                '{}',
                '{}',
            ),
        )
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, venue_guess, doi_extracted
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            ('cand_new', 'Known Paper', 'known paper', 'Wu', '2026', 'Nature', '10.1000/known'),
        )
        conn.commit()

    enrich_candidates(settings, limit=10)
    build_merged_metadata(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal').fetchone()[0] == 0


def test_same_batch_cluster_reuses_leader_identifier_intents_for_url_exact_followers(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True, 'doi_batch_enabled': False},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': False},
            'europepmc': {'enabled': False},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={'library_prelink_enabled': False, 'same_batch_clustering_enabled': True},
    )

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, venue_guess, doi_extracted, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand_leader', 'Shared Paper Canonical', 'shared paper canonical', 'Wu', '2026', 'Nature', '10.1000/shared', 'https://example.org/shared-paper'),
                ('cand_follower', 'Shared Paper Variant Title', 'shared paper variant title', 'Wu', '2026', 'Nature', None, 'https://example.org/shared-paper'),
            ],
        )
        conn.commit()

    calls = {'crossref': 0, 'openalex': 0}

    def make_record(candidate_id: str, source_name: str, query_type: str, query_string: str):
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name=source_name,
            query_type=query_type,
            query_string=query_string,
            matched=True,
            match_score=0.99,
            external_id=f'{source_name}:shared',
            title='Shared Paper Canonical',
            authors_json=json.dumps(['Yue Wu'], ensure_ascii=False),
            abstract=None,
            venue='Nature',
            year='2026',
            publication_type='journal-article',
            doi='10.1000/shared',
            pmid=None,
            pmcid=None,
            url='https://doi.org/10.1000/shared',
            raw_payload_json=json.dumps({'status': 'ok', 'doi': '10.1000/shared'}, ensure_ascii=False),
            latency_ms=25,
        )

    def fake_query_crossref(candidate_id: str, *, doi: str | None = None, title: str | None = None, **kwargs):
        calls['crossref'] += 1
        return make_record(candidate_id, 'crossref', 'doi' if doi else 'title', doi or title or '')

    def fake_query_openalex(candidate_id: str, *, doi: str | None = None, title: str | None = None, **kwargs):
        calls['openalex'] += 1
        return make_record(candidate_id, 'openalex', 'doi' if doi else 'title', doi or title or '')

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)

    enrich_candidates(settings, limit=10)

    assert calls == {'crossref': 1, 'openalex': 1}
    with sqlite3.connect(db_path) as conn:
        resolution = conn.execute(
            'SELECT resolution_stage, resolution_rule, leader_candidate_id, status FROM candidate_resolution_status WHERE candidate_id = ?',
            ('cand_follower',),
        ).fetchone()
        assert resolution == ('same_batch_cluster', 'url_canonical_exact_cluster', 'cand_leader', 'clustered')
        notes = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        stats = json.loads(notes)
        assert stats['same_batch_clustering_enabled'] is True
        assert stats['same_batch_cluster_group_count'] == 1
        assert stats['same_batch_clustered_candidate_count'] == 1
        assert stats['same_batch_cluster_rule_counts'] == {'url_canonical_exact_cluster': 1}
        assert stats['same_batch_cluster_group_savings_estimate'] > 0
        assert stats['dispatch_request_count'] == 2
        assert conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ? AND source_name = ?',
            ('cand_follower', 'crossref'),
        ).fetchone()[0] == 1
        assert conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ? AND source_name = ?',
            ('cand_follower', 'openalex'),
        ).fetchone()[0] == 1



def test_recover_doi_from_url_identity_handles_recursive_decode_and_nature_rule():
    doi, rule = recover_doi_from_url_identity(
        'https://www.e-ultrasonography.org/journal/view.php?doi%3D10.14366%252Fusg.23232'
    )
    assert doi == '10.14366/usg.23232'
    assert rule == 'recursive_url_decode'

    doi, rule = recover_doi_from_url_identity(
        'https://www.nature.com/articles/s41598-026-42032-x_reference.pdf'
    )
    assert doi == '10.1038/s41598-026-42032-x'
    assert rule == 'nature_article_slug'


def test_enrich_candidates_can_promote_deterministic_url_identity_doi_into_doi_queries(tmp_path: Path, monkeypatch):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True, 'doi_batch_enabled': False},
            'semanticscholar': {'enabled': False},
            'pubmed': {'enabled': True},
            'europepmc': {'enabled': True, 'trigger_mode': 'narrowed_biomedical_fallback'},
            'arxiv': {'enabled': False},
            'unpaywall': {'enabled': False},
        },
        runtime_rules={'library_prelink_enabled': False, 'url_identity_doi_recovery_enabled': True},
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, venue_guess, doi_extracted, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'cand_urlid',
                'Prevalence of heart failure with preserved ejection fraction in patients with ischemia and non-obstructive coronary arteries',
                'prevalence of heart failure with preserved ejection fraction in patients with ischemia and non-obstructive coronary arteries',
                'Wu',
                '2026',
                'Scientific Reports',
                None,
                'https://www.nature.com/articles/s41598-026-42032-x_reference.pdf',
            ),
        )
        conn.commit()

    calls: list[tuple[str, str | None, str | None]] = []

    def fake_query_crossref(candidate_id: str, *, doi: str | None = None, title: str | None = None, **kwargs):
        calls.append(('crossref', doi, title))
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='crossref',
            query_type='doi' if doi else 'title',
            query_string=doi or title or '',
            matched=True,
            match_score=1.0,
            external_id='crossref:test',
            title='Recovered by DOI',
            authors_json='[]',
            abstract=None,
            venue='Scientific Reports',
            year='2026',
            publication_type='journal-article',
            doi=doi,
            pmid=None,
            pmcid=None,
            url='https://doi.org/' + (doi or '10.0/test'),
            raw_payload_json='{}',
            latency_ms=5,
        )

    def fake_query_openalex(candidate_id: str, *, doi: str | None = None, title: str | None = None, **kwargs):
        calls.append(('openalex', doi, title))
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name='openalex',
            query_type='doi' if doi else 'title',
            query_string=doi or title or '',
            matched=True,
            match_score=1.0,
            external_id='openalex:test',
            title='Recovered by DOI',
            authors_json='[]',
            abstract=None,
            venue='Scientific Reports',
            year='2026',
            publication_type='journal-article',
            doi=doi,
            pmid=None,
            pmcid=None,
            url='https://doi.org/' + (doi or '10.0/test'),
            raw_payload_json='{}',
            latency_ms=5,
        )

    def unexpected_query(*args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError('biomedical title fallback should not run once DOI is recovered from URL identity')

    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_crossref', fake_query_crossref)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_openalex', fake_query_openalex)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_pubmed', unexpected_query)
    monkeypatch.setattr('mygooglealertpapers.pipeline.enrich.query_europepmc', unexpected_query)

    enrich_candidates(settings, limit=10)

    assert ('crossref', '10.1038/s41598-026-42032-x', 'Prevalence of heart failure with preserved ejection fraction in patients with ischemia and non-obstructive coronary arteries') in calls
    assert ('openalex', '10.1038/s41598-026-42032-x', 'Prevalence of heart failure with preserved ejection fraction in patients with ischemia and non-obstructive coronary arteries') in calls
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ? AND source_name = ? AND query_type = ?',
            ('cand_urlid', 'crossref', 'doi'),
        ).fetchone()[0] == 1
        assert conn.execute(
            'SELECT COUNT(*) FROM source_record WHERE candidate_id = ? AND source_name = ? AND query_type = ?',
            ('cand_urlid', 'openalex', 'doi'),
        ).fetchone()[0] == 1
