"""Unpaywall DOI-only enrichment provider.

Unpaywall is an OA (open access) metadata aggregator. Its primary value in this
pipeline is OA status and OA URL — not core bibliographic metadata, which is
already covered by Crossref / OpenAlex / PubMed.

Design constraints:
- DOI-only lookup; no title-based search
- Must not be treated as a bibliographic authority for merge/canonical decisions
- Only OA status, best_oa_url, and oa_locations are novel signal
- All bibliographic fields (title, authors, year, venue) are best-effort and
  should not override strong matches from primary providers
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from mygooglealertpapers.enrich.base import EnrichmentRecord


def _get_proxy_opener():
    """Return a urllib opener that respects system proxy settings (http_proxy/https_proxy).

    On Windows/macOS this picks up system proxy automatically.
    On Linux with environment variables set, this also works if the vars are exported.
    """
    proxies = urllib.request.getproxies()
    if not proxies:
        return None
    handler = urllib.request.ProxyHandler(proxies)
    return urllib.request.build_opener(handler)


_unpaywall_opener = _get_proxy_opener()


def query_unpaywall(
    candidate_id: str,
    *,
    doi: str | None,
    title: str | None = None,
    first_author_family: str | None = None,
    venue_hint: str | None = None,
    query_year: str | None = None,
    email: str | None = None,
) -> EnrichmentRecord | None:
    """Query Unpaywall for OA status and URL by DOI.

    Returns None if no DOI is available — Unpaywall does not support title search.

    The returned record has:
    - matched: True if a response was received (even if is_oa=False)
    - title/authors/year/venue: best-effort from Unpaywall (may be incomplete)
    - url: best_oa_url from Unpaywall (primary novel signal for this provider)
    - raw_payload_json: full Unpaywall response for debugging
    """
    start = time.perf_counter()

    if not doi:
        return None

    if not email:
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name="unpaywall",
            query_type="doi",
            query_string=doi,
            matched=False,
            match_score=None,
            external_id=None,
            title=None,
            authors_json=None,
            abstract=None,
            venue=None,
            year=None,
            publication_type=None,
            doi=None,
            pmid=None,
            pmcid=None,
            url=None,
            raw_payload_json=json.dumps({"error": "no email configured for Unpaywall"}),
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}"

    proxies = urllib.request.getproxies()
    opener = _get_proxy_opener()

    try:
        if opener:
            with opener.open(url, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        else:
            with urllib.request.urlopen(url, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else "{}"
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name="unpaywall",
            query_type="doi",
            query_string=doi,
            matched=False,
            match_score=None,
            external_id=None,
            title=None,
            authors_json=None,
            abstract=None,
            venue=None,
            year=None,
            publication_type=None,
            doi=doi,
            pmid=None,
            pmcid=None,
            url=None,
            raw_payload_json=json.dumps({"http_error": e.code, "body": raw[:500]}),
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
    except Exception as e:
        return EnrichmentRecord(
            candidate_id=candidate_id,
            source_name="unpaywall",
            query_type="doi",
            query_string=doi,
            matched=False,
            match_score=None,
            external_id=None,
            title=None,
            authors_json=None,
            abstract=None,
            venue=None,
            year=None,
            publication_type=None,
            doi=doi,
            pmid=None,
            pmcid=None,
            url=None,
            raw_payload_json=json.dumps({"error": str(e)}),
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    # Unpaywall found a response
    is_oa = bool(payload.get("is_oa"))
    oa_status = payload.get("oa_status")  # gold | green | hybrid | closed | null
    best_oa_location = payload.get("best_oa_location") or {}
    best_oa_url = best_oa_location.get("url") if isinstance(best_oa_location, dict) else None

    # Extract bibliographic fields (best-effort — Unpaywall is not authoritative)
    title_val = payload.get("title")
    year_val = payload.get("year")
    genre = payload.get("genre")

    # Authors
    authors_raw = payload.get("authors", []) or []
    authors = []
    for a in authors_raw:
        name = " ".join(x for x in [a.get("given"), a.get("family")] if x)
        if name:
            authors.append(name)
    authors_json = json.dumps(authors, ensure_ascii=False) if authors else None

    # Venue / journal
    journal = payload.get("journal_name") or payload.get("publisher")

    # PMID / PMCID (sometimes available)
    pmid_val = payload.get("pmid")
    pmcid_val = payload.get("pmcid")

    # Build query string for trace
    query_string = doi

    return EnrichmentRecord(
        candidate_id=candidate_id,
        source_name="unpaywall",
        query_type="doi",
        query_string=query_string,
        matched=True,  # Unpaywall returned a response
        match_score=1.0 if is_oa else 0.5,  # Higher score for actual OA
        external_id=doi,
        title=title_val,
        authors_json=authors_json,
        abstract=None,
        venue=journal,
        year=str(year_val) if year_val else None,
        publication_type=genre,
        doi=doi,
        pmid=str(pmid_val) if pmid_val else None,
        pmcid=str(pmcid_val) if pmcid_val else None,
        url=best_oa_url,
        raw_payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
        latency_ms=int((time.perf_counter() - start) * 1000),
    )
