from __future__ import annotations

import logging
import time
import uuid

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.enrich.crossref import query_crossref
from mygooglealertpapers.enrich.openalex import query_openalex
from mygooglealertpapers.enrich.pubmed import query_pubmed
from mygooglealertpapers.enrich.base import enrichment_record_from_json, enrichment_record_to_json

logger = logging.getLogger(__name__)


def enrich_candidates(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'enrich_candidates_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='enrich_candidates', requested_limit=limit, notes=None)
        rows = conn.execute(
            """
            SELECT pcn.candidate_id, pcn.norm_title, pcn.doi_extracted, pcn.pmid_extracted, pcn.first_author_family, pcn.venue_guess, pcn.year_guess
            FROM paper_candidate_normalized pcn
            LEFT JOIN source_record sr ON sr.candidate_id = pcn.candidate_id
            WHERE sr.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        logger.info('Found %s unenriched candidate(s)', len(rows))
        for candidate_id, norm_title, doi, pmid, first_author_family, venue_guess, year_guess in rows:
            records = []
            if pmid or norm_title:
                query_type = 'pmid' if pmid else 'title'
                query_key = pmid or norm_title or ''
                cached = repo.get_query_cache(conn, provider='pubmed', query_type=query_type, query_key=query_key)
                if cached:
                    rec = enrichment_record_from_json(cached[0])
                    rec = type(rec)(
                        candidate_id=candidate_id,
                        source_name=rec.source_name,
                        query_type=rec.query_type,
                        query_string=rec.query_string,
                        matched=rec.matched,
                        match_score=rec.match_score,
                        external_id=rec.external_id,
                        title=rec.title,
                        authors_json=rec.authors_json,
                        abstract=rec.abstract,
                        venue=rec.venue,
                        year=rec.year,
                        publication_type=rec.publication_type,
                        doi=rec.doi,
                        pmid=rec.pmid,
                        pmcid=rec.pmcid,
                        url=rec.url,
                        raw_payload_json=rec.raw_payload_json,
                        latency_ms=0,
                    )
                    records.append(rec)
                    tracker.record_stage_cost(conn, stage='enrich_candidates', status='cache_hit', candidate_id=candidate_id, provider='pubmed')
                else:
                    rec = query_pubmed(candidate_id, pmid=pmid, title=norm_title, first_author_family=first_author_family, venue_hint=venue_guess, query_year=year_guess)
                    if rec:
                        records.append(rec)
                        repo.put_query_cache(conn, provider='pubmed', query_type=query_type, query_key=query_key, response_json=enrichment_record_to_json(rec))
            if doi or norm_title:
                query_type = 'doi' if doi else 'title'
                query_key = doi or norm_title or ''
                cached = repo.get_query_cache(conn, provider='crossref', query_type=query_type, query_key=query_key)
                if cached:
                    rec = enrichment_record_from_json(cached[0])
                    rec = type(rec)(
                        candidate_id=candidate_id,
                        source_name=rec.source_name,
                        query_type=rec.query_type,
                        query_string=rec.query_string,
                        matched=rec.matched,
                        match_score=rec.match_score,
                        external_id=rec.external_id,
                        title=rec.title,
                        authors_json=rec.authors_json,
                        abstract=rec.abstract,
                        venue=rec.venue,
                        year=rec.year,
                        publication_type=rec.publication_type,
                        doi=rec.doi,
                        pmid=rec.pmid,
                        pmcid=rec.pmcid,
                        url=rec.url,
                        raw_payload_json=rec.raw_payload_json,
                        latency_ms=0,
                    )
                    records.append(rec)
                    tracker.record_stage_cost(conn, stage='enrich_candidates', status='cache_hit', candidate_id=candidate_id, provider='crossref')
                else:
                    rec = query_crossref(candidate_id, doi=doi, title=norm_title, first_author_family=first_author_family, venue_hint=venue_guess, query_year=year_guess)
                    if rec:
                        records.append(rec)
                        repo.put_query_cache(conn, provider='crossref', query_type=query_type, query_key=query_key, response_json=enrichment_record_to_json(rec))
            if doi or norm_title:
                query_type = 'doi' if doi else 'title'
                query_key = doi or norm_title or ''
                cached = repo.get_query_cache(conn, provider='openalex', query_type=query_type, query_key=query_key)
                if cached:
                    rec = enrichment_record_from_json(cached[0])
                    rec = type(rec)(
                        candidate_id=candidate_id,
                        source_name=rec.source_name,
                        query_type=rec.query_type,
                        query_string=rec.query_string,
                        matched=rec.matched,
                        match_score=rec.match_score,
                        external_id=rec.external_id,
                        title=rec.title,
                        authors_json=rec.authors_json,
                        abstract=rec.abstract,
                        venue=rec.venue,
                        year=rec.year,
                        publication_type=rec.publication_type,
                        doi=rec.doi,
                        pmid=rec.pmid,
                        pmcid=rec.pmcid,
                        url=rec.url,
                        raw_payload_json=rec.raw_payload_json,
                        latency_ms=0,
                    )
                    records.append(rec)
                    tracker.record_stage_cost(conn, stage='enrich_candidates', status='cache_hit', candidate_id=candidate_id, provider='openalex')
                else:
                    rec = query_openalex(candidate_id, doi=doi, title=norm_title, first_author_family=first_author_family, venue_hint=venue_guess, query_year=year_guess)
                    if rec:
                        records.append(rec)
                        repo.put_query_cache(conn, provider='openalex', query_type=query_type, query_key=query_key, response_json=enrichment_record_to_json(rec))
            for rec in records:
                repo.insert_source_record(conn, rec)
                tracker.record_stage_cost(conn, stage='enrich_candidates', status='ok' if rec.matched else 'no_match', candidate_id=candidate_id, provider=rec.source_name, latency_ms=rec.latency_ms)
        repo.finish_batch_run(conn, run_id=run_id, duration_ms=int((time.perf_counter()-started_at)*1000), processed_count=len(rows), status='ok')
        conn.commit()
