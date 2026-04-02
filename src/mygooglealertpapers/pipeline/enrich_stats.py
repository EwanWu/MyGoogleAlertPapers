from __future__ import annotations

import sqlite3
from pathlib import Path


def build_enrichment_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
        source_total = conn.execute('SELECT COUNT(*) FROM source_record').fetchone()[0]
        matched_total = conn.execute('SELECT COUNT(*) FROM source_record WHERE matched = 1').fetchone()[0]
        lines = [
            'Enrichment stats',
            f'- normalized candidates: {total}',
            f'- source records: {source_total}',
            f'- matched source records: {matched_total}',
            '- provider breakdown:',
        ]
        for provider, count, matched in conn.execute('SELECT source_name, COUNT(*), SUM(CASE WHEN matched = 1 THEN 1 ELSE 0 END) FROM source_record GROUP BY source_name ORDER BY source_name'):
            lines.append(f'  - {provider}: {matched}/{count} matched')
        return '\n'.join(lines)
