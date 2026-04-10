from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result


ARXIV_NS = {'atom': 'http://www.w3.org/2005/Atom'}


def query_arxiv(candidate_id: str, *, arxiv_id: str | None = None, title: str | None = None, first_author_family: str | None = None, query_year: str | None = None) -> EnrichmentRecord | None:
    start = time.perf_counter()
    if arxiv_id:
        query_type = 'arxiv_id'
        query_string = arxiv_id
        url = f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
    elif title:
        query_type = 'title'
        query_string = title
        quoted_title = urllib.parse.quote('"' + title + '"')
        url = f"http://export.arxiv.org/api/query?search_query=ti:{quoted_title}&start=0&max_results=1"
    else:
        return None

    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            xml_text = resp.read().decode('utf-8')
        root = ET.fromstring(xml_text)
        entry = root.find('atom:entry', ARXIV_NS)
        if entry is None:
            return EnrichmentRecord(candidate_id, 'arxiv', query_type, query_string, False, None, None, None, None, None, None, None, 'preprint', None, None, None, None, json.dumps({'xml': xml_text}), int((time.perf_counter() - start) * 1000))

        title_value = (entry.findtext('atom:title', default='', namespaces=ARXIV_NS) or '').strip().replace('\n', ' ')
        abstract = (entry.findtext('atom:summary', default='', namespaces=ARXIV_NS) or '').strip().replace('\n', ' ')
        authors = []
        for author in entry.findall('atom:author', ARXIV_NS):
            name = (author.findtext('atom:name', default='', namespaces=ARXIV_NS) or '').strip()
            if name:
                authors.append(name)
        published = (entry.findtext('atom:published', default='', namespaces=ARXIV_NS) or '').strip()
        year = published[:4] if len(published) >= 4 else None
        external_id = (entry.findtext('atom:id', default='', namespaces=ARXIV_NS) or '').strip() or None
        matched_ok = True
        if query_type == 'title':
            matched_ok = accept_result(query_string, title_value, query_year, year, first_author_family, json.dumps(authors, ensure_ascii=False), provider_name='arxiv')
        return EnrichmentRecord(candidate_id, 'arxiv', query_type, query_string, matched_ok, 1.0 if query_type == 'arxiv_id' else None, external_id, title_value or None, json.dumps(authors, ensure_ascii=False), abstract or None, 'arXiv', year, 'preprint', None, None, None, external_id, json.dumps({'xml': xml_text}, ensure_ascii=False), int((time.perf_counter() - start) * 1000))
    except Exception as e:
        return EnrichmentRecord(candidate_id, 'arxiv', query_type, query_string, False, None, None, None, None, None, None, None, 'preprint', None, None, None, None, json.dumps({'error': str(e)}), int((time.perf_counter() - start) * 1000))
