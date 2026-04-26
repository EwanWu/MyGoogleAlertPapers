from __future__ import annotations

import json
import logging
import time
import uuid

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.db.schema import create_schema
from mygooglealertpapers.enrich.base import cache_metadata_from_record, cache_status_from_record, enrichment_record_from_json, enrichment_record_to_json
from mygooglealertpapers.enrich.unpaywall import query_unpaywall

logger = logging.getLogger(__name__)

PROGRESS_EVERY = 25


def _status_from_record(rec) -> tuple[str, str | None]:
    if rec.matched:
        return 'ok', None
    try:
        payload = json.loads(rec.raw_payload_json or '{}')
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        if payload.get('http_error') == 404:
            return 'no_match', None
        if payload.get('error'):
            return 'error', str(payload.get('error'))
        if payload.get('http_error'):
            return 'error', f"http_error:{payload.get('http_error')}"
    return 'no_match', None


def _extract_snapshot_fields(rec) -> dict[str, object]:
    try:
        payload = json.loads(rec.raw_payload_json or '{}')
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    best_oa_location = payload.get('best_oa_location') or {}
    if not isinstance(best_oa_location, dict):
        best_oa_location = {}
    return {
        'doi': rec.doi,
        'is_oa': payload.get('is_oa') if 'is_oa' in payload else (True if rec.matched and rec.match_score == 1.0 else False if rec.matched else None),
        'oa_status': payload.get('oa_status'),
        'best_oa_url': best_oa_location.get('url') or rec.url,
        'best_oa_host_type': best_oa_location.get('host_type'),
        'best_oa_version': best_oa_location.get('version'),
        'license': best_oa_location.get('license'),
        'raw_payload_json': rec.raw_payload_json,
    }


def enrich_paper_oa(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'enrich_paper_oa_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        create_schema(conn)
        repo.start_batch_run(conn, run_id=run_id, stage='enrich_paper_oa', requested_limit=limit, notes='post_dedup_unpaywall')
        rows = conn.execute(
            '''
            SELECT cp.paper_id, cp.canonical_doi
            FROM canonical_paper cp
            LEFT JOIN paper_oa_enrichment_status poas
              ON poas.paper_id = cp.paper_id AND poas.provider = 'unpaywall'
            WHERE cp.canonical_doi IS NOT NULL
              AND (poas.id IS NULL OR poas.status = 'error')
            ORDER BY cp.id ASC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
        logger.info('Found %s canonical paper(s) with DOI requiring OA enrichment', len(rows))

        processed = 0
        for paper_id, doi in rows:
            repo.start_paper_oa_status(conn, paper_id=paper_id, provider='unpaywall', query_type='doi', query_key=doi, notes='post_dedup_oa_enrichment')
            cached = repo.get_query_cache(conn, provider='unpaywall', query_type='doi', query_key=doi)
            cache_hit = False
            rec = None
            if cached is not None:
                cached_rec = enrichment_record_from_json(cached[0])
                if cache_status_from_record(cached_rec) != 'transient_error':
                    rec = cached_rec
                    rec.latency_ms = 0
                    cache_hit = True

            if rec is None:
                if not settings.unpaywall_email:
                    raise RuntimeError(f'UNPAYWALL_EMAIL is required for live Unpaywall query: {doi}')
                rec = query_unpaywall(paper_id, doi=doi, email=settings.unpaywall_email)
                if rec is None:
                    raise RuntimeError(f'unexpected None from query_unpaywall for DOI {doi}')
                repo.put_query_cache(
                    conn,
                    provider='unpaywall',
                    query_type='doi',
                    query_key=doi,
                    response_json=enrichment_record_to_json(rec),
                    **cache_metadata_from_record(rec),
                )

            status, error_summary = _status_from_record(rec)
            if status != 'error':
                snapshot = _extract_snapshot_fields(rec)
                repo.upsert_paper_open_access(
                    conn,
                    paper_id=paper_id,
                    provider='unpaywall',
                    doi=snapshot['doi'],
                    is_oa=snapshot['is_oa'],
                    oa_status=snapshot['oa_status'],
                    best_oa_url=snapshot['best_oa_url'],
                    best_oa_host_type=snapshot['best_oa_host_type'],
                    best_oa_version=snapshot['best_oa_version'],
                    license=snapshot['license'],
                    raw_payload_json=snapshot['raw_payload_json'],
                )
            repo.finish_paper_oa_status(
                conn,
                paper_id=paper_id,
                provider='unpaywall',
                status=status,
                cache_hit=cache_hit,
                latency_ms=rec.latency_ms,
                error_summary=error_summary,
                notes='post_dedup_oa_enrichment',
            )
            tracker.record_stage_cost(
                conn,
                stage='enrich_paper_oa',
                status='cache_hit' if cache_hit else status,
                provider='unpaywall',
                latency_ms=rec.latency_ms,
                notes=json.dumps({'paper_id': paper_id, 'doi': doi, 'post_dedup': True}, ensure_ascii=False),
            )
            processed += 1
            if processed % PROGRESS_EVERY == 0:
                logger.info('Post-dedup OA enrichment progress: processed %s / %s paper(s)', processed, len(rows))
                conn.commit()

        repo.finish_batch_run(
            conn,
            run_id=run_id,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            processed_count=processed,
            status='ok',
            notes='post_dedup_unpaywall',
        )
        conn.commit()


def build_paper_oa_stats(db_path) -> str:
    repo = Repository(db_path)
    with repo.connect() as conn:
        create_schema(conn)
        total_doi = conn.execute('SELECT COUNT(*) FROM canonical_paper WHERE canonical_doi IS NOT NULL').fetchone()[0]
        snapshot_count = conn.execute('SELECT COUNT(*) FROM paper_open_access').fetchone()[0]
        oa_true = conn.execute('SELECT COUNT(*) FROM paper_open_access WHERE is_oa = 1').fetchone()[0]
        url_count = conn.execute('SELECT COUNT(*) FROM paper_open_access WHERE best_oa_url IS NOT NULL AND TRIM(best_oa_url) != ""').fetchone()[0]
        status_rows = conn.execute(
            '''
            SELECT COALESCE(oa_status, 'unknown'), COUNT(*)
            FROM paper_open_access
            GROUP BY COALESCE(oa_status, 'unknown')
            ORDER BY COUNT(*) DESC, COALESCE(oa_status, 'unknown') ASC
            '''
        ).fetchall()
        run_rows = conn.execute(
            '''
            SELECT status, COUNT(*)
            FROM paper_oa_enrichment_status
            GROUP BY status
            ORDER BY COUNT(*) DESC, status ASC
            '''
        ).fetchall()

    lines = [
        'Post-dedup OA enrichment stats',
        f'- canonical papers with DOI: {total_doi}',
        f'- paper_open_access rows: {snapshot_count}',
        f'- is_oa=true rows: {oa_true}',
        f'- best_oa_url filled rows: {url_count}',
        '- oa_status breakdown:',
    ]
    if status_rows:
        lines.extend([f'  - {status}: {count}' for status, count in status_rows])
    else:
        lines.append('  - none')
    lines.append('- enrichment status breakdown:')
    if run_rows:
        lines.extend([f'  - {status}: {count}' for status, count in run_rows])
    else:
        lines.append('  - none')
    return '\n'.join(lines)
