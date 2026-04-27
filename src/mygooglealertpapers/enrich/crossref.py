from __future__ import annotations

import json
import urllib.parse

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result
from mygooglealertpapers.enrich.http_client import request_json


def query_crossref(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, mailto: str | None = None) -> EnrichmentRecord | None:
    if doi:
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
        if mailto:
            url += f"?mailto={urllib.parse.quote(mailto)}"
        query_type = 'doi'
        query_string = doi
    elif title:
        url = f"https://api.crossref.org/works?query.title={urllib.parse.quote(title)}&rows=1"
        if mailto:
            url += f"&mailto={urllib.parse.quote(mailto)}"
        query_type = 'title'
        query_string = title
    else:
        return None

    response = request_json('crossref', url, contact_email=mailto)
    if not response.ok:
        return EnrichmentRecord(candidate_id, 'crossref', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms)

    payload = response.json_data if isinstance(response.json_data, dict) else {}
    item = payload.get('message')
    if query_type == 'title':
        items = payload.get('message', {}).get('items', [])
        item = items[0] if items else None
    if not item:
        return EnrichmentRecord(candidate_id, 'crossref', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(payload, ensure_ascii=False), response.latency_ms)

    title_value = (item.get('title') or [None])[0] if isinstance(item.get('title'), list) else item.get('title')
    authors = []
    for author in item.get('author', []) or []:
        name = ' '.join(x for x in [author.get('given'), author.get('family')] if x)
        if name:
            authors.append(name)
    year = None
    date_parts = (((item.get('published-print') or item.get('published-online') or {}).get('date-parts') or [[None]])[0])
    if date_parts and date_parts[0]:
        year = str(date_parts[0])
    venue = (item.get('container-title') or [None])[0] if isinstance(item.get('container-title'), list) else item.get('container-title')
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, title_value, query_year, year, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=doi, provider_doi=item.get('DOI'), provider_name='crossref')
    return EnrichmentRecord(
        candidate_id=candidate_id,
        source_name='crossref',
        query_type=query_type,
        query_string=query_string,
        matched=matched_ok,
        match_score=1.0 if doi else None,
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
        raw_payload_json=json.dumps(item, ensure_ascii=False),
        latency_ms=response.latency_ms,
    )
