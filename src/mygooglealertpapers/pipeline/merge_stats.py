from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def build_merge_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute('SELECT conflict_flags_json, merge_confidence FROM merged_metadata_proposal').fetchall()
        total = len(rows)
        low_conf = sum(1 for _, conf in rows if (conf or 0) < 0.8)
        conflict_count = 0
        blocked = 0
        grade_counts = {'A': 0, 'B': 0, 'C': 0}
        for payload, _ in rows:
            if not payload or payload == '{}':
                continue
            conflict_count += 1
            try:
                data = json.loads(payload)
            except Exception:
                continue
            if isinstance(data, dict):
                grade = data.get('conflict_grade_max')
                if grade in grade_counts:
                    grade_counts[grade] += 1
                if data.get('canonical_blocked'):
                    blocked += 1
        lines = [
            'Merge stats',
            f'- merged proposals: {total}',
            f'- proposals with conflicts: {conflict_count}',
            f'- low-confidence proposals: {low_conf}',
            f'- canonical-blocked proposals: {blocked}',
        ]
        for grade in ['A', 'B', 'C']:
            lines.append(f'  - grade_{grade}: {grade_counts[grade]}')
        return '\n'.join(lines)
