from __future__ import annotations

from pathlib import Path

from mygooglealertpapers.db.repository import Repository


class CostTracker:
    def __init__(self, repository: Repository, db_path: Path):
        self.repository = repository
        self.db_path = db_path

    def record_stage_cost(
        self,
        conn,
        *,
        stage: str,
        status: str,
        mail_uid: str | None = None,
        candidate_id: str | None = None,
        notes: str | None = None,
        provider: str | None = None,
        latency_ms: int | None = None,
    ) -> None:
        self.repository.insert_cost_event(
            conn,
            stage=stage,
            status=status,
            mail_uid=mail_uid,
            candidate_id=candidate_id,
            notes=notes,
            provider=provider,
            request_count=0,
            tokens_prompt=0,
            tokens_completion=0,
            tokens_total=0,
            estimated_cost_usd=0.0,
            latency_ms=latency_ms or 0,
        )
