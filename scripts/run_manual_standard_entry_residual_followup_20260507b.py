from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB = Path('/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db')
EXPORT = Path('/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/data/exports/manual_standard_entries_residual_followup_20260507b.json')

ENTRIES = [
    {
        'candidate_id': 'cand_7622d596c094c1c4',
        'preferred_title': 'Prognostic value of cardiac-dedicated cadmium-zinc-telluride– single-photon emission computed tomography dynamic imaging derived myocardial blood flow quantification parameters in post–percutaneous coronary intervention acute myocardial infarction patients: A pilot study',
        'preferred_venue': 'Journal of Nuclear Cardiology',
        'preferred_year': '2026',
        'preferred_doi': '10.1016/j.nuclcard.2026.102681',
        'preferred_publication_type': 'article',
        'merge_confidence': 0.9,
        'source_priority_trace': {
            'title': ['manual[residual_followup]:ScienceDirect citation_title'],
            'authors': [],
            'abstract': [],
            'venue': ['manual[residual_followup]:ScienceDirect citation_journal_title'],
            'year': ['manual[residual_followup]:ScienceDirect citation_publication_date -> 2026'],
            'doi': ['manual[residual_followup]:10.1016/j.nuclcard.2026.102681'],
            'pmid': [],
            'type': ['manual[residual_followup]:article'],
            'suppressed_signals': [],
            'fallback_mode': 'manual_residual_followup',
        },
    },
    {
        'candidate_id': 'cand_5eba69b4ad9d4103',
        'preferred_title': 'Can we predict sleep health based on brain features? A large-scale machine learning study using UK Biobank',
        'preferred_venue': 'Brain Communications',
        'preferred_year': '2026',
        'preferred_doi': '10.1093/braincomms/fcag016',
        'preferred_publication_type': 'article',
        'merge_confidence': 0.88,
        'source_priority_trace': {
            'title': ['manual[residual_followup]:JuSER citation_title'],
            'authors': [],
            'abstract': [],
            'venue': ['manual[residual_followup]:JuSER citation_journal_title'],
            'year': ['manual[residual_followup]:JuSER citation_date -> 2026'],
            'doi': ['manual[residual_followup]:10.1093/braincomms/fcag016'],
            'pmid': [],
            'type': ['manual[residual_followup]:article'],
            'suppressed_signals': [],
            'fallback_mode': 'manual_residual_followup',
        },
    },
]


def main() -> None:
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    inserted = []
    with sqlite3.connect(DB) as conn:
        for entry in ENTRIES:
            cid = entry['candidate_id']
            linked = conn.execute(
                'SELECT COUNT(*) FROM candidate_paper_link WHERE candidate_id = ?',
                (cid,),
            ).fetchone()[0]
            if linked:
                inserted.append({'candidate_id': cid, 'status': 'already_linked', **entry})
                continue
            exists = conn.execute(
                'SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?',
                (cid,),
            ).fetchone()[0]
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
