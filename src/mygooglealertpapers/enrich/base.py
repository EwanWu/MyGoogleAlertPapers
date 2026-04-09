from __future__ import annotations

from dataclasses import dataclass
import json


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


import re
from difflib import SequenceMatcher


def normalize_compare_title(title: str | None) -> str:
    if not title:
        return ''
    text = title.casefold()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def title_similarity(a: str | None, b: str | None) -> float:
    aa = normalize_compare_title(a)
    bb = normalize_compare_title(b)
    if not aa or not bb:
        return 0.0
    return SequenceMatcher(None, aa, bb).ratio()


def accept_title_match(query_title: str | None, result_title: str | None, query_year: str | None = None, result_year: str | None = None) -> bool:
    sim = title_similarity(query_title, result_title)
    if sim >= 0.97:
        return True
    if sim < 0.84:
        return False
    if query_year and result_year and query_year != result_year:
        return False
    return sim >= 0.90


def first_author_matches(expected_family: str | None, authors_json: str | None) -> bool | None:
    if not expected_family:
        return None
    if not authors_json:
        return None
    try:
        authors = json.loads(authors_json)
    except Exception:
        return None
    if not authors:
        return None
    first = str(authors[0]).strip().casefold()
    fam = expected_family.strip().casefold()
    return fam in first or first.endswith(fam)


def venue_hint_matches(venue_hint: str | None, provider_venue: str | None) -> bool | None:
    if not venue_hint or not provider_venue:
        return None
    a = normalize_compare_title(venue_hint)
    b = normalize_compare_title(provider_venue)
    if not a or not b:
        return None
    if a in b or b in a:
        return True
    return title_similarity(a, b) >= 0.8


def _normalized_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    if text.startswith('https://doi.org/'):
        text = text[len('https://doi.org/'):]
    return text or None


def provider_payload_has_error(raw_payload_json: str | None) -> bool:
    if not raw_payload_json:
        return False
    try:
        payload = json.loads(raw_payload_json)
    except Exception:
        return False
    if isinstance(payload, dict) and payload.get('error'):
        return True
    return False


def accept_result(query_title: str | None, result_title: str | None, query_year: str | None = None, result_year: str | None = None, expected_family: str | None = None, authors_json: str | None = None, venue_hint: str | None = None, provider_venue: str | None = None, candidate_doi: str | None = None, provider_doi: str | None = None, provider_name: str | None = None) -> bool:
    sim = title_similarity(query_title, result_title)
    candidate_doi_norm = _normalized_doi(candidate_doi)
    provider_doi_norm = _normalized_doi(provider_doi)
    if candidate_doi_norm and provider_doi_norm and candidate_doi_norm != provider_doi_norm:
        return False
    if not accept_title_match(query_title, result_title, query_year, result_year):
        return False
    fam_match = first_author_matches(expected_family, authors_json)
    venue_match = venue_hint_matches(venue_hint, provider_venue)
    if fam_match is False:
        return False
    if venue_match is False:
        return False
    if provider_name == 'pubmed':
        if sim < 0.96 and fam_match is not True:
            return False
        if candidate_doi_norm and provider_doi_norm and candidate_doi_norm != provider_doi_norm:
            return False
    if sim < 0.93:
        if fam_match is not True:
            return False
        if venue_match is not True and query_year and result_year:
            return False
    if query_year and result_year and query_year != result_year and sim < 0.97:
        return False
    return True


from dataclasses import asdict


def enrichment_record_to_json(rec: EnrichmentRecord) -> str:
    return json.dumps(asdict(rec), ensure_ascii=False)


def enrichment_record_from_json(payload: str) -> EnrichmentRecord:
    data = json.loads(payload)
    return EnrichmentRecord(**data)
