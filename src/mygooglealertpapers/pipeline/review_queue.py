from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def _ensure_review_queue_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS merge_review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL UNIQUE,
            reason TEXT,
            assessment_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def build_review_queue_report(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        _ensure_review_queue_table(conn)
        total = conn.execute('SELECT COUNT(*) FROM merge_review_queue').fetchone()[0]
        lines = [
            'Review queue',
            f'- blocked candidates: {total}',
        ]
        for reason, count in conn.execute(
            'SELECT COALESCE(reason, "unknown"), COUNT(*) FROM merge_review_queue GROUP BY COALESCE(reason, "unknown") ORDER BY COUNT(*) DESC'
        ):
            lines.append(f'  - {reason}: {count}')
        return '\n'.join(lines)


def export_review_queue(db_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        _ensure_review_queue_table(conn)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT mrq.candidate_id, mrq.reason, mrq.assessment_json, mrq.created_at, mrq.updated_at,
                   pcn.norm_title, pcn.first_author_family, pcn.year_guess, pcn.doi_extracted, pcn.pmid_extracted,
                   mmp.preferred_title, mmp.preferred_venue, mmp.preferred_year, mmp.preferred_doi, mmp.preferred_pmid,
                   mmp.merge_confidence, mmp.conflict_flags_json,
                   pc.raw_title, pc.raw_link, pc.target_url, pc.venue_guess AS raw_venue_guess
            FROM merge_review_queue mrq
            LEFT JOIN paper_candidate_normalized pcn ON pcn.candidate_id = mrq.candidate_id
            LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = mrq.candidate_id
            LEFT JOIN paper_candidate pc ON pc.candidate_id = mrq.candidate_id
            ORDER BY mrq.updated_at DESC, mrq.id DESC
            """
        ).fetchall()

        source_rows = conn.execute(
            """
            SELECT candidate_id, source_name, query_type, matched, title, venue, year, doi, pmid, pmcid, url
            FROM source_record
            WHERE candidate_id IN (SELECT candidate_id FROM merge_review_queue)
            ORDER BY candidate_id, source_name, query_type, id
            """
        ).fetchall()

    source_map: dict[str, list[dict[str, object]]] = {}
    for row in source_rows:
        item = dict(row)
        source_map.setdefault(item['candidate_id'], []).append(
            {
                'source_name': item['source_name'],
                'query_type': item['query_type'],
                'matched': bool(item['matched']),
                'title': item['title'],
                'venue': item['venue'],
                'year': item['year'],
                'doi': item['doi'],
                'pmid': item['pmid'],
                'pmcid': item['pmcid'],
                'url': item['url'],
            }
        )

    with output_path.open('w', encoding='utf-8') as f:
        for row in rows:
            item = dict(row)
            for key in ('assessment_json', 'conflict_flags_json'):
                payload = item.get(key)
                if payload:
                    try:
                        item[key] = json.loads(payload)
                    except Exception:
                        pass
            item['review_summary'] = {
                'candidate_id': item['candidate_id'],
                'reason': item['reason'],
                'norm_title': item.get('norm_title'),
                'preferred_title': item.get('preferred_title'),
                'preferred_venue': item.get('preferred_venue'),
                'preferred_year': item.get('preferred_year'),
                'preferred_doi': item.get('preferred_doi'),
                'preferred_pmid': item.get('preferred_pmid'),
                'merge_confidence': item.get('merge_confidence'),
            }
            item['source_records'] = source_map.get(item['candidate_id'], [])
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    return output_path
