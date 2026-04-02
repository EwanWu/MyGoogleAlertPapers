from __future__ import annotations

import logging

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.enrich.crossref import query_crossref
from mygooglealertpapers.enrich.openalex import query_openalex
from mygooglealertpapers.enrich.pubmed import query_pubmed

logger = logging.getLogger(__name__)


def enrich_candidates(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    with repo.connect() as conn:
        rows = conn.execute(
            """
            SELECT pcn.candidate_id, pcn.norm_title, pcn.doi_extracted, pcn.pmid_extracted
            FROM paper_candidate_normalized pcn
            LEFT JOIN source_record sr ON sr.candidate_id = pcn.candidate_id
            WHERE sr.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        logger.info('Found %s unenriched candidate(s)', len(rows))
        for candidate_id, norm_title, doi, pmid in rows:
            records = []
            if pmid or norm_title:
                rec = query_pubmed(candidate_id, pmid=pmid, title=norm_title)
                if rec:
                    records.append(rec)
            if doi or norm_title:
                rec = query_crossref(candidate_id, doi=doi, title=norm_title)
                if rec:
                    records.append(rec)
            if doi or norm_title:
                rec = query_openalex(candidate_id, doi=doi, title=norm_title)
                if rec:
                    records.append(rec)
            for rec in records:
                repo.insert_source_record(conn, rec)
                tracker.record_stage_cost(conn, stage='enrich_candidates', status='ok' if rec.matched else 'no_match', candidate_id=candidate_id, provider=rec.source_name, latency_ms=rec.latency_ms)
        conn.commit()
