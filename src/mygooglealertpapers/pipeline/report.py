from __future__ import annotations

import sqlite3
from pathlib import Path


def build_batch_report(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        total_mail = conn.execute("SELECT COUNT(*) FROM mail_ingestion_record").fetchone()[0]
        scholar_mail = conn.execute("SELECT COUNT(*) FROM mail_ingestion_record WHERE is_google_scholar_alert = 1").fetchone()[0]
        total_candidates = conn.execute("SELECT COUNT(*) FROM paper_candidate").fetchone()[0]
        cost_events = conn.execute("SELECT COUNT(*) FROM cost_event").fetchone()[0]
        lines = [
            "Batch report",
            f"- total scanned mails: {total_mail}",
            f"- detected Scholar mails: {scholar_mail}",
            f"- extracted candidates: {total_candidates}",
            f"- cost events logged: {cost_events}",
        ]
        return "\n".join(lines)
