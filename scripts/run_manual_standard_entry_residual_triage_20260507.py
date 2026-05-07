from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path('/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db')
EXPORT = Path('/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/exports/manual_standard_entries_20260507.json')

ENTRIES = [
    {
        'candidate_id': 'cand_3dcad0a71f23404f',
        'preferred_title': 'Cardiovascular Magnetic Resonance in Cardiac Amyloidosis: Part I—Technical Foundations, Techniques, and Endpoints',
        'preferred_venue': 'Magnetic Resonance Imaging Clinics of North America',
        'preferred_year': '2026',
        'preferred_doi': '10.1016/j.mric.2026.02.001',
        'preferred_publication_type': 'article',
        'merge_confidence': 0.82,
        'source_priority_trace': {
            'title': ['manual[residual_triage]:candidate_title + Crossref/PII-supported DOI assignment'],
            'authors': [],
            'abstract': [],
            'venue': ['manual[residual_triage]:Magnetic Resonance Imaging Clinics of North America'],
            'year': ['manual[residual_triage]:2026'],
            'doi': ['manual[residual_triage]:10.1016/j.mric.2026.02.001'],
            'pmid': [],
            'type': ['manual[residual_triage]:article'],
            'suppressed_signals': [],
            'fallback_mode': 'manual_residual_triage',
        },
    },
    {
        'candidate_id': 'cand_8f043460635bbb77',
        'preferred_title': 'Cardiovascular MR in Cardiac Amyloidosis: Part II—Clinical Applications in Diagnosis, Prognosis, and Treatment Response',
        'preferred_venue': 'Magnetic Resonance Imaging Clinics of North America',
        'preferred_year': '2026',
        'preferred_doi': '10.1016/j.mric.2026.02.002',
        'preferred_publication_type': 'article',
        'merge_confidence': 0.8,
        'source_priority_trace': {
            'title': ['manual[residual_triage]:candidate_title + Crossref/PII-supported DOI assignment'],
            'authors': [],
            'abstract': [],
            'venue': ['manual[residual_triage]:Magnetic Resonance Imaging Clinics of North America'],
            'year': ['manual[residual_triage]:2026'],
            'doi': ['manual[residual_triage]:10.1016/j.mric.2026.02.002'],
            'pmid': [],
            'type': ['manual[residual_triage]:article'],
            'suppressed_signals': [],
            'fallback_mode': 'manual_residual_triage',
        },
    },
    {
        'candidate_id': 'cand_0a7f41cfb0f5a3c3',
        'preferred_title': 'Geo-DMAE: Geometric Deep Multi-AutoEncoders for Monitoring Heterogeneous Normal Aging in Brain Subcortex',
        'preferred_venue': 'Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision Workshops',
        'preferred_year': '2026',
        'preferred_doi': None,
        'preferred_publication_type': 'proceedings-article',
        'merge_confidence': 0.42,
        'source_priority_trace': {
            'title': ['manual[residual_triage]:direct CVF workshop PDF title'],
            'authors': [],
            'abstract': [],
            'venue': ['manual[residual_triage]:WACV 2026 workshop venue from URL/path'],
            'year': ['manual[residual_triage]:2026'],
            'doi': [],
            'pmid': [],
            'type': ['manual[residual_triage]:proceedings-article'],
            'suppressed_signals': [],
            'fallback_mode': 'manual_residual_triage',
        },
    },
]


def main() -> None:
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    inserted = []
    with sqlite3.connect(DB) as conn:
        for entry in ENTRIES:
            cid = entry['candidate_id']
            exists = conn.execute(
                'SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?',
                (cid,),
            ).fetchone()[0]
            linked = conn.execute(
                'SELECT COUNT(*) FROM candidate_paper_link WHERE candidate_id = ?',
                (cid,),
            ).fetchone()[0]
            if linked:
                inserted.append({'candidate_id': cid, 'status': 'already_linked'})
                continue
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
                    entry['preferred_title'],
                    json.dumps([], ensure_ascii=False),
                    None,
                    entry['preferred_venue'],
                    entry['preferred_year'],
                    entry['preferred_doi'],
                    None,
                    entry['preferred_publication_type'],
                    None,
                    json.dumps(entry['source_priority_trace'], ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False),
                    entry['merge_confidence'],
                ),
            )
            inserted.append({'candidate_id': cid, 'status': 'inserted', **entry})
        conn.commit()
    EXPORT.write_text(json.dumps(inserted, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(EXPORT)
    for row in inserted:
        print(row['status'], row['candidate_id'])


if __name__ == '__main__':
    main()
