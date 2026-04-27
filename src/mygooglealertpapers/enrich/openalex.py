from __future__ import annotations

import json
import urllib.parse

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result
from mygooglealertpapers.enrich.http_client import request_json


def _extract_primary_location_fields(item: dict) -> tuple[str | None, str | None]:
    primary_location = item.get('primary_location') or {}
    source = primary_location.get('source') or {}
    venue = source.get('display_name')
    url = primary_location.get('landing_page_url')
    return venue, url


def query_openalex(candidate_id: str, *, doi: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, email: str | None = None) -> EnrichmentRecord | None:
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
    if email:
        url += f"&email={urllib.parse.quote(email)}"

    response = request_json('openalex', url, contact_email=email)
    if not response.ok:
        return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(response.to_error_payload(), ensure_ascii=False), response.latency_ms)

    payload = response.json_data if isinstance(response.json_data, dict) else {}
    results = payload.get('results', [])
    if not results:
        return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(payload, ensure_ascii=False), response.latency_ms)
    item = results[0]
    authors = [a.get('author', {}).get('display_name') for a in item.get('authorships', []) if a.get('author', {}).get('display_name')]
    venue, url = _extract_primary_location_fields(item)
    ids = item.get('ids') or {}
    provider_doi = (ids.get('doi') or '').replace('https://doi.org/', '') or None
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, item.get('display_name'), query_year, str(item.get('publication_year')) if item.get('publication_year') else None, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=doi, provider_doi=provider_doi, provider_name='openalex')
    return EnrichmentRecord(candidate_id, 'openalex', query_type, query_string, matched_ok, 1.0 if doi else None, item.get('id'), item.get('display_name'), json.dumps(authors, ensure_ascii=False), item.get('abstract_inverted_index') and json.dumps(item.get('abstract_inverted_index')), venue, str(item.get('publication_year')) if item.get('publication_year') else None, item.get('type'), provider_doi, (ids.get('pmid') or '').replace('https://pubmed.ncbi.nlm.nih.gov/', '').strip('/') or None, (ids.get('pmcid') or '').replace('https://www.ncbi.nlm.nih.gov/pmc/articles/', '').strip('/') or None, url, json.dumps(item, ensure_ascii=False), response.latency_ms)



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
