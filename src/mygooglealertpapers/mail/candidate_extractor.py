from __future__ import annotations

import hashlib
from dataclasses import dataclass

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


def _candidate_id(mail_uid: str, idx: int, title: str | None) -> str:
    digest = hashlib.sha1(f"{mail_uid}|{idx}|{title or ''}".encode("utf-8")).hexdigest()[:16]
    return f"cand_{digest}"


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.split()).strip()
    return cleaned or None


def _looks_like_title(text: str | None) -> bool:
    if not text:
        return False
    if len(text) < 20 or len(text) > 500:
        return False
    lowered = text.casefold()
    reject_hints = [
        "view all",
        "my profile",
        "google scholar",
        "alert",
        "unsubscribe",
        "view it on google scholar",
        "edit this alert",
    ]
    return not any(h in lowered for h in reject_hints)


def extract_candidates(parsed_email: ParsedEmail, mail_uid: str) -> list[PaperCandidateRaw]:
    candidates: list[PaperCandidateRaw] = []
    if not parsed_email.body_html:
        return candidates

    soup = BeautifulSoup(parsed_email.body_html, "html.parser")
    seen_titles: set[str] = set()
    idx = 0

    for link in soup.find_all("a", href=True):
        title = _clean_text(link.get_text(" ", strip=True))
        href = _clean_text(link.get("href"))
        if not _looks_like_title(title):
            continue
        if not href:
            continue
        title_key = title.casefold()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        parent_text = None
        snippet_text = None
        parent = link.parent
        if parent is not None:
            parent_text = _clean_text(parent.get_text(" ", strip=True))
            next_sibling = parent.find_next_sibling()
            if next_sibling is not None:
                snippet_text = _clean_text(next_sibling.get_text(" ", strip=True))

        idx += 1
        candidates.append(
            PaperCandidateRaw(
                candidate_id=_candidate_id(mail_uid, idx, title),
                mail_uid=mail_uid,
                candidate_index_in_mail=idx,
                raw_title=title,
                raw_authors=None,
                raw_source_text=parent_text,
                raw_link=href,
                raw_snippet=snippet_text,
                parser_confidence=0.55,
                template_variant="html_anchor_context_v1",
                extraction_notes="Title/link from anchor with parent/sibling context fallback.",
            )
        )

    return candidates
