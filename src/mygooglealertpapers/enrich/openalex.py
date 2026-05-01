from __future__ import annotations

import json
import urllib.parse

from mygooglealertpapers.enrich.base import (
    EnrichmentRecord,
    accept_result,
    first_author_matches,
    title_similarity,
    venue_hint_matches,
)
from mygooglealertpapers.enrich.http_client import request_json


def _extract_primary_location_fields(item: dict) -> tuple[str | None, str | None]:
    primary_location = item.get('primary_location') or {}
    source = primary_location.get('source') or {}
    venue = source.get('display_name')
    url = primary_location.get('landing_page_url')
    return venue, url


def _pick_openalex_title_item(
    query_title: str,
    results: list[dict],
    *,
    doi: str | None = None,
    first_author_family: str | None = None,
    venue_hint: str | None = None,
    query_year: str | None = None,
) -> dict | None:
    if not results:
        return None

    accepted: list[tuple[tuple[float, int, int, int, int], dict]] = []
    for idx, item in enumerate(results):
        authors = [
            a.get('author', {}).get('display_name')
            for a in item.get('authorships', [])
            if a.get('author', {}).get('display_name')
        ]
        venue, _ = _extract_primary_location_fields(item)
        ids = item.get('ids') or {}
        provider_doi = (ids.get('doi') or '').replace('https://doi.org/', '') or None
        result_year = str(item.get('publication_year')) if item.get('publication_year') else None
        result_title = item.get('display_name')
        matched_ok = accept_result(
            query_title,
            result_title,
            query_year,
            result_year,
            first_author_family,
            json.dumps(authors, ensure_ascii=False),
            venue_hint,
            venue,
            candidate_doi=doi,
            provider_doi=provider_doi,
            provider_name='openalex',
        )
        if not matched_ok:
            continue
        sim = title_similarity(query_title, result_title)
        fam_match = first_author_matches(first_author_family, json.dumps(authors, ensure_ascii=False))
        venue_match = venue_hint_matches(venue_hint, venue)
        score = (
            sim,
            1 if provider_doi else 0,
            1 if (query_year and result_year and query_year == result_year) else 0,
            1 if venue_match is True else 0,
            1 if fam_match is True else 0,
        )
        accepted.append((score, item))

    if accepted:
        accepted.sort(key=lambda entry: entry[0], reverse=True)
        return accepted[0][1]
    return results[0]


def build_openalex_record(
    candidate_id: str,
    *,
    query_type: str,
    query_string: str,
    doi: str | None,
    item: dict | None,
    raw_payload_json: str,
    latency_ms: int,
    first_author_family: str | None = None,
    venue_hint: str | None = None,
    query_year: str | None = None,
) -> EnrichmentRecord:
    if not item:
        return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, raw_payload_json, latency_ms)
    authors = [a.get('author', {}).get('display_name') for a in item.get('authorships', []) if a.get('author', {}).get('display_name')]
    venue, url = _extract_primary_location_fields(item)
    ids = item.get('ids') or {}
    provider_doi = (ids.get('doi') or '').replace('https://doi.org/', '') or None
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, item.get('display_name'), query_year, str(item.get('publication_year')) if item.get('publication_year') else None, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=doi, provider_doi=provider_doi, provider_name='openalex')
    return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, matched_ok, 1.0 if query_type == 'doi' else None, item.get('id'), item.get('display_name'), json.dumps(authors, ensure_ascii=False), item.get('abstract_inverted_index') and json.dumps(item.get('abstract_inverted_index')), venue, str(item.get('publication_year')) if item.get('publication_year') else None, item.get('type'), provider_doi, (ids.get('pmid') or '').replace('https://pubmed.ncbi.nlm.nih.gov/', '').strip('/') or None, (ids.get('pmcid') or '').replace('https://www.ncbi.nlm.nih.gov/pmc/articles/', '').strip('/') or None, url, raw_payload_json, latency_ms)


def fetch_openalex_title_item(
    title: str,
    *,
    email: str | None = None,
    per_page: int = 1,
    doi: str | None = None,
    first_author_family: str | None = None,
    venue_hint: str | None = None,
    query_year: str | None = None,
    pick_best_accepted: bool = False,
) -> tuple[dict | None, str, int]:
    page_size = max(1, min(int(per_page or 1), 25))
    url = f"https://api.openalex.org/works?search={urllib.parse.quote(title)}&per-page={page_size}"
    if email:
        url += f"&email={urllib.parse.quote(email)}"
    response = request_json('openalex', url, contact_email=email)
    if not response.ok:
        return None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms
    payload = response.json_data if isinstance(response.json_data, dict) else {}
    results = payload.get('results', [])
    item = (
        _pick_openalex_title_item(
            title,
            results,
            doi=doi,
            first_author_family=first_author_family,
            venue_hint=venue_hint,
            query_year=query_year,
        )
        if pick_best_accepted else (results[0] if results else None)
    )
    raw_payload_json = json.dumps(payload if page_size > 1 else (item if item else payload), ensure_ascii=False)
    return item, raw_payload_json, response.latency_ms


def query_openalex(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, email: str | None = None, title_per_page: int = 1, title_pick_best_accepted: bool = False) -> EnrichmentRecord | None:
    if doi:
        url = f"https://api.openalex.org/works?filter=doi:{urllib.parse.quote('https://doi.org/' + doi)}&per-page=1"
        if email:
            url += f"&email={urllib.parse.quote(email)}"
        response = request_json('openalex', url, contact_email=email)
        if not response.ok:
            return EnrichmentRecord(candidate_id, 'openalex', 'doi', doi, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms)
        payload = response.json_data if isinstance(response.json_data, dict) else {}
        results = payload.get('results', [])
        item = results[0] if results else None
        return build_openalex_record(candidate_id, query_type='doi', query_string=doi, doi=doi, item=item, raw_payload_json=json.dumps(item if item else payload, ensure_ascii=False), latency_ms=response.latency_ms)
    if title:
        item, raw_payload_json, latency_ms = fetch_openalex_title_item(
            title,
            email=email,
            per_page=title_per_page,
            doi=doi,
            first_author_family=first_author_family,
            venue_hint=venue_hint,
            query_year=query_year,
            pick_best_accepted=title_pick_best_accepted,
        )
        return build_openalex_record(candidate_id, query_type='title', query_string=title, doi=doi, item=item, raw_payload_json=raw_payload_json, latency_ms=latency_ms, first_author_family=first_author_family, venue_hint=venue_hint, query_year=query_year)
    return None


def query_openalex_batch_by_doi(dois: list[str], *, email: str | None = None):
    normalized = []
    for doi in dois:
        if not doi:
            continue
        value = doi if doi.startswith('https://doi.org/') else 'https://doi.org/' + doi
        normalized.append(value)
    if not normalized:
        return []
    joined = '|'.join(urllib.parse.quote(value, safe=':/') for value in normalized[:50])
    url = f"https://api.openalex.org/works?filter=doi:{joined}&per-page=100"
    if email:
        url += f"&email={urllib.parse.quote(email)}"
    response = request_json('openalex', url, timeout=30, contact_email=email)
    if not response.ok:
        raise RuntimeError(json.dumps(response.to_error_payload(), ensure_ascii=False))
    payload = response.json_data if isinstance(response.json_data, dict) else {}
    return payload.get('results', [])
