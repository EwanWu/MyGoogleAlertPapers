from __future__ import annotations

import logging
import time
import uuid
import sqlite3

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.normalize.authors import authors_to_json, first_author_family
from mygooglealertpapers.normalize.identifiers import canonicalize_url, extract_arxiv_id, extract_doi, extract_pmcid, extract_pmid
from mygooglealertpapers.normalize.text import clean_venue
from mygooglealertpapers.normalize.title import make_title_key, normalize_title

logger = logging.getLogger(__name__)


def normalize_candidates(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'normalize_candidates_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='normalize_candidates', requested_limit=limit, notes=None)
        rows = conn.execute(
            """
            SELECT pc.candidate_id, pc.raw_title, pc.raw_authors, pc.raw_link, pc.raw_snippet,
                   pc.target_url, pc.venue_guess, pc.year_guess
            FROM paper_candidate pc
            LEFT JOIN paper_candidate_normalized pcn ON pcn.candidate_id = pc.candidate_id
            WHERE pcn.id IS NULL
            ORDER BY pc.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        logger.info("Found %s unnormalized candidate(s)", len(rows))
        for row in rows:
            candidate_id, raw_title, raw_authors, raw_link, raw_snippet, target_url, venue_guess, year_guess = row
            url_source = target_url or raw_link
            combined_text = "\n".join(x for x in [raw_title, raw_link, raw_snippet, target_url] if x)
            conn.execute(
                """
                INSERT INTO paper_candidate_normalized (
                    candidate_id, norm_title, norm_title_key, norm_authors_json,
                    first_author_family, year_guess, venue_guess, doi_extracted,
                    pmid_extracted, pmcid_extracted, arxiv_id_extracted,
                    url_canonical, scholar_cluster_hint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    normalize_title(raw_title),
                    make_title_key(raw_title),
                    authors_to_json(raw_authors),
                    first_author_family(raw_authors),
                    year_guess,
                    clean_venue(venue_guess),
                    extract_doi(combined_text),
                    extract_pmid(combined_text),
                    extract_pmcid(combined_text) or extract_pmcid(url_source),
                    extract_arxiv_id(combined_text),
                    canonicalize_url(url_source),
                    url_source if url_source and 'scholar.google.com/scholar?cluster=' in url_source else None,
                ),
            )
            tracker.record_stage_cost(conn, stage="normalize_candidates", status="ok", candidate_id=candidate_id)
        repo.finish_batch_run(conn, run_id=run_id, duration_ms=int((time.perf_counter()-started_at)*1000), processed_count=len(rows), status='ok')
        conn.commit()
