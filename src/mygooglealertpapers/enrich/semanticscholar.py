from __future__ import annotations

import json
import urllib.parse

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result
from mygooglealertpapers.enrich.http_client import request_json


BASE_FIELDS = 'title,authors,venue,year,externalIds,url'


def build_semanticscholar_record(
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
        return EnrichmentRecord(candidate_id, 'semanticscholar', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, raw_payload_json, latency_ms)

    authors = [author.get('name') for author in item.get('authors', []) if author.get('name')]
    ext = item.get('externalIds') or {}
    venue = item.get('venue')
    year = str(item.get('year')) if item.get('year') else None
    provider_doi = ext.get('DOI')
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, item.get('title'), query_year, year, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=doi, provider_doi=provider_doi, provider_name='semanticscholar')
    return EnrichmentRecord(
        candidate_id=candidate_id,
        source_name='semanticscholar',
        query_type=query_type,
        query_string=query_string,
        matched=matched_ok,
        match_score=1.0 if query_type == 'doi' else None,
        external_id=item.get('paperId'),
        title=item.get('title'),
        authors_json=json.dumps(authors, ensure_ascii=False),
        abstract=None,
        venue=venue,
        year=year,
        publication_type=None,
        doi=provider_doi,
        pmid=ext.get('PubMed'),
        pmcid=ext.get('PubMedCentral'),
        url=item.get('url'),
        raw_payload_json=raw_payload_json,
        latency_ms=latency_ms,
    )


def fetch_semanticscholar_title_item(title: str, *, api_key: str | None = None) -> tuple[dict | None, str, int]:
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(title)}&limit=1&fields={urllib.parse.quote(BASE_FIELDS, safe=",")}'
    extra_headers = {'x-api-key': api_key} if api_key else None
    response = request_json('semanticscholar', url, extra_headers=extra_headers)
    if not response.ok:
        return None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms
    payload = response.json_data if isinstance(response.json_data, dict) else {}
    item = (payload.get('data') or [None])[0]
    raw_payload_json = json.dumps(item if item else payload, ensure_ascii=False)
    return item, raw_payload_json, response.latency_ms


def query_semanticscholar(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, api_key: str | None = None) -> EnrichmentRecord | None:
    if doi:
        paper_id = urllib.parse.quote(f'DOI:{doi}', safe='')
        url = f'https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={urllib.parse.quote(BASE_FIELDS, safe=",")}'
        extra_headers = {'x-api-key': api_key} if api_key else None
        response = request_json('semanticscholar', url, extra_headers=extra_headers)
        if not response.ok:
            return EnrichmentRecord(candidate_id, 'semanticscholar', 'doi', doi, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms)
        payload = response.json_data if isinstance(response.json_data, dict) else {}
        return build_semanticscholar_record(candidate_id, query_type='doi', query_string=doi, doi=doi, item=payload if isinstance(payload, dict) else None, raw_payload_json=json.dumps(payload, ensure_ascii=False), latency_ms=response.latency_ms)
    if title:
        item, raw_payload_json, latency_ms = fetch_semanticscholar_title_item(title, api_key=api_key)
        return build_semanticscholar_record(candidate_id, query_type='title', query_string=title, doi=doi, item=item, raw_payload_json=raw_payload_json, latency_ms=latency_ms, first_author_family=first_author_family, venue_hint=venue_hint, query_year=query_year)
    return None
