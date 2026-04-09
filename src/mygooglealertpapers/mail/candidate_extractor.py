from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

from mygooglealertpapers.mail.message_parser import ParsedEmail


@dataclass(slots=True)
class PaperCandidateRaw:
    candidate_id: str
    mail_uid: str
    candidate_index_in_mail: int
    raw_title: str | None
    raw_authors: str | None
    raw_source_text: str | None
    raw_link: str | None
    raw_snippet: str | None
    parser_confidence: float
    template_variant: str
    extraction_notes: str | None = None
    scholar_wrapper_url: str | None = None
    target_url: str | None = None
    resource_type_hint: str | None = None
    venue_guess: str | None = None
    year_guess: str | None = None


RESOURCE_PREFIXES = {
    "[html]": "html",
    "[pdf]": "pdf",
}


def _candidate_id(mail_uid: str, idx: int, title: str | None) -> str:
    digest = hashlib.sha1(f"{mail_uid}|{idx}|{title or ''}".encode("utf-8")).hexdigest()[:16]
    return f"cand_{digest}"


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.split()).strip()
    return cleaned or None


def _unwrap_scholar_url(href: str | None) -> tuple[str | None, str | None]:
    href = _clean_text(href)
    if not href:
        return None, None
    parsed = urlparse(href)
    if "scholar.google." in parsed.netloc and parsed.path == "/scholar_url":
        q = parse_qs(parsed.query)
        target = q.get("url", [None])[0]
        return href, unquote(target) if target else None
    return href, href


def _infer_resource_type(title: str | None, target_url: str | None) -> tuple[str | None, str | None]:
    title = _clean_text(title)
    if not title:
        return None, None
    lowered = title.casefold()
    for prefix, resource_type in RESOURCE_PREFIXES.items():
        if lowered.startswith(prefix):
            stripped = _clean_text(title[len(prefix):])
            return resource_type, stripped
    if target_url:
        url_lower = target_url.casefold()
        if url_lower.endswith('.pdf') or '/pdf/' in url_lower or url_lower.endswith('/full.pdf'):
            return 'pdf', title
        if '/article/' in url_lower or '/abs/' in url_lower or '/abstract' in url_lower or '/full/' in url_lower:
            return 'html', title
    return None, title


def _looks_like_title(text: str | None) -> bool:
    if not text:
        return False
    if len(text) < 20 or len(text) > 500:
        return False
    lowered = text.casefold()
    reject_hints = [
        'view all',
        'my profile',
        'google scholar',
        'alert',
        'unsubscribe',
        'view it on google scholar',
        'edit this alert',
    ]
    return not any(h in lowered for h in reject_hints)


def _parse_snippet(snippet: str | None) -> tuple[str | None, str | None, str | None]:
    snippet = _clean_text(snippet)
    if not snippet:
        return None, None, None
    authors_raw = None
    venue_guess = None
    year_guess = None
    if ' - ' in snippet:
        left, right = snippet.split(' - ', 1)
        authors_raw = _clean_text(left)
        right = _clean_text(right)
        if right:
            if right.isdigit() and len(right) == 4:
                year_guess = right
            else:
                venue_guess = right
                if ',' in right:
                    maybe_year = _clean_text(right.rsplit(',', 1)[-1])
                    if maybe_year and maybe_year.isdigit() and len(maybe_year) == 4:
                        year_guess = maybe_year
                        venue_guess = _clean_text(right.rsplit(',', 1)[0])
    return authors_raw, venue_guess, year_guess


def extract_candidates(parsed_email: ParsedEmail, mail_uid: str) -> list[PaperCandidateRaw]:
    candidates: list[PaperCandidateRaw] = []
    if not parsed_email.body_html:
        return candidates

    soup = BeautifulSoup(parsed_email.body_html, 'html.parser')
    seen_titles: set[str] = set()
    idx = 0

    for link in soup.find_all('a', href=True):
        title = _clean_text(link.get_text(' ', strip=True))
        wrapper_url, target_url = _unwrap_scholar_url(link.get('href'))
        resource_type_hint, clean_title = _infer_resource_type(title, target_url)
        if not _looks_like_title(clean_title):
            continue
        if not target_url:
            continue
        title_key = clean_title.casefold()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        context_line = None
        snippet_text = None
        parent = link.parent
        if parent is not None:
            context_line = _clean_text(parent.get_text(' ', strip=True))
            next_sibling = parent.find_next_sibling()
            if next_sibling is not None:
                snippet_text = _clean_text(next_sibling.get_text(' ', strip=True))

        authors_raw, venue_guess, year_guess = _parse_snippet(snippet_text)

        idx += 1
        candidates.append(
            PaperCandidateRaw(
                candidate_id=_candidate_id(mail_uid, idx, clean_title),
                mail_uid=mail_uid,
                candidate_index_in_mail=idx,
                raw_title=clean_title,
                raw_authors=authors_raw,
                raw_source_text=context_line,
                raw_link=target_url,
                raw_snippet=snippet_text,
                parser_confidence=0.72,
                template_variant='html_anchor_context_v3',
                extraction_notes='Title/link from anchor with Scholar URL unwrapping, resource-type inference, and safer snippet parsing.',
                scholar_wrapper_url=wrapper_url,
                target_url=target_url,
                resource_type_hint=resource_type_hint,
                venue_guess=venue_guess,
                year_guess=year_guess,
            )
        )

    return candidates
