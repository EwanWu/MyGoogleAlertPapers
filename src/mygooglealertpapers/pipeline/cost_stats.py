from __future__ import annotations

import sqlite3
from pathlib import Path


def build_cost_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        lines = [
            'Cost stats',
            '- batch run summary:',
        ]
        for stage, cnt, total_ms, avg_ms in conn.execute(
            "SELECT stage, COUNT(*), COALESCE(SUM(duration_ms),0), COALESCE(AVG(duration_ms),0) FROM batch_run GROUP BY stage ORDER BY stage"
        ):
            lines.append(f'  - {stage}: runs={cnt}, total_duration_ms={int(total_ms)}, avg_duration_ms={avg_ms:.1f}')
        lines.append('- stage event summary:')
        for stage, cnt, total_ms, avg_ms in conn.execute(
            "SELECT stage, COUNT(*), COALESCE(SUM(latency_ms),0), COALESCE(AVG(latency_ms),0) FROM cost_event GROUP BY stage ORDER BY stage"
        ):
            lines.append(f'  - {stage}: events={cnt}, total_latency_ms={int(total_ms)}, avg_latency_ms={avg_ms:.1f}')
        lines.append('- provider summary:')
        for provider, cnt, total_ms, avg_ms in conn.execute(
            "SELECT COALESCE(provider, 'none'), COUNT(*), COALESCE(SUM(latency_ms),0), COALESCE(AVG(latency_ms),0) FROM cost_event GROUP BY COALESCE(provider, 'none') ORDER BY COALESCE(provider, 'none')"
        ):
            lines.append(f'  - {provider}: events={cnt}, total_latency_ms={int(total_ms)}, avg_latency_ms={avg_ms:.1f}')
        return '\n'.join(lines)
