from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result


def query_europepmc(candidate_id: str, *, doi: str | None = None, pmid: str | None = None, title: str | None = None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None) -> EnrichmentRecord | None:
    start = time.perf_counter()
    if pmid:
        query_type = 'pmid'
        query_string = pmid
        url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{urllib.parse.quote(pmid)}%20AND%20SRC:MED&format=json&pageSize=1'
    elif doi:
        query_type = 'doi'
        query_string = doi
        url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{urllib.parse.quote(doi)}&format=json&pageSize=1'
    elif title:
        query_type = 'title'
        query_string = title
        url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE:%22{urllib.parse.quote(title)}%22&format=json&pageSize=1'
    else:
        return None

    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return EnrichmentRecord(candidate_id, 'europepmc', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, pmid, None, None, json.dumps({'error': str(e)}), int((time.perf_counter() - start) * 1000))

    results = (payload.get('resultList') or {}).get('result') or []
    if not results:
        return EnrichmentRecord(candidate_id, 'europepmc', query_type, query_string, False, None, None, None, None, None, None, None, None, doi, pmid, None, None, json.dumps(payload), int((time.perf_counter() - start) * 1000))

    item = results[0]
    authors = [name.strip() for name in (item.get('authorString') or '').replace('.', '. ').split(',') if name.strip()]
    title_value = item.get('title')
    venue = item.get('journalTitle')
    year = item.get('pubYear')
    provider_doi = item.get('doi')
    provider_pmid = item.get('pmid') or (item.get('id') if item.get('source') == 'MED' else None)
    provider_pmcid = item.get('pmcid')
    abstract = item.get('abstractText')
    matched_ok = True
    if query_type == 'title':
        matched_ok = accept_result(query_string, title_value, query_year, year, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=doi, provider_doi=provider_doi, provider_name='europepmc')
    return EnrichmentRecord(candidate_id, 'europepmc', query_type, query_string, matched_ok, 1.0 if query_type in {'doi', 'pmid'} else None, item.get('id'), title_value, json.dumps(authors, ensure_ascii=False), abstract, venue, year, item.get('pubType'), provider_doi, provider_pmid, provider_pmcid, item.get('fullTextUrlList', {}).get('fullTextUrl', [{}])[0].get('url') if item.get('fullTextUrlList') else None, json.dumps(item, ensure_ascii=False), int((time.perf_counter() - start) * 1000))
