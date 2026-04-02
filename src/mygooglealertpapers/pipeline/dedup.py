from __future__ import annotations

import json
import logging
import uuid

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository

logger = logging.getLogger(__name__)


def _new_paper_id() -> str:
    return f"paper_{uuid.uuid4().hex[:16]}"


def deduplicate_candidates(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    with repo.connect() as conn:
        rows = conn.execute(
            """
            SELECT pcn.candidate_id, pcn.norm_title, pcn.norm_title_key, pcn.first_author_family,
                   pcn.year_guess, pcn.doi_extracted, pcn.pmid_extracted, pcn.pmcid_extracted,
                   mmp.preferred_title, mmp.preferred_authors_json, mmp.preferred_abstract,
                   mmp.preferred_venue, mmp.preferred_year, mmp.preferred_doi, mmp.preferred_pmid,
                   mmp.preferred_publication_type
            FROM paper_candidate_normalized pcn
            JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id
            LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id
            WHERE cpl.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        logger.info('Found %s candidate(s) for dedup scaffold', len(rows))
        for row in rows:
            (
                candidate_id, norm_title, norm_title_key, first_author_family,
                year_guess, doi_extracted, pmid_extracted, pmcid_extracted,
                preferred_title, preferred_authors_json, preferred_abstract,
                preferred_venue, preferred_year, preferred_doi, preferred_pmid,
                preferred_publication_type,
            ) = row

            paper = None
            evidence = {}

            if preferred_doi or doi_extracted:
                doi = preferred_doi or doi_extracted
                paper = conn.execute(
                    'SELECT paper_id FROM canonical_paper WHERE canonical_doi = ? LIMIT 1',
                    (doi,),
                ).fetchone()
                if paper:
                    evidence = {'rule': 'doi_exact', 'doi': doi}

            if paper is None and (preferred_pmid or pmid_extracted):
                pmid = preferred_pmid or pmid_extracted
                paper = conn.execute(
                    'SELECT paper_id FROM canonical_paper WHERE canonical_pmid = ? LIMIT 1',
                    (pmid,),
                ).fetchone()
                if paper:
                    evidence = {'rule': 'pmid_exact', 'pmid': pmid}

            if paper is None and pmcid_extracted:
                paper = conn.execute(
                    'SELECT paper_id FROM canonical_paper WHERE canonical_pmcid = ? LIMIT 1',
                    (pmcid_extracted,),
                ).fetchone()
                if paper:
                    evidence = {'rule': 'pmcid_exact', 'pmcid': pmcid_extracted}

            if paper is None and norm_title_key and first_author_family and year_guess:
                paper = conn.execute(
                    '''
                    SELECT paper_id FROM canonical_paper
                    WHERE canonical_title_key = ? AND first_author_family = ? AND canonical_year = ?
                    LIMIT 1
                    ''',
                    (norm_title_key, first_author_family, year_guess),
                ).fetchone()
                if paper:
                    evidence = {'rule': 'title_author_year_exact', 'title_key': norm_title_key, 'first_author_family': first_author_family, 'year': year_guess}

            if paper is None and norm_title_key and first_author_family:
                paper = conn.execute(
                    '''
                    SELECT paper_id FROM canonical_paper
                    WHERE canonical_title_key = ? AND first_author_family = ?
                    LIMIT 1
                    ''',
                    (norm_title_key, first_author_family),
                ).fetchone()
                if paper:
                    evidence = {'rule': 'title_author_exact', 'title_key': norm_title_key, 'first_author_family': first_author_family}

            if paper is None:
                paper_id = _new_paper_id()
                conn.execute(
                    """
                    INSERT INTO canonical_paper (
                        paper_id, canonical_title, canonical_title_key, canonical_authors_json,
                        canonical_abstract, canonical_venue, canonical_year, canonical_doi,
                        canonical_pmid, canonical_pmcid, publication_type, first_author_family,
                        version_preference, influence_metrics_json, topic_signals_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        paper_id,
                        preferred_title or norm_title,
                        norm_title_key,
                        preferred_authors_json,
                        preferred_abstract,
                        preferred_venue,
                        preferred_year or year_guess,
                        preferred_doi or doi_extracted,
                        preferred_pmid or pmid_extracted,
                        pmcid_extracted,
                        preferred_publication_type,
                        first_author_family,
                        'unknown',
                        '{}',
                        '{}',
                    ),
                )
                evidence = {'rule': 'new_canonical'}
            else:
                paper_id = paper[0]

            conn.execute(
                """
                INSERT INTO candidate_paper_link (
                    candidate_id, paper_id, relation_type, confidence, evidence_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    paper_id,
                    'assigned',
                    0.95 if evidence.get('rule') in {'doi_exact', 'pmid_exact', 'pmcid_exact'} else 0.75 if evidence.get('rule') != 'new_canonical' else 0.6,
                    json.dumps(evidence, ensure_ascii=False),
                ),
            )
            tracker.record_stage_cost(conn, stage='dedup_candidates', status='ok', candidate_id=candidate_id, notes=json.dumps(evidence, ensure_ascii=False))
        conn.commit()
