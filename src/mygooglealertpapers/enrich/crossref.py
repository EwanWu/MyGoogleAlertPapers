from __future__ import annotations

import json
import urllib.parse

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result
from mygooglealertpapers.enrich.http_client import request_json


def _crossref_url(base: str, params: dict[str, object]) -> str:
    filtered = {key: value for key, value in params.items() if value not in (None, '')}
    if not filtered:
        return base
    return f"{base}?{urllib.parse.urlencode(filtered)}"


def _crossref_title_value(item: dict) -> str | None:
    return (item.get('title') or [None])[0] if isinstance(item.get('title'), list) else item.get('title')


def _crossref_authors(item: dict) -> list[str]:
    authors: list[str] = []
    for author in item.get('author', []) or []:
        name = ' '.join(x for x in [author.get('given'), author.get('family')] if x)
        if name:
            authors.append(name)
    return authors


def _crossref_year(item: dict) -> str | None:
    date_source = item.get('published-print') or item.get('published-online') or item.get('published') or item.get('issued') or {}
    date_parts = ((date_source.get('date-parts') or [[None]])[0])
    if date_parts and date_parts[0]:
        return str(date_parts[0])
    return None


def _crossref_venue(item: dict) -> str | None:
    return (item.get('container-title') or [None])[0] if isinstance(item.get('container-title'), list) else item.get('container-title')


def build_crossref_record(
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
        return EnrichmentRecord(candidate_id, 'crossref', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, raw_payload_json, latency_ms)

    title_value = _crossref_title_value(item)
    authors = _crossref_authors(item)
    year = _crossref_year(item)
    venue = _crossref_venue(item)
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, title_value, query_year, year, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=doi, provider_doi=item.get('DOI'), provider_name='crossref')
    return EnrichmentRecord(
        candidate_id=candidate_id,
        source_name='crossref',
        query_type=query_type,
        query_string=query_string,
        matched=matched_ok,
        match_score=1.0 if query_type == 'doi' else None,
        external_id=item.get('DOI'),
        title=title_value,
        authors_json=json.dumps(authors, ensure_ascii=False),
        abstract=item.get('abstract'),
        venue=venue,
        year=year,
        publication_type=item.get('type'),
        doi=item.get('DOI'),
        pmid=None,
        pmcid=None,
        url=item.get('URL'),
        raw_payload_json=raw_payload_json,
        latency_ms=latency_ms,
    )


def fetch_crossref_title_item(title: str, *, mailto: str | None = None) -> tuple[dict | None, str, int]:
    url = _crossref_url(
        'https://api.crossref.org/works',
        {
            'query.title': title,
            'rows': 1,
            'mailto': mailto,
        },
    )
    response = request_json('crossref', url, contact_email=mailto)
    if not response.ok:
        return None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms
    payload = response.json_data if isinstance(response.json_data, dict) else {}
    items = payload.get('message', {}).get('items', [])
    item = items[0] if items else None
    raw_payload_json = json.dumps(item if item else payload, ensure_ascii=False)
    return item, raw_payload_json, response.latency_ms


def query_crossref(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, mailto: str | None = None) -> EnrichmentRecord | None:
    if doi:
        url = _crossref_url(
            f"https://api.crossref.org/works/{urllib.parse.quote(doi)}",
            {
                'mailto': mailto,
                },
        )
        response = request_json('crossref', url, contact_email=mailto)
        if not response.ok:
            return EnrichmentRecord(candidate_id, 'crossref', 'doi', doi, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms)
        payload = response.json_data if isinstance(response.json_data, dict) else {}
        item = payload.get('message')
        return build_crossref_record(candidate_id, query_type='doi', query_string=doi, doi=doi, item=item, raw_payload_json=json.dumps(item if item else payload, ensure_ascii=False), latency_ms=response.latency_ms)
    if title:
        item, raw_payload_json, latency_ms = fetch_crossref_title_item(title, mailto=mailto)
        return build_crossref_record(candidate_id, query_type='title', query_string=title, doi=doi, item=item, raw_payload_json=raw_payload_json, latency_ms=latency_ms, first_author_family=first_author_family, venue_hint=venue_hint, query_year=query_year)
    return None
