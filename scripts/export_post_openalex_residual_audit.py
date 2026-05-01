#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

from mygooglealertpapers.config import load_settings
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.pipeline.candidate_resolution import cluster_candidates_within_batch
from mygooglealertpapers.pipeline.enrich import (
    _build_same_batch_clustered_intents,
    _experimental_post_openalex_non_suppression_reason,
    _prepare_dispatch_groups,
    _title_lane_reason_and_subreason_for_group,
)


@dataclass
class AuditRow:
    slice_name: str
    candidate_id: str
    fanout: int
    non_suppression_reason: str
    title_lane_reason: str | None
    title_lane_subreason: str | None
    norm_title: str | None
    first_author_family: str | None
    year_guess: str | None
    venue_guess: str | None
    url_canonical: str | None
    openalex_matched: int | None
    openalex_match_score: float | None
    openalex_title: str | None
    openalex_doi: str | None
    openalex_title_similarity: float | None
    openalex_title_token_jaccard: float | None
    crossref_matched: int | None
    crossref_match_score: float | None
    crossref_title: str | None
    crossref_doi: str | None
    crossref_title_similarity: float | None
    crossref_title_token_jaccard: float | None
    preferred_doi: str | None
    merge_confidence: float | None
    heuristic_bucket: str


TITLE_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _normalize_title(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.casefold().split())


def _token_set(text: str | None) -> set[str]:
    return set(TITLE_TOKEN_RE.findall(_normalize_title(text)))


def _sequence_similarity(left: str | None, right: str | None) -> float | None:
    if not left or not right:
        return None
    return round(SequenceMatcher(None, _normalize_title(left), _normalize_title(right)).ratio(), 4)


def _token_jaccard(left: str | None, right: str | None) -> float | None:
    left_tokens = _token_set(left)
    right_tokens = _token_set(right)
    if not left_tokens or not right_tokens:
        return None
    union = left_tokens | right_tokens
    if not union:
        return None
    return round(len(left_tokens & right_tokens) / len(union), 4)


def _heuristic_bucket(norm_title: str | None, openalex_title: str | None, crossref_title: str | None) -> str:
    oa_seq = _sequence_similarity(norm_title, openalex_title) or 0.0
    cr_seq = _sequence_similarity(norm_title, crossref_title) or 0.0
    oa_jac = _token_jaccard(norm_title, openalex_title) or 0.0
    cr_jac = _token_jaccard(norm_title, crossref_title) or 0.0
    if cr_seq >= 0.9 and cr_jac >= 0.85 and oa_seq < 0.55 and oa_jac < 0.4:
        return 'likely_openalex_recall_gap'
    if cr_seq >= 0.8 and oa_seq >= 0.5:
        return 'possible_normalization_or_ranking_issue'
    if cr_seq < 0.8:
        return 'source_title_noise_or_crossref_cleanup'
    return 'mixed_or_unclear'


def _latest_title_record_map(conn: sqlite3.Connection, provider: str) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        '''
        SELECT sr.*
        FROM source_record sr
        JOIN (
            SELECT candidate_id, MAX(id) AS max_id
            FROM source_record
            WHERE source_name = ? AND query_type = 'title'
            GROUP BY candidate_id
        ) last ON last.max_id = sr.id
        ''',
        (provider,),
    ).fetchall()
    return {row['candidate_id']: row for row in rows}


def _latest_merge_map(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    rows = conn.execute(
        '''
        SELECT mp.*
        FROM merged_metadata_proposal mp
        JOIN (
            SELECT candidate_id, MAX(id) AS max_id
            FROM merged_metadata_proposal
            GROUP BY candidate_id
        ) last ON last.max_id = mp.id
        '''
    ).fetchall()
    return {row['candidate_id']: row for row in rows}


def export_audit(source_db: Path, results_db: Path, policy_profile: Path, out_csv: Path, slice_name: str) -> dict[str, object]:
    os.environ['SQLITE_PATH'] = str(source_db)
    os.environ['MGAP_POLICY_PROFILE'] = str(policy_profile)
    settings = load_settings()
    repo = Repository(settings.sqlite_path)

    with repo.connect() as source_conn, sqlite3.connect(results_db) as results_conn:
        source_conn.row_factory = sqlite3.Row
        results_conn.row_factory = sqlite3.Row
        rows = source_conn.execute(
            '''
            SELECT pcn.candidate_id, pcn.norm_title, pcn.doi_extracted, pcn.pmid_extracted,
                   pcn.arxiv_id_extracted, pcn.first_author_family, pcn.venue_guess, pcn.year_guess,
                   pcn.pmcid_extracted, pcn.url_canonical, pcn.scholar_cluster_hint
            FROM paper_candidate_normalized pcn
            ORDER BY pcn.id ASC
            '''
        ).fetchall()
        row_by_candidate = {row['candidate_id']: row for row in rows}
        cluster_summary = cluster_candidates_within_batch(settings, repo, source_conn, rows)
        leader_to_followers = dict(cluster_summary.get('leader_to_followers') or {})
        intents = _build_same_batch_clustered_intents(settings, rows, cluster_summary)
        dispatch_groups, _, _ = _prepare_dispatch_groups(
            settings,
            intents,
            row_by_candidate=row_by_candidate,
            leader_to_followers=leader_to_followers,
        )

        openalex_map = _latest_title_record_map(results_conn, 'openalex')
        crossref_map = _latest_title_record_map(results_conn, 'crossref')
        merge_map = _latest_merge_map(results_conn)

        audit_rows: list[AuditRow] = []
        for group in dispatch_groups:
            title_lane_reason, title_lane_subreason = _title_lane_reason_and_subreason_for_group(
                group,
                row_by_candidate,
                leader_to_followers,
            )
            non_suppression_reason = _experimental_post_openalex_non_suppression_reason(
                settings,
                results_conn,
                group,
                title_lane_reason,
                title_lane_subreason,
            )
            if non_suppression_reason != 'openalex_title_unmatched':
                continue
            candidate_id = group.representative.candidate_id
            source_row = row_by_candidate[candidate_id]
            openalex_row = openalex_map.get(candidate_id)
            crossref_row = crossref_map.get(candidate_id)
            merge_row = merge_map.get(candidate_id)
            audit_rows.append(
                AuditRow(
                    slice_name=slice_name,
                    candidate_id=candidate_id,
                    fanout=len(group.intents),
                    non_suppression_reason=non_suppression_reason,
                    title_lane_reason=title_lane_reason,
                    title_lane_subreason=title_lane_subreason,
                    norm_title=source_row['norm_title'],
                    first_author_family=source_row['first_author_family'],
                    year_guess=source_row['year_guess'],
                    venue_guess=source_row['venue_guess'],
                    url_canonical=source_row['url_canonical'],
                    openalex_matched=(int(openalex_row['matched']) if openalex_row is not None and openalex_row['matched'] is not None else None),
                    openalex_match_score=(float(openalex_row['match_score']) if openalex_row is not None and openalex_row['match_score'] is not None else None),
                    openalex_title=(openalex_row['title'] if openalex_row is not None else None),
                    openalex_doi=(openalex_row['doi'] if openalex_row is not None else None),
                    openalex_title_similarity=_sequence_similarity(source_row['norm_title'], openalex_row['title'] if openalex_row is not None else None),
                    openalex_title_token_jaccard=_token_jaccard(source_row['norm_title'], openalex_row['title'] if openalex_row is not None else None),
                    crossref_matched=(int(crossref_row['matched']) if crossref_row is not None and crossref_row['matched'] is not None else None),
                    crossref_match_score=(float(crossref_row['match_score']) if crossref_row is not None and crossref_row['match_score'] is not None else None),
                    crossref_title=(crossref_row['title'] if crossref_row is not None else None),
                    crossref_doi=(crossref_row['doi'] if crossref_row is not None else None),
                    crossref_title_similarity=_sequence_similarity(source_row['norm_title'], crossref_row['title'] if crossref_row is not None else None),
                    crossref_title_token_jaccard=_token_jaccard(source_row['norm_title'], crossref_row['title'] if crossref_row is not None else None),
                    preferred_doi=(merge_row['preferred_doi'] if merge_row is not None else None),
                    merge_confidence=(float(merge_row['merge_confidence']) if merge_row is not None and merge_row['merge_confidence'] is not None else None),
                    heuristic_bucket=_heuristic_bucket(
                        source_row['norm_title'],
                        openalex_row['title'] if openalex_row is not None else None,
                        crossref_row['title'] if crossref_row is not None else None,
                    ),
                )
            )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(audit_rows[0]).keys()) if audit_rows else list(AuditRow.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(asdict(row))

    summary = {
        'slice_name': slice_name,
        'source_db': str(source_db),
        'results_db': str(results_db),
        'policy_profile': str(policy_profile),
        'out_csv': str(out_csv),
        'row_count': len(audit_rows),
        'heuristic_bucket_counts': {},
    }
    for row in audit_rows:
        summary['heuristic_bucket_counts'][row.heuristic_bucket] = summary['heuristic_bucket_counts'].get(row.heuristic_bucket, 0) + 1
    return summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Export candidate-level audit rows for unsuppressed post-openalex residual title groups.')
    p.add_argument('--source-db', required=True)
    p.add_argument('--results-db', required=True)
    p.add_argument('--policy-profile', required=True)
    p.add_argument('--out-csv', required=True)
    p.add_argument('--slice-name', required=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_audit(
        source_db=Path(args.source_db).resolve(),
        results_db=Path(args.results_db).resolve(),
        policy_profile=Path(args.policy_profile).resolve(),
        out_csv=Path(args.out_csv).resolve(),
        slice_name=args.slice_name,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
