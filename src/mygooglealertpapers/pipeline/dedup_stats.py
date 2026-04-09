from __future__ import annotations

import sqlite3
from pathlib import Path


def build_dedup_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        candidates = conn.execute('SELECT COUNT(*) FROM paper_candidate').fetchone()[0]
        canonical = conn.execute('SELECT COUNT(*) FROM canonical_paper').fetchone()[0]
        linked = conn.execute('SELECT COUNT(*) FROM candidate_paper_link').fetchone()[0]
        table_exists = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='merge_review_queue'").fetchone()[0] > 0
        review_blocked = conn.execute('SELECT COUNT(*) FROM merge_review_queue').fetchone()[0] if table_exists else 0
        lines = [
            'Dedup stats',
            f'- paper candidates: {candidates}',
            f'- canonical papers: {canonical}',
            f'- candidate-paper links: {linked}',
            f'- blocked-for-review candidates: {review_blocked}',
        ]
        if candidates:
            lines.append(f'- compression ratio (canonical/candidate): {canonical}/{candidates} = {canonical / candidates:.3f}')
        for rule, count in conn.execute("SELECT json_extract(evidence_json, '$.rule'), COUNT(*) FROM candidate_paper_link GROUP BY json_extract(evidence_json, '$.rule') ORDER BY COUNT(*) DESC"):
            lines.append(f'  - {rule}: {count}')
        return '\n'.join(lines)
