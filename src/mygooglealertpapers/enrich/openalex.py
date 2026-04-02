from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result


def query_openalex(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None) -> EnrichmentRecord | None:
    start = time.perf_counter()
    if doi:
        url = f"https://api.openalex.org/works?filter=doi:{urllib.parse.quote('https://doi.org/' + doi)}&per-page=1"
        query_type = 'doi'
        query_string = doi
    elif title:
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(title)}&per-page=1"
        query_type = 'title'
        query_string = title
    else:
        return None
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps({'error': str(e)}), int((time.perf_counter()-start)*1000))
    results = payload.get('results', [])
    if not results:
        return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(payload), int((time.perf_counter()-start)*1000))
    item = results[0]
    authors = [a.get('author', {}).get('display_name') for a in item.get('authorships', []) if a.get('author', {}).get('display_name')]
    venue = (item.get('primary_location') or {}).get('source', {}).get('display_name')
    ids = item.get('ids') or {}
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, item.get('display_name'), query_year, str(item.get('publication_year')) if item.get('publication_year') else None, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue)
    return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, matched_ok, 1.0 if doi else None, item.get('id'), item.get('display_name'), json.dumps(authors, ensure_ascii=False), item.get('abstract_inverted_index') and json.dumps(item.get('abstract_inverted_index')), venue, str(item.get('publication_year')) if item.get('publication_year') else None, item.get('type'), (ids.get('doi') or '').replace('https://doi.org/', '') or None, (ids.get('pmid') or '').replace('https://pubmed.ncbi.nlm.nih.gov/', '').strip('/') or None, (ids.get('pmcid') or '').replace('https://www.ncbi.nlm.nih.gov/pmc/articles/', '').strip('/') or None, (item.get('primary_location') or {}).get('landing_page_url'), json.dumps(item, ensure_ascii=False), int((time.perf_counter()-start)*1000))
