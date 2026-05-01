from __future__ import annotations

import csv
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.db.schema import create_schema_at_default_path


_SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'export_post_openalex_residual_audit.py'
_SPEC = importlib.util.spec_from_file_location('export_post_openalex_residual_audit', _SCRIPT_PATH)
assert _SPEC and _SPEC.loader
_AUDIT_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _AUDIT_MODULE
_SPEC.loader.exec_module(_AUDIT_MODULE)
export_audit = _AUDIT_MODULE.export_audit


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
            'openalex': {'enabled': True},
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


def test_export_post_openalex_residual_audit_includes_gate_and_fallback_fields(tmp_path: Path, monkeypatch):
    source_db = tmp_path / 'source.db'
    results_db = tmp_path / 'results.db'
    policy_profile = tmp_path / 'policy.yaml'
    out_csv = tmp_path / 'audit.csv'
    create_schema_at_default_path(source_db)
    create_schema_at_default_path(results_db)
    policy_profile.write_text('name: test\n')

    settings = _make_settings(
        source_db,
        runtime_rules={
            'title_lane_post_openalex_skip_subreasons_by_provider': {
                'crossref': ['url_canonical_only'],
            },
            'openalex_title_per_page_by_subreason': {
                'url_canonical_only': 5,
            },
            'openalex_title_pick_best_accepted_subreasons': ['url_canonical_only'],
            'openalex_title_extra_result_require_arxiv_id_subreasons': ['url_canonical_only'],
        },
    )
    monkeypatch.setattr(_AUDIT_MODULE, 'load_settings', lambda: settings)

    with sqlite3.connect(source_db) as conn:
        conn.execute(
            '''
            INSERT INTO paper_candidate_normalized (
                candidate_id, norm_title, norm_title_key, first_author_family,
                venue_guess, year_guess, url_canonical
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'cand_audit_1',
                'Residual Audit Paper',
                'residual audit paper',
                'Wu',
                'arXiv preprint arXiv:2601.12345',
                '2026',
                'https://example.org/paper/residual-audit',
            ),
        )
        conn.commit()

    with sqlite3.connect(results_db) as conn:
        conn.execute(
            '''
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, match_score,
                external_id, title, authors_json, abstract, venue, year, publication_type,
                doi, pmid, pmcid, url, raw_payload_json, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'cand_audit_1',
                'openalex',
                'title',
                'Residual Audit Paper',
                1,
                0.91,
                'openalex:1',
                'Residual Audit Paper',
                json.dumps(['Yue Wu'], ensure_ascii=False),
                None,
                'arXiv',
                '2026',
                'preprint',
                None,
                None,
                None,
                'https://openalex.org/W1',
                json.dumps({'status': 'ok'}, ensure_ascii=False),
                11,
            ),
        )
        conn.execute(
            '''
            INSERT INTO source_record (
                candidate_id, source_name, query_type, query_string, matched, match_score,
                external_id, title, authors_json, abstract, venue, year, publication_type,
                doi, pmid, pmcid, url, raw_payload_json, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'cand_audit_1',
                'crossref',
                'title',
                'Residual Audit Paper',
                1,
                0.99,
                'crossref:1',
                'Residual Audit Paper',
                json.dumps(['Yue Wu'], ensure_ascii=False),
                None,
                'arXiv',
                '2026',
                'preprint',
                '10.1000/residual-audit',
                None,
                None,
                'https://doi.org/10.1000/residual-audit',
                json.dumps({'status': 'ok'}, ensure_ascii=False),
                17,
            ),
        )
        conn.execute(
            '''
            INSERT INTO merged_metadata_proposal (
                candidate_id, preferred_title, preferred_authors_json, preferred_venue,
                preferred_year, preferred_doi, source_priority_trace, conflict_flags_json, merge_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'cand_audit_1',
                'Residual Audit Paper',
                json.dumps(['Yue Wu'], ensure_ascii=False),
                'arXiv',
                '2026',
                '10.1000/residual-audit',
                json.dumps({'fallback_mode': 'merged_sources'}, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                0.9,
            ),
        )
        conn.commit()

    summary = export_audit(
        source_db=source_db,
        results_db=results_db,
        policy_profile=policy_profile,
        out_csv=out_csv,
        slice_name='unit',
        reasons={'openalex_title_match_without_doi'},
    )

    assert summary['row_count'] == 1
    assert summary['non_suppression_reason_counts'] == {'openalex_title_match_without_doi': 1}
    assert summary['gate_status_counts'] == {'blocked_missing_arxiv_id': 1}

    with out_csv.open(newline='', encoding='utf-8') as f:
        row = next(csv.DictReader(f))
    assert row['candidate_id'] == 'cand_audit_1'
    assert row['arxiv_id_extracted'] == ''
    assert row['openalex_extra_result_gate_status'] == 'blocked_missing_arxiv_id'
    assert row['effective_openalex_title_per_page'] == '1'
    assert row['effective_openalex_pick_best_accepted'] == '0'
    assert row['openalex_extra_results_blocked_by_arxiv_gate'] == '1'
    assert row['crossref_only_doi_rescue'] == '1'
    assert row['fallback_mode'] == 'merged_sources'
    assert row['normalized_only_fallback'] == '0'
