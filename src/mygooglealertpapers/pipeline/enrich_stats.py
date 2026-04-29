from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def build_enrichment_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
        source_total = conn.execute('SELECT COUNT(*) FROM source_record').fetchone()[0]
        matched_total = conn.execute('SELECT COUNT(*) FROM source_record WHERE matched = 1').fetchone()[0]
        dispatch_stats = None
        notes_row = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if notes_row and notes_row[0]:
            try:
                dispatch_stats = json.loads(notes_row[0])
            except Exception:
                dispatch_stats = None
        lines = [
            'Enrichment stats',
            f'- normalized candidates: {total}',
            f'- source records: {source_total}',
            f'- matched source records: {matched_total}',
        ]
        if dispatch_stats:
            lines.extend([
                '- dispatch summary:',
                f"  - runnable provider intents: {dispatch_stats.get('runnable_provider_intents')}",
                f"  - dispatch groups: {dispatch_stats.get('dispatch_group_count')}",
                f"  - dispatch requests: {dispatch_stats.get('dispatch_request_count')}",
                f"  - processed runnable intents: {dispatch_stats.get('processed_runnable_intents', dispatch_stats.get('runnable_provider_intents'))}/{dispatch_stats.get('runnable_provider_intents')}",
                f"  - request savings vs processed intents: {dispatch_stats.get('request_savings_vs_processed_intents', 'n/a')}",
                f"  - request savings vs total planned intents: {dispatch_stats.get('request_savings_vs_total_planned_intents', dispatch_stats.get('request_savings_vs_runnable_intents'))}",
                f"  - cache-hit groups: {dispatch_stats.get('cache_hit_group_count')}",
                f"  - fanout candidates: {dispatch_stats.get('fanout_candidate_count')}",
                f"  - shared title reuse groups: {dispatch_stats.get('shared_title_reuse_group_count')}",
                f"  - shared title reuse intents: {dispatch_stats.get('shared_title_reuse_intent_count')}",
                f"  - shared title reuse requests: {dispatch_stats.get('shared_title_reuse_request_count')}",
                f"  - shared title reuse request savings: {dispatch_stats.get('shared_title_reuse_request_savings')}",
            ])
        lines.append('- provider breakdown:')
        for provider, count, matched in conn.execute('SELECT source_name, COUNT(*), SUM(CASE WHEN matched = 1 THEN 1 ELSE 0 END) FROM source_record GROUP BY source_name ORDER BY source_name'):
            lines.append(f'  - {provider}: {matched}/{count} matched')
        return '\n'.join(lines)
