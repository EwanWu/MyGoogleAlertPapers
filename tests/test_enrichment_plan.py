from __future__ import annotations

import sqlite3
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.pipeline.enrichment_plan import build_enrichment_plan


def _make_settings(db_path: Path) -> Settings:
    profile = PolicyProfile(
        name='test_profile',
        path=None,
        provider_rules={
            'crossref': {'enabled': True},
            'openalex': {'enabled': True},
            'semanticscholar': {'enabled': True},
            'pubmed': {'enabled': True},
            'europepmc': {'enabled': True, 'trigger_mode': 'narrowed_biomedical_fallback'},
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
        openalex_email='unit@test.example',
        semantic_scholar_api_key=None,
        unpaywall_email=None,
        policy_profile=profile,
    )


def test_build_enrichment_plan_counts_dedup_opportunities_and_writes_markdown(tmp_path: Path):
    db_path = tmp_path / 'mgap.db'
    create_schema_at_default_path(db_path)
    settings = _make_settings(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family, venue_guess, year_guess, doi_extracted, pmid_extracted, arxiv_id_extracted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            [
                ('cand1', 'Shared DOI paper', 'shared doi paper', 'Wu', 'Nature', '2026', '10.1000/shared', None, None),
                ('cand2', 'Shared DOI paper', 'shared doi paper', 'Wu', 'Nature', '2026', '10.1000/shared', None, None),
                ('cand3', 'Interesting MRI study', 'interesting mri study', 'Wu', 'Brain', '2025', None, None, None),
            ],
        )
        conn.commit()

    output_path = tmp_path / 'enrichment-plan.md'
    summary = build_enrichment_plan(settings, limit=10, output_path=output_path)

    assert summary['candidate_count'] == 3
    assert summary['provider_intent_count'] == 11
    assert summary['unique_intent_count'] == 8
    assert summary['duplicate_intent_count'] == 3
    assert summary['identifier_driven_intents'] == 6
    assert summary['title_search_intents'] == 5
    assert summary['identifier_driven_unique_intents'] == 3
    assert summary['title_search_unique_intents'] == 5
    assert summary['dedup_only_request_count'] == 8
    assert summary['recommended_request_count'] == 8
    assert summary['request_savings_vs_naive'] == 3
    assert summary['request_savings_vs_dedup_only'] == 0
    assert summary['provider_breakdown'][0]['provider'] == 'crossref'

    strategy_rows = {(row['provider'], row['query_type']): row for row in summary['request_strategy_breakdown']}
    assert strategy_rows[('openalex', 'doi')]['recommended_execution_mode'] == 'batch_after_dedup'
    assert strategy_rows[('openalex', 'doi')]['recommended_request_count'] == 1
    assert strategy_rows[('openalex', 'doi')]['request_savings_vs_naive'] == 1
    assert strategy_rows[('openalex', 'doi')]['request_savings_vs_dedup_only'] == 0
    assert strategy_rows[('crossref', 'doi')]['recommended_execution_mode'] == 'dedup_only'
    assert strategy_rows[('crossref', 'doi')]['recommended_request_count'] == 1

    top_group = summary['top_duplicate_query_groups'][0]
    assert top_group['provider'] == 'crossref'
    assert top_group['query_type'] == 'doi'
    assert top_group['candidate_count'] == 2
    assert top_group['extra_intents'] == 1

    assert output_path.exists()
    markdown = output_path.read_text(encoding='utf-8')
    assert 'Provider breakdown' in markdown
    assert 'Execution recommendations' in markdown
    assert '| crossref | 3 | 2 | 1 |' in markdown
    assert '| openalex | doi | batch_after_dedup | 2 | 1 | 1 | 1 | 0 |' in markdown
