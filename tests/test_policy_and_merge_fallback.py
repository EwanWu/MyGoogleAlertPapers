from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.pipeline.enrich import _build_provider_intents
from mygooglealertpapers.pipeline.merge import build_merged_metadata


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
