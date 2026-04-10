from __future__ import annotations

import json
import logging
import re
import time
import uuid
from difflib import SequenceMatcher
from urllib.parse import urlparse

from mygooglealertpapers.config import Settings
from mygooglealertpapers.normalize.text import clean_abstract, clean_text, clean_title, clean_venue, comparison_text
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository

logger = logging.getLogger(__name__)

SOURCE_PRIORITY = {
    'crossref': 4,
    'openalex': 3,
    'semanticscholar': 2,
    'pubmed': 1,
}

GRADE_ORDER = {'A': 1, 'B': 2, 'C': 3}
BLOCKING_GRADE_C_FIELDS = {'doi', 'pmid', 'pmcid', 'title'}
VENUE_ABBREVIATIONS = {
    'jacc': 'journal of the american college of cardiology',
    'jacc cardiovascular imaging': 'jacc cardiovascular imaging',
    'cjca': 'canadian journal of cardiology',
    'mrm': 'magnetic resonance in medicine',
    'bmj open': 'bmj open',
}
STOPWORD_TOKENS = {'the', 'of', 'and', 'in', 'for', 'journal'}


def _clean_text(value: str | None) -> str | None:
    return clean_text(value)


def _field_clean_text(field: str, value: str | None) -> str | None:
    if field == 'title':
        return clean_title(value)
    if field == 'venue':
        return clean_venue(value)
    if field == 'abstract':
        return clean_abstract(value)
    return clean_text(value)


def _normalize_conflict_value(field: str, value: str | None) -> str | None:
    text = _field_clean_text(field, value)
    if not text:
        return None
    if field in {'title', 'venue'}:
        text = text.casefold().rstrip(' .')
    elif field == 'doi':
        text = text.casefold().strip()
        if text.startswith('https://doi.org/'):
            text = text[len('https://doi.org/'):]
        text = text.rstrip(' ./')
    elif field in {'pmid', 'pmcid'}:
        text = text.strip().upper() if field == 'pmcid' else text.strip()
    elif field == 'year':
        text = text.strip()
    return text or None


def _comparison_text(value: str | None) -> str:
    return comparison_text(value)


def _normalize_venue_alias(value: str | None) -> str:
    text = _comparison_text(value)
    if not text:
        return ''
    text = VENUE_ABBREVIATIONS.get(text, text)
    if text.startswith('the '):
        text = text[4:]
    text = text.replace(' alzheimer s ', " alzheimer's ")
    text = text.replace('cardiovascular imaging', 'cardiovascular imaging')
    text = re.sub(r'\bjournal\b', 'journal', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return VENUE_ABBREVIATIONS.get(text, text)


def _venue_token_signature(value: str | None) -> set[str]:
    text = _normalize_venue_alias(value)
    if not text:
        return set()
    tokens = {tok for tok in text.split() if tok and tok not in STOPWORD_TOKENS}
    return tokens


def _venue_equivalent(left: str | None, right: str | None) -> bool:
    a = _normalize_venue_alias(left)
    b = _normalize_venue_alias(right)
    if not a or not b:
        return False
    if a == b:
        return True
    if a in b or b in a:
        return True
    a_tokens = _venue_token_signature(left)
    b_tokens = _venue_token_signature(right)
    if a_tokens and a_tokens == b_tokens:
        return True
    if a_tokens and b_tokens and len(a_tokens & b_tokens) / len(a_tokens | b_tokens) >= 0.9:
        return True
    return False


def _pairwise_min_similarity(values: list[str]) -> float:
    if len(values) < 2:
        return 1.0
    min_sim = 1.0
    for i, left in enumerate(values):
        for right in values[i + 1:]:
            sim = SequenceMatcher(None, left, right).ratio()
            min_sim = min(min_sim, sim)
    return min_sim


def _token_jaccard(a: str, b: str) -> float:
    left = set(a.split())
    right = set(b.split())
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _titles_look_like_variants(values: list[str]) -> bool:
    comparison_values = [_comparison_text(v) for v in values if _comparison_text(v)]
    if len(comparison_values) < 2:
        return True
    for i, left in enumerate(comparison_values):
        for right in comparison_values[i + 1:]:
            if left == right:
                continue
            shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
            if shorter and (longer.startswith(shorter) or shorter in longer):
                if len(shorter) / max(len(longer), 1) >= 0.55:
                    continue
            if _token_jaccard(left, right) >= 0.72:
                continue
            return False
    return True


def _grade_conflict(field: str, values: list[str]) -> str:
    if field in {'doi', 'pmid', 'pmcid'}:
        return 'C'
    if field == 'year':
        years = []
        for value in values:
            try:
                years.append(int(str(value)))
            except Exception:
                pass
        if len(years) >= 2 and max(years) - min(years) <= 1:
            return 'B'
        return 'C'

    comparison_values = [_comparison_text(v) for v in values if _comparison_text(v)]
    min_sim = _pairwise_min_similarity(comparison_values)

    if field == 'title':
        if min_sim >= 0.985:
            return 'A'
        if min_sim >= 0.92:
            return 'B'
        if _titles_look_like_variants(values):
            return 'B'
        return 'C'

    if field == 'venue':
        if all(_venue_equivalent(values[0], other) for other in values[1:]):
            return 'A'
        normalized_values = [_normalize_venue_alias(v) for v in values if _normalize_venue_alias(v)]
        if len(normalized_values) >= 2:
            venue_sim = _pairwise_min_similarity(normalized_values)
            if venue_sim >= 0.96:
                return 'A'
            if venue_sim >= 0.88:
                return 'B'
        if min_sim >= 0.9:
            return 'B'
        return 'C'

    return 'B'


def _venue_rough_match(left: str | None, right: str | None) -> bool:
    if _venue_equivalent(left, right):
        return True
    a = _comparison_text(left)
    b = _comparison_text(right)
    if not a or not b:
        return False
    return a == b or a in b or b in a or _pairwise_min_similarity([a, b]) >= 0.9


def _is_non_ncbi_candidate_url(url: str | None) -> bool:
    if not url:
        return False
    host = (urlparse(url).netloc or '').casefold()
    if not host:
        return False
    return all(token not in host for token in ['pubmed.ncbi.nlm.nih.gov', 'pmc.ncbi.nlm.nih.gov', 'ncbi.nlm.nih.gov'])


def _apply_pubmed_doi_suppression(
    rows: list[dict[str, object]],
    *,
    candidate_venue: str | None = None,
    candidate_year: str | None = None,
    candidate_url: str | None = None,
    candidate_pmcid: str | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    doi_groups: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        doi_norm = _normalize_conflict_value('doi', row.get('doi'))
        if not doi_norm:
            continue
        doi_groups.setdefault(doi_norm, []).append(row)

    consensus_doi = None
    consensus_supporters: list[str] = []
    for doi_norm, supporters in doi_groups.items():
        non_pubmed_supporters = [
            row for row in supporters
            if row.get('source_name') != 'pubmed' and row.get('matched')
        ]
        supporter_names = sorted({str(row.get('source_name')) for row in non_pubmed_supporters})
        if len(supporter_names) >= 2:
            consensus_doi = doi_norm
            consensus_supporters = supporter_names
            break

    crossref_consensus_row = None
    if not consensus_doi:
        crossref_rows = [
            row for row in rows
            if row.get('source_name') == 'crossref' and row.get('matched') and _normalize_conflict_value('doi', row.get('doi'))
        ]
        if len(crossref_rows) == 1:
            row = crossref_rows[0]
            if (
                (_is_non_ncbi_candidate_url(candidate_url) or bool(_normalize_conflict_value('pmcid', candidate_pmcid)))
                and _venue_rough_match(candidate_venue, row.get('venue'))
                and (not candidate_year or not row.get('year') or str(candidate_year) == str(row.get('year')))
            ):
                consensus_doi = _normalize_conflict_value('doi', row.get('doi'))
                consensus_supporters = ['crossref', 'candidate_url', 'candidate_venue']
                crossref_consensus_row = row

    if not consensus_doi:
        return rows, []

    suppressed: list[dict[str, object]] = []
    adjusted_rows: list[dict[str, object]] = []
    for row in rows:
        source_name = row.get('source_name')
        query_type = row.get('query_type')
        doi_norm = _normalize_conflict_value('doi', row.get('doi'))
        pubmed_pmcid = _normalize_conflict_value('pmcid', row.get('pmcid'))
        candidate_pmcid_norm = _normalize_conflict_value('pmcid', candidate_pmcid)
        pmcid_conflict = bool(candidate_pmcid_norm and pubmed_pmcid and candidate_pmcid_norm != pubmed_pmcid)
        if source_name == 'pubmed' and query_type == 'title' and doi_norm and doi_norm != consensus_doi:
            suppression_reason = 'pubmed_title_doi_conflicts_with_consensus'
            if pmcid_conflict:
                suppression_reason = 'pubmed_title_doi_conflicts_with_candidate_pmcid'
            elif crossref_consensus_row is not None:
                suppression_reason = 'pubmed_title_doi_conflicts_with_crossref_plus_candidate_url'
            new_row = dict(row)
            suppressed.append(
                {
                    'source_name': source_name,
                    'query_type': query_type,
                    'suppressed_field': 'doi',
                    'suppressed_value': row.get('doi'),
                    'kept_pmid': row.get('pmid'),
                    'kept_pmcid': row.get('pmcid'),
                    'consensus_doi': consensus_doi,
                    'consensus_supporters': consensus_supporters,
                    'suppression_reason': suppression_reason,
                    'candidate_pmcid': candidate_pmcid,
                    'candidate_url': candidate_url,
                }
            )
            new_row['doi'] = None
            adjusted_rows.append(new_row)
        else:
            adjusted_rows.append(row)
    return adjusted_rows, suppressed


def _build_conflict_assessment(rows, fields: list[str], *, suppressed_signals: list[dict[str, object]] | None = None) -> dict:
    raw_conflicts: dict[str, list[str]] = {}
    graded_conflicts: dict[str, dict[str, object]] = {}

    for field in fields:
        normalized_map: dict[str | None, set[str]] = {}
        for row in rows:
            raw = row[field]
            if not raw:
                continue
            key = _normalize_conflict_value(field, raw)
            normalized_map.setdefault(key, set()).add(_field_clean_text(field, raw) or str(raw))
        normalized_map = {k: v for k, v in normalized_map.items() if k is not None}
        if len(normalized_map) <= 1:
            continue
        values = sorted({item for group in normalized_map.values() for item in group})
        grade = _grade_conflict(field, values)
        raw_conflicts[field] = values
        graded_conflicts[field] = {'grade': grade, 'values': values}

    if not graded_conflicts:
        return {}

    severe_conflict_fields = sorted([field for field, info in graded_conflicts.items() if info['grade'] == 'C'])
    canonical_blocked = any(field in BLOCKING_GRADE_C_FIELDS for field in severe_conflict_fields)
    if not canonical_blocked and len(severe_conflict_fields) >= 2:
        canonical_blocked = True
    if not canonical_blocked and 'year' in severe_conflict_fields and len(severe_conflict_fields) >= 1:
        canonical_blocked = True

    if severe_conflict_fields:
        conflict_grade_max = 'C'
    elif any(info['grade'] == 'B' for info in graded_conflicts.values()):
        conflict_grade_max = 'B'
    else:
        conflict_grade_max = 'A'

    return {
        'raw_conflicts': raw_conflicts,
        'graded_conflicts': graded_conflicts,
        'conflict_grade_max': conflict_grade_max,
        'severe_conflict_fields': severe_conflict_fields,
        'canonical_blocked': canonical_blocked,
        'canonical_block_reason': (
            'severe_conflict:' + ','.join(severe_conflict_fields)
            if canonical_blocked and severe_conflict_fields
            else None
        ),
        'suppressed_signals': suppressed_signals or [],
    }


def _merge_confidence(conflict_assessment: dict) -> float:
    if not conflict_assessment:
        return 0.9
    grade = conflict_assessment.get('conflict_grade_max')
    blocked = bool(conflict_assessment.get('canonical_blocked'))
    if grade == 'A':
        return 0.8
    if grade == 'B':
        return 0.65
    if blocked:
        return 0.25
    return 0.45


def _pick_preferred(rows, field: str):
    candidates = []
    for r in rows:
        value = r[field]
        if not value:
            continue
        score = SOURCE_PRIORITY.get(r['source_name'], 0)
        if field in {'doi', 'pmid', 'pmcid'}:
            if r.get('query_type') in {'doi', 'doi_batch', 'pmid'}:
                score += 3
            elif r.get('query_type') == 'title':
                score -= 1
        candidates.append((score, value, r['source_name'], r.get('query_type')))
    if not candidates:
        return None, []
    candidates.sort(key=lambda x: (-x[0], x[2], x[3] or ''))
    return candidates[0][1], [f"{src}[{qtype}]:{val}" for _, val, src, qtype in candidates]


def build_merged_metadata(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'merge_metadata_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='merge_metadata', requested_limit=limit, notes=None)
        rows = conn.execute(
            """
            SELECT pcn.candidate_id
            FROM paper_candidate_normalized pcn
            LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id
            WHERE mmp.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        candidate_ids = [r[0] for r in rows]
        logger.info('Found %s candidate(s) without merged proposal', len(candidate_ids))
        for candidate_id in candidate_ids:
            src_rows = conn.execute(
                """
                SELECT source_name, query_type, title, authors_json, abstract, venue, year,
                       publication_type, doi, pmid, pmcid, url, matched
                FROM source_record
                WHERE candidate_id = ? AND matched = 1
                """,
                (candidate_id,),
            ).fetchall()
            if not src_rows:
                tracker.record_stage_cost(conn, stage='merge_metadata', status='no_sources', candidate_id=candidate_id)
                continue

            fallback_row = conn.execute(
                '''
                SELECT norm_title, norm_authors_json, venue_guess, year_guess, doi_extracted, pmid_extracted,
                       pmcid_extracted, url_canonical
                FROM paper_candidate_normalized
                WHERE candidate_id = ?
                ''',
                (candidate_id,),
            ).fetchone()
            dict_rows = [
                {
                    'source_name': r[0], 'query_type': r[1], 'title': r[2], 'authors_json': r[3], 'abstract': r[4],
                    'venue': r[5], 'year': r[6], 'publication_type': r[7], 'doi': r[8],
                    'pmid': r[9], 'pmcid': r[10], 'url': r[11], 'matched': r[12]
                }
                for r in src_rows
            ]
            if fallback_row:
                (
                    norm_title, norm_authors_json, norm_venue_guess, norm_year_guess,
                    norm_doi, norm_pmid, norm_pmcid, norm_url,
                ) = fallback_row
            else:
                norm_title = norm_authors_json = norm_venue_guess = norm_year_guess = norm_doi = norm_pmid = norm_pmcid = norm_url = None

            adjusted_rows, suppressed_signals = _apply_pubmed_doi_suppression(
                dict_rows,
                candidate_venue=norm_venue_guess,
                candidate_year=norm_year_guess,
                candidate_url=norm_url,
                candidate_pmcid=norm_pmcid,
            )
            preferred_title, title_trace = _pick_preferred(adjusted_rows, 'title')
            preferred_authors_json, authors_trace = _pick_preferred(adjusted_rows, 'authors_json')
            preferred_abstract, abstract_trace = _pick_preferred(adjusted_rows, 'abstract')
            preferred_venue, venue_trace = _pick_preferred(adjusted_rows, 'venue')
            preferred_year, year_trace = _pick_preferred(adjusted_rows, 'year')
            preferred_doi, doi_trace = _pick_preferred(adjusted_rows, 'doi')
            preferred_pmid, pmid_trace = _pick_preferred(adjusted_rows, 'pmid')
            preferred_publication_type, type_trace = _pick_preferred(adjusted_rows, 'publication_type')

            conflict_assessment = _build_conflict_assessment(adjusted_rows, ['title', 'venue', 'year', 'doi', 'pmid'], suppressed_signals=suppressed_signals)

            conn.execute(
                """
                INSERT INTO merged_metadata_proposal (
                    candidate_id, preferred_title, preferred_authors_json,
                    preferred_abstract, preferred_venue, preferred_year,
                    preferred_doi, preferred_pmid, preferred_publication_type,
                    version_status, source_priority_trace, conflict_flags_json,
                    merge_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    clean_title(preferred_title or norm_title),
                    preferred_authors_json or norm_authors_json,
                    clean_abstract(preferred_abstract),
                    clean_venue(preferred_venue or norm_venue_guess),
                    preferred_year or norm_year_guess,
                    preferred_doi or norm_doi,
                    preferred_pmid or norm_pmid,
                    preferred_publication_type,
                    'unknown',
                    json.dumps({
                        'title': title_trace,
                        'authors': authors_trace,
                        'abstract': abstract_trace,
                        'venue': venue_trace,
                        'year': year_trace,
                        'doi': doi_trace,
                        'pmid': pmid_trace,
                        'type': type_trace,
                        'suppressed_signals': suppressed_signals,
                    }, ensure_ascii=False),
                    json.dumps(conflict_assessment, ensure_ascii=False) if conflict_assessment else '{}',
                    _merge_confidence(conflict_assessment),
                ),
            )
            tracker.record_stage_cost(
                conn,
                stage='merge_metadata',
                status='blocked' if conflict_assessment.get('canonical_blocked') else 'ok',
                candidate_id=candidate_id,
                notes=json.dumps(conflict_assessment, ensure_ascii=False) if conflict_assessment else None,
            )
        repo.finish_batch_run(conn, run_id=run_id, duration_ms=int((time.perf_counter()-started_at)*1000), processed_count=len(candidate_ids), status='ok')
        conn.commit()
