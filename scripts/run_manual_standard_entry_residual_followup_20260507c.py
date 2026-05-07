from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path('/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db')
EXPORT = Path('/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/exports/manual_standard_entries_residual_followup_20260507c.json')

ENTRY = {
    'candidate_id': 'cand_ef3cc43d12bc802a',
    'preferred_title': 'Imaging the glymphatic system: Between promise and proof in modern radiology',
    'preferred_venue': 'Journal of Applied & Clinical Radiology',
    'preferred_year': '2026',
    'preferred_doi': '10.4103/JAACR.JAACR_26_25',
    'preferred_publication_type': 'article',
    'merge_confidence': 0.78,
    'source_priority_trace': {
        'title': ['manual[residual_followup]:candidate/raw title; LWW page title confirms article'],
        'authors': [],
        'abstract': [],
        'venue': ['manual[residual_followup]:LWW title / Journal of Applied & Clinical Radiology'],
        'year': ['manual[residual_followup]:candidate year 2026'],
        'doi': ['manual[residual_followup]:LWW citation_doi / wkhealth_doi = 10.4103/JAACR.JAACR_26_25'],
        'pmid': [],
        'type': ['manual[residual_followup]:article'],
        'suppressed_signals': [],
        'fallback_mode': 'manual_residual_followup',
    },
}


def main() -> None:
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as conn:
        cid = ENTRY['candidate_id']
        linked = conn.execute('SELECT COUNT(*) FROM candidate_paper_link WHERE candidate_id = ?', (cid,)).fetchone()[0]
        if linked:
            rows = [{'candidate_id': cid, 'status': 'already_linked', **ENTRY}]
        else:
            exists = conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?', (cid,)).fetchone()[0]
            if exists:
                conn.execute('DELETE FROM merged_metadata_proposal WHERE candidate_id = ?', (cid,))
            conn.execute(
                '''
                INSERT INTO merged_metadata_proposal (
                    candidate_id, preferred_title, preferred_authors_json, preferred_abstract,
                    preferred_venue, preferred_year, preferred_doi, preferred_pmid,
                    preferred_publication_type, version_status, source_priority_trace,
                    conflict_flags_json, merge_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    cid,
                    ENTRY['preferred_title'],
                    json.dumps([], ensure_ascii=False),
                    None,
                    ENTRY['preferred_venue'],
                    ENTRY['preferred_year'],
                    ENTRY['preferred_doi'],
                    None,
                    ENTRY['preferred_publication_type'],
                    None,
                    json.dumps(ENTRY['source_priority_trace'], ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False),
                    ENTRY['merge_confidence'],
                ),
            )
            conn.commit()
            rows = [{'candidate_id': cid, 'status': 'inserted', **ENTRY}]
    EXPORT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(EXPORT)
    print(rows[0]['status'], rows[0]['candidate_id'])


if __name__ == '__main__':
    main()
