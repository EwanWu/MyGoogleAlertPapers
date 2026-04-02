from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qs, unquote

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
PMID_RE = re.compile(r"(?:pubmed\.ncbi\.nlm\.nih\.gov/|pmid[/:\s])(?P<pmid>\d{5,10})", re.IGNORECASE)
PMCID_RE = re.compile(r"(?:pmc/articles/|pmcid[/:\s])(?P<pmcid>PMC\d+)", re.IGNORECASE)
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(?P<arxiv>[0-9]{4}\.[0-9]{4,5})(?:v\d+)?", re.IGNORECASE)


def extract_doi(text: str | None) -> str | None:
    if not text:
        return None
    m = DOI_RE.search(text)
    return m.group(0).lower() if m else None


def extract_pmid(text: str | None) -> str | None:
    if not text:
        return None
    m = PMID_RE.search(text)
    return m.group("pmid") if m else None


def extract_pmcid(text: str | None) -> str | None:
    if not text:
        return None
    m = PMCID_RE.search(text)
    return m.group("pmcid").upper() if m else None


def extract_arxiv_id(text: str | None) -> str | None:
    if not text:
        return None
    m = ARXIV_RE.search(text)
    return m.group("arxiv") if m else None


def canonicalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or ""
    query = parsed.query
    if "scholar.google." in netloc and parsed.path == "/scholar_url":
        q = parse_qs(query)
        target = q.get("url", [None])[0]
        return unquote(target) if target else url
    canonical = f"{scheme}://{netloc}{path}"
    if query and "scholar.google." not in netloc:
        canonical = f"{canonical}?{query}"
    return canonical
