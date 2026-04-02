from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EnrichmentRecord:
    candidate_id: str
    source_name: str
    query_type: str
    query_string: str
    matched: bool
    match_score: float | None
    external_id: str | None
    title: str | None
    authors_json: str | None
    abstract: str | None
    venue: str | None
    year: str | None
    publication_type: str | None
    doi: str | None
    pmid: str | None
    pmcid: str | None
    url: str | None
    raw_payload_json: str
    latency_ms: int
