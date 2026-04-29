from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.pipeline.enrich import enrich_candidates
from mygooglealertpapers.pipeline.merge import build_merged_metadata


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
