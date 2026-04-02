from __future__ import annotations

import sqlite3
from pathlib import Path


def build_merge_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal').fetchone()[0]
        low_conf = conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal WHERE merge_confidence < 0.8').fetchone()[0]
        conflict_count = conn.execute("SELECT COUNT(*) FROM merged_metadata_proposal WHERE conflict_flags_json IS NOT NULL AND conflict_flags_json != '{}' ").fetchone()[0]
        lines = [
            'Merge stats',
            f'- merged proposals: {total}',
            f'- proposals with conflicts: {conflict_count}',
            f'- low-confidence proposals: {low_conf}',
        ]
        return '\n'.join(lines)
