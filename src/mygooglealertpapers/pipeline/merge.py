from __future__ import annotations

import json
import logging
import sqlite3
from collections import Counter, defaultdict

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository

logger = logging.getLogger(__name__)

SOURCE_PRIORITY = {
    'pubmed': 3,
    'crossref': 2,
    'openalex': 1,
}


def _pick_preferred(rows, field: str):
    candidates = []
    for r in rows:
        value = r[field]
        if value:
            candidates.append((SOURCE_PRIORITY.get(r['source_name'], 0), value, r['source_name']))
    if not candidates:
        return None, []
    candidates.sort(key=lambda x: (-x[0], x[2]))
    return candidates[0][1], [f"{src}:{val}" for _, val, src in candidates]


def _conflicts(rows, field: str) -> list[str]:
    values = {r[field] for r in rows if r[field]}
    return sorted(values) if len(values) > 1 else []


def build_merged_metadata(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    with repo.connect() as conn:
        rows = conn.execute(
            """
            SELECT pcn.candidate_id
            FROM paper_candidate_normalized pcn
            LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id
            WHERE mmp.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        candidate_ids = [r[0] for r in rows]
        logger.info('Found %s candidate(s) without merged proposal', len(candidate_ids))
        for candidate_id in candidate_ids:
            src_rows = conn.execute(
                """
                SELECT source_name, title, authors_json, abstract, venue, year,
                       publication_type, doi, pmid, pmcid, url, matched
                FROM source_record
                WHERE candidate_id = ? AND matched = 1
                """,
                (candidate_id,),
            ).fetchall()
            if not src_rows:
                tracker.record_stage_cost(conn, stage='merge_metadata', status='no_sources', candidate_id=candidate_id)
                continue
            dict_rows = [
                {
                    'source_name': r[0], 'title': r[1], 'authors_json': r[2], 'abstract': r[3],
                    'venue': r[4], 'year': r[5], 'publication_type': r[6], 'doi': r[7],
                    'pmid': r[8], 'pmcid': r[9], 'url': r[10], 'matched': r[11]
                }
                for r in src_rows
            ]
            preferred_title, title_trace = _pick_preferred(dict_rows, 'title')
            preferred_authors_json, authors_trace = _pick_preferred(dict_rows, 'authors_json')
            preferred_abstract, abstract_trace = _pick_preferred(dict_rows, 'abstract')
            preferred_venue, venue_trace = _pick_preferred(dict_rows, 'venue')
            preferred_year, year_trace = _pick_preferred(dict_rows, 'year')
            preferred_doi, doi_trace = _pick_preferred(dict_rows, 'doi')
            preferred_pmid, pmid_trace = _pick_preferred(dict_rows, 'pmid')
            preferred_publication_type, type_trace = _pick_preferred(dict_rows, 'publication_type')

            conflict_flags = {}
            for field in ['title', 'venue', 'year', 'doi', 'pmid']:
                vals = _conflicts(dict_rows, field)
                if vals:
                    conflict_flags[field] = vals

            conn.execute(
                """
                INSERT INTO merged_metadata_proposal (
                    candidate_id, preferred_title, preferred_authors_json,
                    preferred_abstract, preferred_venue, preferred_year,
                    preferred_doi, preferred_pmid, preferred_publication_type,
                    version_status, source_priority_trace, conflict_flags_json,
                    merge_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    preferred_title,
                    preferred_authors_json,
                    preferred_abstract,
                    preferred_venue,
                    preferred_year,
                    preferred_doi,
                    preferred_pmid,
                    preferred_publication_type,
                    'unknown',
                    json.dumps({
                        'title': title_trace,
                        'authors': authors_trace,
                        'abstract': abstract_trace,
                        'venue': venue_trace,
                        'year': year_trace,
                        'doi': doi_trace,
                        'pmid': pmid_trace,
                        'type': type_trace,
                    }, ensure_ascii=False),
                    json.dumps(conflict_flags, ensure_ascii=False),
                    0.9 if not conflict_flags else 0.6,
                ),
            )
            tracker.record_stage_cost(conn, stage='merge_metadata', status='ok', candidate_id=candidate_id)
        conn.commit()
