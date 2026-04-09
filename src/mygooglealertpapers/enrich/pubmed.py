from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from mygooglealertpapers.enrich.base import EnrichmentRecord, accept_result


def query_pubmed(candidate_id: str, *, pmid: str | None, title: str | None, first_author_family: str | None = None, venue_hint: str | None = None, query_year: str | None = None, candidate_doi: str | None = None) -> EnrichmentRecord | None:
    start = time.perf_counter()
    query_type = None
    query_string = None
    try:
        if pmid:
            query_type = "pmid"
            query_string = pmid
            efetch = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={urllib.parse.quote(pmid)}&retmode=xml"
        elif title:
            query_type = "title"
            query_string = title
            esearch = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=1&term={urllib.parse.quote(title)}[Title]"
            with urllib.request.urlopen(esearch, timeout=20) as resp:
                search_xml = resp.read().decode('utf-8')
            root = ET.fromstring(search_xml)
            ids = [e.text for e in root.findall('.//Id') if e.text]
            if not ids:
                return EnrichmentRecord(candidate_id, 'pubmed', query_type, query_string, False, None, None, None, None, None, None, None, None, None, None, None, None, json.dumps({'search_xml': search_xml}), int((time.perf_counter()-start)*1000))
            pmid = ids[0]
            efetch = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={urllib.parse.quote(pmid)}&retmode=xml"
        else:
            return None
        with urllib.request.urlopen(efetch, timeout=20) as resp:
            xml_text = resp.read().decode('utf-8')
        root = ET.fromstring(xml_text)
        article = root.find('.//PubmedArticle')
        if article is None:
            return EnrichmentRecord(candidate_id, 'pubmed', query_type, query_string, False, None, None, None, None, None, None, None, None, None, pmid, None, None, json.dumps({'xml': xml_text}), int((time.perf_counter()-start)*1000))
        title_value = ''.join(article.findtext('.//ArticleTitle') or '')
        abstract = ' '.join(t.text or '' for t in article.findall('.//AbstractText')) or None
        authors = []
        for a in article.findall('.//Author'):
            last = a.findtext('LastName')
            fore = a.findtext('ForeName')
            name = ' '.join(x for x in [fore, last] if x)
            if name:
                authors.append(name)
        venue = article.findtext('.//Journal/Title')
        year = article.findtext('.//PubDate/Year')
        doi = None
        for aid in article.findall('.//ArticleId'):
            if aid.attrib.get('IdType') == 'doi' and aid.text:
                doi = aid.text.lower()
        pmcid = None
        for aid in article.findall('.//ArticleId'):
            if aid.attrib.get('IdType') == 'pmc' and aid.text:
                pmcid = aid.text.upper()
        matched_ok = True
        if query_type == 'title':
            matched_ok = accept_result(query_string, title_value, query_year, year, first_author_family, json.dumps(authors, ensure_ascii=False), venue_hint, venue, candidate_doi=candidate_doi, provider_doi=doi, provider_name='pubmed')
        return EnrichmentRecord(candidate_id, 'pubmed', query_type, query_string, matched_ok, 1.0 if query_type == 'pmid' else None, pmid, title_value, json.dumps(authors, ensure_ascii=False), abstract, venue, year, 'journal-article', doi, pmid, pmcid, f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/' if pmid else None, json.dumps({'xml': xml_text}), int((time.perf_counter()-start)*1000))
    except Exception as e:
        return EnrichmentRecord(candidate_id, 'pubmed', query_type or 'unknown', query_string or '', False, None, None, None, None, None, None, None, None, None, pmid, None, None, json.dumps({'error': str(e)}), int((time.perf_counter()-start)*1000))
