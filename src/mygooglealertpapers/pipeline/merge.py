from __future__ import annotations

import json
import logging
import time
import uuid
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


def _normalize_conflict_value(field: str, value: str | None) -> str | None:
    if not value:
        return None
    normalized = str(value).strip()
    if field in {'title', 'venue'}:
        normalized = normalized.casefold()
        normalized = normalized.replace('–', '-').replace('—', '-')
        normalized = normalized.replace('&amp;', '&')
        normalized = normalized.rstrip(' .')
    if field in {'doi'}:
        normalized = normalized.casefold().rstrip(' ./')
    return normalized or None


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
    normalized_map = {}
    for r in rows:
        raw = r[field]
        if not raw:
            continue
        key = _normalize_conflict_value(field, raw)
        normalized_map.setdefault(key, set()).add(raw)
    if len(normalized_map) <= 1:
        return []
    out = []
    for vals in normalized_map.values():
        out.extend(sorted(vals))
    return sorted(set(out))


def build_merged_metadata(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'merge_metadata_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='merge_metadata', requested_limit=limit, notes=None)
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

            fallback_row = conn.execute(
                '''
                SELECT norm_title, norm_authors_json, venue_guess, year_guess, doi_extracted, pmid_extracted
                FROM paper_candidate_normalized
                WHERE candidate_id = ?
                ''',
                (candidate_id,),
            ).fetchone()
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

            if fallback_row:
                norm_title, norm_authors_json, norm_venue_guess, norm_year_guess, norm_doi, norm_pmid = fallback_row
            else:
                norm_title = norm_authors_json = norm_venue_guess = norm_year_guess = norm_doi = norm_pmid = None

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
                    preferred_title or norm_title,
                    preferred_authors_json or norm_authors_json,
                    preferred_abstract,
                    preferred_venue or norm_venue_guess,
                    preferred_year or norm_year_guess,
                    preferred_doi or norm_doi,
                    preferred_pmid or norm_pmid,
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
        repo.finish_batch_run(conn, run_id=run_id, duration_ms=int((time.perf_counter()-started_at)*1000), processed_count=len(candidate_ids), status='ok')
        conn.commit()
