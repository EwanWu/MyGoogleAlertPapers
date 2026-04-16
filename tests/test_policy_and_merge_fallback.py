from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.pipeline.enrich import _build_provider_intents
from mygooglealertpapers.pipeline.merge import build_merged_metadata
from mygooglealertpapers.pipeline.dedup import deduplicate_candidates


def _make_settings(db_path: Path, *, provider_rules: dict[str, dict[str, object]] | None = None, merge_rules: dict[str, object] | None = None) -> Settings:
    profile = PolicyProfile(
        name='test_profile',
        path=None,
        provider_rules=provider_rules or {},
        merge_rules=merge_rules or {},
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
        policy_profile=profile,
    )


def test_build_provider_intents_respects_profile_flags():
    settings = _make_settings(
        Path('/tmp/unused.db'),
        provider_rules={
            'semanticscholar': {'enabled': False},
            'europepmc': {'enabled': True, 'trigger_mode': 'broad_biomedical'},
            'arxiv': {'enabled': False},
        },
    )
    row = ('cand1', 'Brain MRI biomarkers', '10.1000/test', None, None, 'Wu', 'Neurology', '2026')
    intents = _build_provider_intents(settings, row)
    providers = {(intent.provider, intent.query_type) for intent in intents}
    assert ('crossref', 'doi') in providers
    assert ('openalex', 'doi') in providers
    assert ('semanticscholar', 'doi') not in providers
    assert ('europepmc', 'doi') in providers
    assert all(provider != 'arxiv' for provider, _ in providers)


def test_merge_builds_normalized_only_fallback_when_enabled(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path, merge_rules={'normalized_only_fallback': True})

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, norm_authors_json,
                first_author_family, year_guess, venue_guess, doi_extracted,
                pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'cand_fallback',
                'Fallback Title',
                'fallback title',
                '["A. Author"]',
                'Author',
                '2026',
                'Journal X',
                '10.1000/fallback',
                None,
                None,
                None,
                'https://example.org/paper',
                None,
            ),
        )
        conn.execute(
            """
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, doi
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ('cand_fallback', 'crossref', 'doi', '10.1000/fallback', 0, '10.1000/fallback'),
        )
        conn.commit()

    build_merged_metadata(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT preferred_title, preferred_doi, source_priority_trace, conflict_flags_json, merge_confidence FROM merged_metadata_proposal WHERE candidate_id = ?",
            ('cand_fallback',),
        ).fetchone()
        assert row is not None
        preferred_title, preferred_doi, source_priority_trace, conflict_flags_json, merge_confidence = row
        assert preferred_title == 'Fallback Title'
        assert preferred_doi == '10.1000/fallback'
        assert 'normalized_only' in source_priority_trace
        assert 'normalized_only' in conflict_flags_json
        assert merge_confidence == 0.15


def test_merge_skips_normalized_only_fallback_when_disabled(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path, merge_rules={'normalized_only_fallback': False})

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, norm_authors_json,
                first_author_family, year_guess, venue_guess, doi_extracted,
                pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'cand_skip',
                'Skip Title',
                'skip title',
                '["A. Author"]',
                'Author',
                '2026',
                'Journal X',
                '10.1000/skip',
                None,
                None,
                None,
                'https://example.org/paper',
                None,
            ),
        )
        conn.commit()

    build_merged_metadata(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?", ('cand_skip',)).fetchone()[0]
        assert count == 0


def test_merge_rejects_author_blob_fallback_when_guardrail_enabled(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        merge_rules={
            'normalized_only_fallback': True,
            'fallback_reject_author_blob': True,
        },
    )

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, norm_authors_json,
                first_author_family, year_guess, venue_guess, doi_extracted,
                pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'cand_author_blob',
                'Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3',
                'huan yang 1 yunchao chen 1 teng ma 1 jizhen feng 1 chencui huang 3',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        conn.execute(
            """
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, title
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ('cand_author_blob', 'crossref', 'title', 'huan yang', 0, 'Chen Huan'),
        )
        conn.commit()

    build_merged_metadata(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?", ('cand_author_blob',)).fetchone()[0]
        assert count == 0


def test_merge_routes_low_similarity_fallback_to_review(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        merge_rules={
            'normalized_only_fallback': True,
            'fallback_review_similarity_threshold': 0.45,
        },
    )

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, norm_authors_json,
                first_author_family, year_guess, venue_guess, doi_extracted,
                pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'cand_review',
                'Domain-Guided Machine Learning for High-Dimensional Multi-Modal Neuroimaging and Biomarker Integration in Alzheimer\'s Disease',
                'domain guided machine learning',
                '["C Sorensen"]',
                'Sorensen',
                '2026',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        conn.execute(
            """
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, title, doi
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ('cand_review', 'crossref', 'title', 'domain guided machine learning', 0, 'A Survey on Explainable Artificial Intelligence', '10.1000/xai'),
        )
        conn.commit()

    build_merged_metadata(settings, limit=10)
    deduplicate_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT conflict_flags_json FROM merged_metadata_proposal WHERE candidate_id = ?",
            ('cand_review',),
        ).fetchone()
        assert row is not None
        payload = row[0]
        assert 'fallback_guardrail' in payload
        assert 'low_source_title_similarity' in payload
        review_count = conn.execute("SELECT COUNT(*) FROM merge_review_queue WHERE candidate_id = ?", ('cand_review',)).fetchone()[0]
        assert review_count == 1
        link_count = conn.execute("SELECT COUNT(*) FROM candidate_paper_link WHERE candidate_id = ?", ('cand_review',)).fetchone()[0]
        assert link_count == 0


def test_merge_routes_sparse_low_similarity_fallback_to_review(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        merge_rules={
            'normalized_only_fallback': True,
            'fallback_review_sparse_metadata_similarity_threshold': 0.5,
        },
    )

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, norm_authors_json,
                first_author_family, year_guess, venue_guess, doi_extracted,
                pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'cand_sparse_review',
                'Measuring blood flow and pulsatility with MRI: optimisation, validation and application in cerebral small vessel',
                'measuring blood flow and pulsatility',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        conn.execute(
            """
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, title, doi
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ('cand_sparse_review', 'crossref', 'title', 'measuring blood flow', 0, 'A Review of Indocyanine Green Fluorescent Imaging in Surgery', '10.1155/2012/940585'),
        )
        conn.commit()

    build_merged_metadata(settings, limit=10)
    deduplicate_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        review_count = conn.execute("SELECT COUNT(*) FROM merge_review_queue WHERE candidate_id = ?", ('cand_sparse_review',)).fetchone()[0]
        assert review_count == 1
        payload = conn.execute("SELECT conflict_flags_json FROM merged_metadata_proposal WHERE candidate_id = ?", ('cand_sparse_review',)).fetchone()[0]
        assert 'sparse_metadata_low_source_title_similarity' in payload


def test_merge_salvages_author_tail_pollution_when_cleaned_title_matches_source(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(
        db_path,
        merge_rules={
            'normalized_only_fallback': True,
            'fallback_review_author_pollution': True,
            'fallback_author_pollution_salvage_similarity_threshold': 0.8,
        },
    )

    import sqlite3

    polluted_title = 'PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease Hugh S Markus, FMed Sci, Marco Egle MSc'
    cleaned_title = 'PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease'

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, norm_authors_json,
                first_author_family, year_guess, venue_guess, doi_extracted,
                pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                url_canonical, scholar_cluster_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'cand_author_salvage',
                polluted_title,
                'preserve randomized trial',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        conn.execute(
            """
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, title, doi, year, venue
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('cand_author_salvage', 'crossref', 'title', 'preserve randomized trial', 0, cleaned_title, '10.1161/strokeaha.120.032054', '2021', 'Stroke'),
        )
        conn.commit()

    build_merged_metadata(settings, limit=10)
    deduplicate_candidates(settings, limit=10)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT preferred_title, conflict_flags_json FROM merged_metadata_proposal WHERE candidate_id = ?",
            ('cand_author_salvage',),
        ).fetchone()
        assert row is not None
        assert row[0] == cleaned_title
        assert 'title_author_tail_pollution_salvaged' in row[1]
        review_count = conn.execute("SELECT COUNT(*) FROM merge_review_queue WHERE candidate_id = ?", ('cand_author_salvage',)).fetchone()[0]
        assert review_count == 0
