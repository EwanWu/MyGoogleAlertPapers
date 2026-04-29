from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository


@dataclass(slots=True)
class LibraryPrelinkMatch:
    paper_id: str
    rule: str
    alias_type: str | None
    alias_key: str | None
    confidence: float


EXACT_CLUSTER_PRIORITY: list[tuple[str, str, float]] = [
    ('doi', 'doi_exact_cluster', 1.0),
    ('pmid', 'pmid_exact_cluster', 1.0),
    ('pmcid', 'pmcid_exact_cluster', 1.0),
    ('arxiv', 'arxiv_exact_cluster', 0.99),
    ('scholar_cluster', 'scholar_cluster_exact_cluster', 0.98),
    ('url_canonical', 'url_canonical_exact_cluster', 0.97),
]


def _runtime_value(settings: Settings, key: str, default: object = None) -> object:
    return settings.policy_profile.runtime_value(key, default)


def library_prelink_enabled(settings: Settings) -> bool:
    return bool(_runtime_value(settings, 'library_prelink_enabled', True))


def same_batch_clustering_enabled(settings: Settings) -> bool:
    return bool(_runtime_value(settings, 'same_batch_clustering_enabled', False))


def _normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    if text.startswith('https://doi.org/'):
        text = text[len('https://doi.org/'):]
    return text or None


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _normalize_arxiv(value: str | None) -> str | None:
    text = _normalize_text(value)
    return text.lower() if text else None


def _normalize_scholar_cluster(value: str | None) -> str | None:
    text = _normalize_text(value)
    if not text:
        return None
    parsed = urlparse(text)
    query = parse_qs(parsed.query)
    cluster = query.get('cluster', [None])[0]
    if cluster:
        cluster = cluster.strip()
        return cluster or None
    return text


def _candidate_exact_keys(row: sqlite3.Row | tuple) -> dict[str, str]:
    if isinstance(row, sqlite3.Row):
        doi = row['doi_extracted'] if 'doi_extracted' in row.keys() else None
        pmid = row['pmid_extracted'] if 'pmid_extracted' in row.keys() else None
        pmcid = row['pmcid_extracted'] if 'pmcid_extracted' in row.keys() else None
        arxiv_id = row['arxiv_id_extracted'] if 'arxiv_id_extracted' in row.keys() else None
        url_canonical = row['url_canonical'] if 'url_canonical' in row.keys() else None
        scholar_cluster_hint = row['scholar_cluster_hint'] if 'scholar_cluster_hint' in row.keys() else None
    else:
        _, _, doi, pmid, pmcid, arxiv_id, url_canonical, scholar_cluster_hint = row
    result: dict[str, str] = {}
    if norm := _normalize_doi(doi):
        result['doi'] = norm
    if norm := _normalize_text(pmid):
        result['pmid'] = norm
    if norm := _normalize_text(pmcid):
        result['pmcid'] = norm.upper()
    if norm := _normalize_arxiv(arxiv_id):
        result['arxiv'] = norm
    if norm := _normalize_text(url_canonical):
        result['url_canonical'] = norm
    if norm := _normalize_scholar_cluster(scholar_cluster_hint):
        result['scholar_cluster'] = norm
    return result


def _pick_cluster_leader(component_rows: list[sqlite3.Row | tuple], order_index: dict[str, int]) -> sqlite3.Row | tuple:
    def score(row: sqlite3.Row | tuple) -> tuple[int, int, int, int, int, int, int, int]:
        keys = _candidate_exact_keys(row)
        candidate_id = row[0]
        norm_title = row[1]
        return (
            int('doi' in keys),
            int('pmid' in keys),
            int('pmcid' in keys),
            int('arxiv' in keys),
            int('scholar_cluster' in keys),
            int('url_canonical' in keys),
            int(bool(norm_title)),
            -order_index.get(candidate_id, 0),
        )

    return max(component_rows, key=score)


def cluster_candidates_within_batch(
    settings: Settings,
    repo: Repository,
    conn: sqlite3.Connection,
    rows: list[sqlite3.Row | tuple],
) -> dict[str, object]:
    if not same_batch_clustering_enabled(settings):
        return {
            'enabled': False,
            'leader_to_followers': {},
            'follower_to_leader': {},
            'clustered_candidate_count': 0,
            'cluster_group_count': 0,
            'rule_counts': {},
        }

    row_by_candidate = {row[0]: row for row in rows}
    order_index = {row[0]: idx for idx, row in enumerate(rows)}
    parent = {candidate_id: candidate_id for candidate_id in row_by_candidate}

    def find(candidate_id: str) -> str:
        root = candidate_id
        while parent[root] != root:
            root = parent[root]
        while parent[candidate_id] != candidate_id:
            nxt = parent[candidate_id]
            parent[candidate_id] = root
            candidate_id = nxt
        return root

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if order_index[left_root] <= order_index[right_root]:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    buckets: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        candidate_id = row[0]
        for alias_type, alias_key in _candidate_exact_keys(row).items():
            buckets.setdefault((alias_type, alias_key), []).append(candidate_id)

    for candidate_ids in buckets.values():
        if len(candidate_ids) < 2:
            continue
        leader = candidate_ids[0]
        for follower in candidate_ids[1:]:
            union(leader, follower)

    components: dict[str, list[str]] = {}
    for candidate_id in row_by_candidate:
        components.setdefault(find(candidate_id), []).append(candidate_id)

    leader_to_followers: dict[str, list[str]] = {}
    follower_to_leader: dict[str, str] = {}
    rule_counts: dict[str, int] = {}
    cluster_group_count = 0

    for component_candidate_ids in components.values():
        if len(component_candidate_ids) < 2:
            continue
        component_rows = [row_by_candidate[candidate_id] for candidate_id in sorted(component_candidate_ids, key=lambda cid: order_index[cid])]
        leader_row = _pick_cluster_leader(component_rows, order_index)
        leader_candidate_id = leader_row[0]
        leader_keys = _candidate_exact_keys(leader_row)
        cluster_group_count += 1

        shared_alias_type = None
        shared_alias_key = None
        shared_rule = 'same_batch_exact_cluster'
        shared_confidence = 0.97
        for alias_type, rule, confidence in EXACT_CLUSTER_PRIORITY:
            alias_key = leader_keys.get(alias_type)
            if not alias_key:
                continue
            member_count = sum(1 for row in component_rows if _candidate_exact_keys(row).get(alias_type) == alias_key)
            if member_count >= 2:
                shared_alias_type = alias_type
                shared_alias_key = alias_key
                shared_rule = rule
                shared_confidence = confidence
                break

        followers = [candidate_id for candidate_id in sorted(component_candidate_ids, key=lambda cid: order_index[cid]) if candidate_id != leader_candidate_id]
        if not followers:
            continue
        leader_to_followers[leader_candidate_id] = followers
        rule_counts[shared_rule] = rule_counts.get(shared_rule, 0) + len(followers)

        for follower_candidate_id in followers:
            follower_to_leader[follower_candidate_id] = leader_candidate_id
            evidence = {
                'rule': shared_rule,
                'leader_candidate_id': leader_candidate_id,
                'shared_alias_type': shared_alias_type,
                'shared_alias_key': shared_alias_key,
                'confidence': shared_confidence,
                'cluster_candidate_ids': [leader_candidate_id, *followers],
            }
            repo.upsert_candidate_resolution_status(
                conn,
                candidate_id=follower_candidate_id,
                resolution_stage='same_batch_cluster',
                resolution_rule=shared_rule,
                paper_id=None,
                leader_candidate_id=leader_candidate_id,
                status='clustered',
                evidence_json=json.dumps(evidence, ensure_ascii=False),
            )

    return {
        'enabled': True,
        'leader_to_followers': leader_to_followers,
        'follower_to_leader': follower_to_leader,
        'clustered_candidate_count': len(follower_to_leader),
        'cluster_group_count': cluster_group_count,
        'rule_counts': rule_counts,
    }


def _ensure_identity_aliases(repo: Repository, conn: sqlite3.Connection) -> None:
    repo.refresh_paper_identity_aliases_from_links(conn)


def _find_library_prelink(repo: Repository, conn: sqlite3.Connection, row: sqlite3.Row | tuple) -> LibraryPrelinkMatch | None:
    keys = _candidate_exact_keys(row)

    if doi := keys.get('doi'):
        paper = repo.find_canonical_paper_by_field(conn, field_name='canonical_doi', field_value=doi)
        if paper:
            return LibraryPrelinkMatch(paper_id=paper[0], rule='doi_exact', alias_type='doi', alias_key=doi, confidence=1.0)

    if pmid := keys.get('pmid'):
        paper = repo.find_canonical_paper_by_field(conn, field_name='canonical_pmid', field_value=pmid)
        if paper:
            return LibraryPrelinkMatch(paper_id=paper[0], rule='pmid_exact', alias_type='pmid', alias_key=pmid, confidence=1.0)

    if pmcid := keys.get('pmcid'):
        paper = repo.find_canonical_paper_by_field(conn, field_name='canonical_pmcid', field_value=pmcid)
        if paper:
            return LibraryPrelinkMatch(paper_id=paper[0], rule='pmcid_exact', alias_type='pmcid', alias_key=pmcid, confidence=1.0)

    for alias_type, rule, confidence in [
        ('arxiv', 'arxiv_exact', 0.99),
        ('scholar_cluster', 'scholar_cluster_exact', 0.98),
        ('url_canonical', 'url_canonical_exact', 0.97),
    ]:
        alias_key = keys.get(alias_type)
        if not alias_key:
            continue
        paper = repo.find_paper_by_identity_alias(conn, alias_type=alias_type, alias_key=alias_key)
        if paper:
            return LibraryPrelinkMatch(paper_id=paper[0], rule=rule, alias_type=alias_type, alias_key=alias_key, confidence=confidence)

    return None


def prelink_candidates_against_library(
    settings: Settings,
    repo: Repository,
    tracker: CostTracker,
    conn: sqlite3.Connection,
    rows: list[sqlite3.Row | tuple],
) -> dict[str, object]:
    if not library_prelink_enabled(settings):
        return {
            'enabled': False,
            'prelinked_candidate_ids': set(),
            'prelinked_candidate_count': 0,
            'rule_counts': {},
        }

    _ensure_identity_aliases(repo, conn)
    prelinked_ids: set[str] = set()
    rule_counts: dict[str, int] = {}
    for row in rows:
        candidate_id = row[0]
        if conn.execute('SELECT 1 FROM candidate_paper_link WHERE candidate_id = ? LIMIT 1', (candidate_id,)).fetchone():
            continue
        match = _find_library_prelink(repo, conn, row)
        if match is None:
            continue
        evidence = {
            'rule': match.rule,
            'paper_id': match.paper_id,
            'alias_type': match.alias_type,
            'alias_key': match.alias_key,
            'confidence': match.confidence,
        }
        repo.upsert_candidate_paper_link(
            conn,
            candidate_id=candidate_id,
            paper_id=match.paper_id,
            relation_type='library_prelinked',
            confidence=match.confidence,
            evidence_json=json.dumps(evidence, ensure_ascii=False),
        )
        repo.upsert_candidate_resolution_status(
            conn,
            candidate_id=candidate_id,
            resolution_stage='library_prelink',
            resolution_rule=match.rule,
            paper_id=match.paper_id,
            leader_candidate_id=None,
            status='linked',
            evidence_json=json.dumps(evidence, ensure_ascii=False),
        )
        tracker.record_stage_cost(
            conn,
            stage='resolve_candidates',
            status='prelinked',
            candidate_id=candidate_id,
            latency_ms=0,
            notes=json.dumps(evidence, ensure_ascii=False),
        )
        prelinked_ids.add(candidate_id)
        rule_counts[match.rule] = rule_counts.get(match.rule, 0) + 1

    return {
        'enabled': True,
        'prelinked_candidate_ids': prelinked_ids,
        'prelinked_candidate_count': len(prelinked_ids),
        'rule_counts': rule_counts,
    }


def resolve_candidates_against_library(settings: Settings, *, limit: int) -> dict[str, object]:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'resolve_candidates_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='resolve_candidates', requested_limit=limit, notes=None)
        rows = conn.execute(
            '''
            SELECT pcn.candidate_id, pcn.norm_title, pcn.doi_extracted, pcn.pmid_extracted,
                   pcn.pmcid_extracted, pcn.arxiv_id_extracted, pcn.url_canonical, pcn.scholar_cluster_hint
            FROM paper_candidate_normalized pcn
            LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id
            WHERE cpl.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
        summary = prelink_candidates_against_library(settings, repo, tracker, conn, rows)
        payload = {
            'library_prelink_enabled': summary['enabled'],
            'candidate_count': len(rows),
            'library_prelinked_candidate_count': summary['prelinked_candidate_count'],
            'library_prelink_rule_counts': summary['rule_counts'],
        }
        repo.finish_batch_run(
            conn,
            run_id=run_id,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            processed_count=len(rows),
            status='ok',
            notes=json.dumps(payload, ensure_ascii=False),
        )
        conn.commit()
        return payload
