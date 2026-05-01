from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
import uuid
from difflib import SequenceMatcher
from urllib.parse import urlparse

from mygooglealertpapers.config import Settings
from mygooglealertpapers.normalize.text import clean_abstract, clean_text, clean_title, clean_venue, comparison_text
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.pipeline.candidate_resolution import _candidate_exact_keys, cluster_candidates_within_batch

logger = logging.getLogger(__name__)

SOURCE_PRIORITY = {
    'crossref': 4,
    'openalex': 3,
    'semanticscholar': 2,
    'pubmed': 1,
    # unpaywall is not a bibliographic authority; it only provides OA status/URL.
    # Set to 0 so it never overrides Crossref/OpenAlex/SemanticScholar/PubMed
    # for title, authors, year, venue, or DOI decisions.
    'unpaywall': 0,
}

PUBMED_FALLBACK_FIELDS = {'abstract', 'pmid', 'pmcid'}

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
AUTHOR_FOOTNOTE_BLOB_RE = re.compile(r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}|[A-Z]{1,4}(?:\s+[A-Z][a-z]+){0,2})\s+\d+\b')
AUTHOR_CREDENTIAL_RE = re.compile(r'\b(?:phd|msc|md|fmed\s*sci|mbbs|bsc|frcp|mph)\b', re.IGNORECASE)
NON_ENGLISH_SCRIPT_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]')

TITLE_LANE_REASON_NO_IDENTIFIER = 'no_identifier_available'
TITLE_LANE_REASON_IDENTIFIER_GAP = 'identifier_present_but_not_sufficient_for_provider_path'
TITLE_LANE_REASON_CLUSTER_LEADER = 'cluster_leader_path'
TITLE_LANE_SUBREASON_PMID_ONLY = 'pmid_without_doi'
TITLE_LANE_SUBREASON_PMCID_ONLY = 'pmcid_only'
TITLE_LANE_SUBREASON_URL_ONLY = 'url_canonical_only'
TITLE_LANE_SUBREASON_SCHOLAR_ONLY = 'scholar_cluster_only'
TITLE_LANE_SUBREASON_ARXIV_ONLY = 'arxiv_only'
TITLE_LANE_SUBREASON_MIXED_NON_DOI = 'mixed_non_doi_identifier'


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


def _looks_non_english_title(title: str | None) -> bool:
    text = clean_title(title) or ''
    if not text:
        return False
    if NON_ENGLISH_SCRIPT_RE.search(text):
        return True
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    latin_letters = 0
    for ch in letters:
        if 'LATIN' in unicodedata.name(ch, ''):
            latin_letters += 1
    return latin_letters == 0


def _looks_like_author_footnote_blob(title: str | None) -> bool:
    text = clean_title(title) or ''
    if not text:
        return False
    matches = AUTHOR_FOOTNOTE_BLOB_RE.findall(text)
    return len(matches) >= 3


def _has_author_tail_pollution(title: str | None) -> bool:
    text = clean_title(title) or ''
    if not text:
        return False
    if AUTHOR_CREDENTIAL_RE.search(text):
        return True
    parts = [part.strip() for part in text.split(',') if part.strip()]
    if len(parts) < 2:
        return False
    tail = ', '.join(parts[-2:])
    titlecase_words = re.findall(r'\b[A-Z][a-z]+\b', tail)
    if len(titlecase_words) >= 3 and len(parts) >= 3:
        return True
    return False


def _strip_author_tail_pollution(title: str | None) -> str | None:
    text = clean_title(title) or ''
    if not text or not _has_author_tail_pollution(text):
        return None
    original = text

    credential_match = AUTHOR_CREDENTIAL_RE.search(text)
    if credential_match:
        text = text[:credential_match.start()].rstrip(' ,;')

    text = re.sub(r'(?:,\s*[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+){0,2})+$', '', text).rstrip(' ,;')

    tokens = text.split()
    trailing_name_tokens = 0
    while tokens:
        token = tokens[-1].strip(',.')
        if re.fullmatch(r'[A-Z][a-z]+', token) or re.fullmatch(r'[A-Z]\.?', token):
            tokens.pop()
            trailing_name_tokens += 1
            continue
        break
    if trailing_name_tokens >= 2:
        text = ' '.join(tokens).rstrip(' ,;')

    text = clean_title(text) or ''
    return text if text and text != original else None


def _best_source_title_match(candidate_title: str | None, rows: list[dict[str, object]]) -> tuple[float, dict[str, object] | None]:
    candidate = _comparison_text(candidate_title)
    if not candidate:
        return 0.0, None
    best = 0.0
    best_row = None
    for row in rows:
        title = _comparison_text(row.get('title'))
        if not title:
            continue
        score = SequenceMatcher(None, candidate, title).ratio()
        if score > best:
            best = score
            best_row = row
    return best, best_row


def _max_source_title_similarity(candidate_title: str | None, rows: list[dict[str, object]]) -> float:
    best, _ = _best_source_title_match(candidate_title, rows)
    return best


def _salvage_author_tail_pollution(
    settings: Settings,
    *,
    norm_title: str | None,
    unmatched_rows: list[dict[str, object]],
) -> dict[str, object] | None:
    threshold = settings.policy_profile.merge_value('fallback_author_pollution_salvage_similarity_threshold', None)
    if threshold is None:
        return None

    cleaned_title = _strip_author_tail_pollution(norm_title)
    if not cleaned_title:
        return None

    raw_similarity, _ = _best_source_title_match(norm_title, unmatched_rows)
    cleaned_similarity, best_row = _best_source_title_match(cleaned_title, unmatched_rows)
    if not best_row:
        return None

    has_supporting_identifier = bool(best_row.get('doi') or best_row.get('pmid') or best_row.get('pmcid'))
    if cleaned_similarity < float(threshold):
        return None
    if cleaned_similarity < raw_similarity + 0.05:
        return None
    if not has_supporting_identifier:
        return None

    return {
        'cleaned_title': cleaned_title,
        'raw_title_similarity': round(raw_similarity, 3),
        'cleaned_title_similarity': round(cleaned_similarity, 3),
        'matched_source_name': best_row.get('source_name'),
        'matched_source_title': best_row.get('title'),
        'matched_source_has_identifier': has_supporting_identifier,
    }


def _identifier_gap_subreason_for_exact_keys(exact_keys: dict[str, str]) -> str | None:
    non_doi_keys = {key for key in exact_keys if key != 'doi'}
    if not non_doi_keys:
        return None
    if len(non_doi_keys) > 1:
        return TITLE_LANE_SUBREASON_MIXED_NON_DOI
    only_key = next(iter(non_doi_keys))
    if only_key == 'pmid':
        return TITLE_LANE_SUBREASON_PMID_ONLY
    if only_key == 'pmcid':
        return TITLE_LANE_SUBREASON_PMCID_ONLY
    if only_key == 'url_canonical':
        return TITLE_LANE_SUBREASON_URL_ONLY
    if only_key == 'scholar_cluster':
        return TITLE_LANE_SUBREASON_SCHOLAR_ONLY
    if only_key == 'arxiv':
        return TITLE_LANE_SUBREASON_ARXIV_ONLY
    return TITLE_LANE_SUBREASON_MIXED_NON_DOI


def _latest_unmatched_source_row(
    unmatched_rows: list[dict[str, object]],
    *,
    source_name: str,
    query_type: str,
) -> dict[str, object] | None:
    for row in reversed(unmatched_rows):
        if row.get('source_name') == source_name and row.get('query_type') == query_type:
            return row
    return None


def _post_openalex_title_status_from_unmatched_rows(unmatched_rows: list[dict[str, object]]) -> str | None:
    row = _latest_unmatched_source_row(unmatched_rows, source_name='openalex', query_type='title')
    if row is None:
        return None
    if int(row.get('matched') or 0) != 1:
        return 'openalex_title_unmatched'
    if not row.get('doi'):
        return 'openalex_title_match_without_doi'
    return 'openalex_prior_doi_title_match'


def _normalized_fallback_context(
    *,
    candidate_id: str,
    normalized_row,
    unmatched_rows: list[dict[str, object]],
    leader_to_followers: dict[str, list[str]],
    follower_to_leader: dict[str, str],
) -> dict[str, object]:
    exact_keys = _candidate_exact_keys(normalized_row) if normalized_row is not None else {}
    is_cluster_leader = bool(leader_to_followers.get(candidate_id))
    is_cluster_follower = candidate_id in follower_to_leader
    if is_cluster_leader or is_cluster_follower:
        title_lane_reason = TITLE_LANE_REASON_CLUSTER_LEADER
        title_lane_subreason = None
    elif exact_keys:
        title_lane_reason = TITLE_LANE_REASON_IDENTIFIER_GAP
        title_lane_subreason = _identifier_gap_subreason_for_exact_keys(exact_keys)
    else:
        title_lane_reason = TITLE_LANE_REASON_NO_IDENTIFIER
        title_lane_subreason = None

    arxiv_id = None
    if normalized_row is not None and hasattr(normalized_row, 'keys') and 'arxiv_id_extracted' in normalized_row.keys():
        arxiv_id = normalized_row['arxiv_id_extracted']
    post_openalex_status = _post_openalex_title_status_from_unmatched_rows(unmatched_rows)
    crossref_title_row = _latest_unmatched_source_row(unmatched_rows, source_name='crossref', query_type='title')

    targeted_post_openalex_url_only_non_arxiv = bool(
        title_lane_reason == TITLE_LANE_REASON_IDENTIFIER_GAP
        and title_lane_subreason == TITLE_LANE_SUBREASON_URL_ONLY
        and not arxiv_id
        and post_openalex_status == 'openalex_title_unmatched'
        and crossref_title_row is not None
        and not is_cluster_leader
        and not is_cluster_follower
    )

    return {
        'candidate_id': candidate_id,
        'exact_keys': exact_keys,
        'title_lane_reason': title_lane_reason,
        'title_lane_subreason': title_lane_subreason,
        'post_openalex_status': post_openalex_status,
        'is_cluster_leader': is_cluster_leader,
        'is_cluster_follower': is_cluster_follower,
        'has_crossref_title_attempt': crossref_title_row is not None,
        'has_arxiv_id': bool(arxiv_id),
        'targeted_post_openalex_url_only_non_arxiv': targeted_post_openalex_url_only_non_arxiv,
    }


def _normalized_fallback_guardrail(
    settings: Settings,
    *,
    norm_title: str | None,
    norm_authors_json: str | None,
    norm_venue_guess: str | None,
    norm_year_guess: str | None,
    norm_doi: str | None,
    norm_pmid: str | None,
    norm_pmcid: str | None,
    unmatched_rows: list[dict[str, object]],
    fallback_context: dict[str, object] | None = None,
) -> dict[str, object]:
    has_identifier = bool(norm_doi or norm_pmid or norm_pmcid)
    max_title_similarity = _max_source_title_similarity(norm_title, unmatched_rows)
    review_similarity_threshold = settings.policy_profile.merge_value('fallback_review_similarity_threshold', None)
    sparse_similarity_threshold = settings.policy_profile.merge_value('fallback_review_sparse_metadata_similarity_threshold', None)
    targeted_reject_similarity_threshold = settings.policy_profile.merge_value(
        'fallback_reject_similarity_threshold_post_openalex_url_only_non_arxiv',
        None,
    )
    targeted_review_similarity_threshold = settings.policy_profile.merge_value(
        'fallback_review_similarity_threshold_post_openalex_url_only_non_arxiv',
        None,
    )
    reject_non_english_title = bool(settings.policy_profile.merge_value('fallback_reject_non_english_title', False))
    reject_author_blob = bool(settings.policy_profile.merge_value('fallback_reject_author_blob', False))
    reject_author_blob_identifier_aware = bool(settings.policy_profile.merge_value('fallback_reject_author_blob_identifier_aware', False))
    review_author_pollution = bool(settings.policy_profile.merge_value('fallback_review_author_pollution', False))
    has_authors = bool(clean_text(norm_authors_json))
    has_venue = bool(clean_venue(norm_venue_guess))
    has_year = bool(clean_text(norm_year_guess))

    reasons: list[str] = []
    decision = 'accept'
    author_pollution_salvage = None

    if reject_non_english_title and _looks_non_english_title(norm_title):
        decision = 'reject'
        reasons.append('title_not_english')
    elif reject_author_blob_identifier_aware and not has_identifier and _looks_like_author_footnote_blob(norm_title):
        decision = 'reject'
        reasons.append('title_looks_like_author_footnote_blob_identifier_aware')
    elif reject_author_blob and _looks_like_author_footnote_blob(norm_title):
        decision = 'reject'
        reasons.append('title_looks_like_author_footnote_blob')
    elif review_author_pollution and _has_author_tail_pollution(norm_title):
        author_pollution_salvage = _salvage_author_tail_pollution(
            settings,
            norm_title=norm_title,
            unmatched_rows=unmatched_rows,
        )
        if author_pollution_salvage:
            decision = 'accept'
            reasons.append('title_author_tail_pollution_salvaged')
        else:
            decision = 'review'
            reasons.append('title_has_author_tail_pollution')
    elif (
        targeted_reject_similarity_threshold is not None
        and not has_identifier
        and bool((fallback_context or {}).get('targeted_post_openalex_url_only_non_arxiv'))
        and max_title_similarity <= float(targeted_reject_similarity_threshold)
    ):
        decision = 'reject'
        reasons.append('targeted_post_openalex_url_only_non_arxiv_very_low_source_title_similarity')
    elif (
        targeted_review_similarity_threshold is not None
        and not has_identifier
        and bool((fallback_context or {}).get('targeted_post_openalex_url_only_non_arxiv'))
        and max_title_similarity <= float(targeted_review_similarity_threshold)
    ):
        decision = 'review'
        reasons.append('targeted_post_openalex_url_only_non_arxiv_low_source_title_similarity')
    elif review_similarity_threshold is not None and not has_identifier and max_title_similarity <= float(review_similarity_threshold):
        decision = 'review'
        reasons.append('low_source_title_similarity')
    elif (
        sparse_similarity_threshold is not None
        and not has_identifier
        and not has_authors
        and not has_venue
        and not has_year
        and max_title_similarity < float(sparse_similarity_threshold)
    ):
        decision = 'review'
        reasons.append('sparse_metadata_low_source_title_similarity')

    return {
        'decision': decision,
        'reasons': reasons,
        'has_identifier': has_identifier,
        'max_source_title_similarity': round(max_title_similarity, 3),
        'review_similarity_threshold': review_similarity_threshold,
        'sparse_similarity_threshold': sparse_similarity_threshold,
        'targeted_reject_similarity_threshold': targeted_reject_similarity_threshold,
        'targeted_review_similarity_threshold': targeted_review_similarity_threshold,
        'reject_non_english_title': reject_non_english_title,
        'unmatched_source_count': len(unmatched_rows),
        'has_authors': has_authors,
        'has_venue': has_venue,
        'has_year': has_year,
        'normalized_title_override': author_pollution_salvage.get('cleaned_title') if author_pollution_salvage else None,
        'author_pollution_salvage': author_pollution_salvage,
        'fallback_context': fallback_context or {},
    }


def _pick_preferred(rows, field: str, *, pubmed_fallback_only_for_core_fields: bool = True):
    candidates = []
    trace_candidates = []
    for r in rows:
        value = r[field]
        if not value:
            continue
        source_name = r['source_name']
        query_type = r.get('query_type')
        trace_candidates.append((value, source_name, query_type))
        if pubmed_fallback_only_for_core_fields and source_name == 'pubmed' and field not in PUBMED_FALLBACK_FIELDS:
            continue
        score = SOURCE_PRIORITY.get(source_name, 0)
        if field in {'doi', 'pmid', 'pmcid'}:
            if query_type in {'doi', 'doi_batch', 'pmid'}:
                score += 3
            elif query_type == 'title':
                score -= 1
        candidates.append((score, value, source_name, query_type))
    if not candidates:
        return None, [f"{src}[{qtype}]:{val}" for val, src, qtype in trace_candidates]
    candidates.sort(key=lambda x: (-x[0], x[2], x[3] or ''))
    return candidates[0][1], [f"{src}[{qtype}]:{val}" for _, val, src, qtype in candidates]


def build_merged_metadata(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    normalized_only_fallback = bool(settings.policy_profile.merge_value('normalized_only_fallback', False))
    pubmed_title_doi_suppression_enabled = bool(settings.policy_profile.merge_value('pubmed_title_doi_suppression', True))
    pubmed_fallback_only_for_core_fields = bool(settings.policy_profile.provider_value('pubmed', 'fallback_only_for_core_fields', True))
    run_id = 'merge_metadata_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='merge_metadata', requested_limit=limit, notes=None)
        normalized_rows = conn.execute(
            '''
            SELECT candidate_id, norm_title, doi_extracted, pmid_extracted, pmcid_extracted,
                   arxiv_id_extracted, url_canonical, scholar_cluster_hint
            FROM paper_candidate_normalized
            ORDER BY id ASC
            '''
        ).fetchall()
        normalized_row_by_candidate = {row[0]: row for row in normalized_rows}
        cluster_summary = cluster_candidates_within_batch(settings, repo, conn, normalized_rows)
        leader_to_followers = dict(cluster_summary.get('leader_to_followers') or {})
        follower_to_leader = dict(cluster_summary.get('follower_to_leader') or {})
        rows = conn.execute(
            """
            SELECT pcn.candidate_id
            FROM paper_candidate_normalized pcn
            LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id
            LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id
            WHERE mmp.id IS NULL AND cpl.id IS NULL
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

            if not src_rows:
                if not normalized_only_fallback or not fallback_row:
                    tracker.record_stage_cost(conn, stage='merge_metadata', status='no_sources', candidate_id=candidate_id)
                    continue
                unmatched_source_rows = [
                    {
                        'source_name': r[0], 'query_type': r[1], 'title': r[2], 'authors_json': r[3], 'abstract': r[4],
                        'venue': r[5], 'year': r[6], 'publication_type': r[7], 'doi': r[8],
                        'pmid': r[9], 'pmcid': r[10], 'url': r[11], 'matched': r[12]
                    }
                    for r in conn.execute(
                        """
                        SELECT source_name, query_type, title, authors_json, abstract, venue, year,
                               publication_type, doi, pmid, pmcid, url, matched
                        FROM source_record
                        WHERE candidate_id = ?
                        """,
                        (candidate_id,),
                    ).fetchall()
                ]
                fallback_context = _normalized_fallback_context(
                    candidate_id=candidate_id,
                    normalized_row=normalized_row_by_candidate.get(candidate_id),
                    unmatched_rows=unmatched_source_rows,
                    leader_to_followers=leader_to_followers,
                    follower_to_leader=follower_to_leader,
                )
                fallback_guardrail = _normalized_fallback_guardrail(
                    settings,
                    norm_title=norm_title,
                    norm_authors_json=norm_authors_json,
                    norm_venue_guess=norm_venue_guess,
                    norm_year_guess=norm_year_guess,
                    norm_doi=norm_doi,
                    norm_pmid=norm_pmid,
                    norm_pmcid=norm_pmcid,
                    unmatched_rows=unmatched_source_rows,
                    fallback_context=fallback_context,
                )
                if fallback_guardrail['decision'] == 'reject':
                    tracker.record_stage_cost(
                        conn,
                        stage='merge_metadata',
                        status='fallback_rejected',
                        candidate_id=candidate_id,
                        notes=json.dumps({'fallback_mode': 'normalized_only', 'guardrail': fallback_guardrail}, ensure_ascii=False),
                    )
                    continue
                preferred_title = fallback_guardrail.get('normalized_title_override') or norm_title
                preferred_authors_json = norm_authors_json
                preferred_abstract = None
                preferred_venue = norm_venue_guess
                preferred_year = norm_year_guess
                preferred_doi = norm_doi
                preferred_pmid = norm_pmid
                preferred_publication_type = None
                title_trace = [f'normalized[candidate]:{norm_title}'] if norm_title else []
                authors_trace = [f'normalized[candidate]:{norm_authors_json}'] if norm_authors_json else []
                abstract_trace = []
                venue_trace = [f'normalized[candidate]:{norm_venue_guess}'] if norm_venue_guess else []
                year_trace = [f'normalized[candidate]:{norm_year_guess}'] if norm_year_guess else []
                doi_trace = [f'normalized[candidate]:{norm_doi}'] if norm_doi else []
                pmid_trace = [f'normalized[candidate]:{norm_pmid}'] if norm_pmid else []
                type_trace = []
                suppressed_signals = []
                fallback_review = fallback_guardrail['decision'] == 'review'
                fallback_salvaged = bool(fallback_guardrail.get('author_pollution_salvage'))
                conflict_assessment = {
                    'raw_conflicts': {},
                    'graded_conflicts': {},
                    'conflict_grade_max': 'fallback_salvaged' if fallback_salvaged else ('fallback_review' if fallback_review else 'fallback_only'),
                    'severe_conflict_fields': [],
                    'canonical_blocked': fallback_review,
                    'canonical_block_reason': 'fallback_guardrail:' + ','.join(fallback_guardrail['reasons']) if fallback_review else None,
                    'suppressed_signals': [],
                    'fallback_mode': 'normalized_only',
                    'fallback_guardrail': fallback_guardrail,
                }
                merge_confidence = 0.2 if fallback_salvaged else (0.1 if fallback_review else 0.15)
                stage_status = 'fallback_salvaged' if fallback_salvaged else ('fallback_review' if fallback_review else 'fallback_only')
            else:
                adjusted_rows, suppressed_signals = (
                    _apply_pubmed_doi_suppression(
                        dict_rows,
                        candidate_venue=norm_venue_guess,
                        candidate_year=norm_year_guess,
                        candidate_url=norm_url,
                        candidate_pmcid=norm_pmcid,
                    )
                    if pubmed_title_doi_suppression_enabled
                    else (dict_rows, [])
                )
                preferred_title, title_trace = _pick_preferred(adjusted_rows, 'title', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_authors_json, authors_trace = _pick_preferred(adjusted_rows, 'authors_json', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_abstract, abstract_trace = _pick_preferred(adjusted_rows, 'abstract', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_venue, venue_trace = _pick_preferred(adjusted_rows, 'venue', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_year, year_trace = _pick_preferred(adjusted_rows, 'year', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_doi, doi_trace = _pick_preferred(adjusted_rows, 'doi', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_pmid, pmid_trace = _pick_preferred(adjusted_rows, 'pmid', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)
                preferred_publication_type, type_trace = _pick_preferred(adjusted_rows, 'publication_type', pubmed_fallback_only_for_core_fields=pubmed_fallback_only_for_core_fields)

                conflict_assessment = _build_conflict_assessment(adjusted_rows, ['title', 'venue', 'year', 'doi', 'pmid'], suppressed_signals=suppressed_signals)
                merge_confidence = _merge_confidence(conflict_assessment)
                stage_status = 'blocked' if conflict_assessment.get('canonical_blocked') else 'ok'

            conn.execute(
                """
                INSERT INTO merged_metadata_proposal (
                    candidate_id, preferred_title, preferred_authors_json,
                    preferred_abstract, preferred_venue, preferred_year,
                    preferred_doi, preferred_pmid, preferred_publication_type,
                    version_status, source_priority_trace, conflict_flags_json,
                    merge_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(candidate_id) DO UPDATE SET
                    preferred_title=excluded.preferred_title,
                    preferred_authors_json=excluded.preferred_authors_json,
                    preferred_abstract=excluded.preferred_abstract,
                    preferred_venue=excluded.preferred_venue,
                    preferred_year=excluded.preferred_year,
                    preferred_doi=excluded.preferred_doi,
                    preferred_pmid=excluded.preferred_pmid,
                    preferred_publication_type=excluded.preferred_publication_type,
                    version_status=excluded.version_status,
                    source_priority_trace=excluded.source_priority_trace,
                    conflict_flags_json=excluded.conflict_flags_json,
                    merge_confidence=excluded.merge_confidence,
                    created_at=CURRENT_TIMESTAMP
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
                        'fallback_mode': 'normalized_only' if stage_status in {'fallback_only', 'fallback_review'} else None,
                    }, ensure_ascii=False),
                    json.dumps(conflict_assessment, ensure_ascii=False) if conflict_assessment else '{}',
                    merge_confidence,
                ),
            )
            tracker.record_stage_cost(
                conn,
                stage='merge_metadata',
                status=stage_status,
                candidate_id=candidate_id,
                notes=json.dumps(conflict_assessment, ensure_ascii=False) if conflict_assessment else None,
            )
        repo.finish_batch_run(conn, run_id=run_id, duration_ms=int((time.perf_counter()-started_at)*1000), processed_count=len(candidate_ids), status='ok')
        conn.commit()
