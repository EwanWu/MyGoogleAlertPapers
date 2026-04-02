from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

from mygooglealertpapers.enrich.base import EnrichmentRecord


def query_crossref(candidate_id: str, *, doi: str | None, title: str | None) -> EnrichmentRecord | None:
    start = time.perf_counter()
    if doi:
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
        query_type = "doi"
        query_string = doi
    elif title:
        url = f"https://api.crossref.org/works?query.title={urllib.parse.quote(title)}&rows=1"
        query_type = "title"
        query_string = title
    else:
        return None
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return EnrichmentRecord(candidate_id, "crossref", query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps({"error": str(e)}), int((time.perf_counter()-start)*1000))

    item = payload.get("message")
    if query_type == "title":
        items = payload.get("message", {}).get("items", [])
        item = items[0] if items else None
    if not item:
        return EnrichmentRecord(candidate_id, "crossref", query_type, query_string, False, None, None, None, None, None, None, None, None, doi, None, None, None, json.dumps(payload), int((time.perf_counter()-start)*1000))

    title_value = (item.get("title") or [None])[0] if isinstance(item.get("title"), list) else item.get("title")
    authors = []
    for a in item.get("author", []) or []:
        name = " ".join(x for x in [a.get("given"), a.get("family")] if x)
        if name:
            authors.append(name)
    year = None
    date_parts = (((item.get("published-print") or item.get("published-online") or {}).get("date-parts") or [[None]])[0])
    if date_parts and date_parts[0]:
        year = str(date_parts[0])
    return EnrichmentRecord(
        candidate_id=candidate_id,
        source_name="crossref",
        query_type=query_type,
        query_string=query_string,
        matched=True,
        match_score=1.0 if doi else None,
        external_id=item.get("DOI"),
        title=title_value,
        authors_json=json.dumps(authors, ensure_ascii=False),
        abstract=item.get("abstract"),
        venue=(item.get("container-title") or [None])[0] if isinstance(item.get("container-title"), list) else item.get("container-title"),
        year=year,
        publication_type=item.get("type"),
        doi=item.get("DOI"),
        pmid=None,
        pmcid=None,
        url=(item.get("URL")),
        raw_payload_json=json.dumps(item, ensure_ascii=False),
        latency_ms=int((time.perf_counter()-start)*1000),
    )
