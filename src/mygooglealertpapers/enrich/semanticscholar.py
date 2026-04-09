from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result


BASE_FIELDS = 'title,authors,venue,year,externalIds,url'


def _request_json(url: str, *, api_key: str | None = None, timeout: int = 20):
    req = urllib.request.Request(url)
    if api_key:
        req.add_header('x-api-key', api_key)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def query_semanticscholar(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, api_key: str | None = None) -> EnrichmentRecord | None:
    start = time.perf_counter()
    if doi:
        query_type = 'doi'
        query_string = doi
        paper_id = urllib.parse.quote(f'DOI:{doi}', safe='')
        url = f'https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={urllib.parse.quote(BASE_FIELDS, safe=",")}'
        mode = 'paper'
    elif title:
        query_type = 'title'
        query_string = title
        url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(title)}&limit=1&fields={urllib.parse.quote(BASE_FIELDS, safe=",")}'
        mode = 'search'
    else:
        return None
    try:
        payload = _request_json(url, api_key=api_key)
    except Exception as e:
        return EnrichmentRecord(candidate_id, 'semanticscholar', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps({'error': str(e)}), int((time.perf_counter()-start)*1000))

    item = payload if mode == 'paper' else ((payload.get('data') or [None])[0])
    if not item:
        return EnrichmentRecord(candidate_id, 'semanticscholar', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(payload, ensure_ascii=False), int((time.perf_counter()-start)*1000))

    authors = [a.get('name') for a in item.get('authors', []) if a.get('name')]
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
        match_score=1.0 if doi else None,
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
        raw_payload_json=json.dumps(item, ensure_ascii=False),
        latency_ms=int((time.perf_counter()-start)*1000),
    )
