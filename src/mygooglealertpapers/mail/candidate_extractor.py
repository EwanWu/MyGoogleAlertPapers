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


def extract_candidates(parsed_email: ParsedEmail, mail_uid: str) -> list[PaperCandidateRaw]:
    candidates: list[PaperCandidateRaw] = []
    if parsed_email.body_html:
        soup = BeautifulSoup(parsed_email.body_html, "html.parser")
        seen_titles: set[str] = set()
        links = soup.find_all("a", href=True)
        idx = 0
        for link in links:
            title = " ".join(link.get_text(" ", strip=True).split())
            href = link.get("href")
            if not title or len(title) < 20:
                continue
            title_key = title.casefold()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            idx += 1
            candidates.append(
                PaperCandidateRaw(
                    candidate_id=_candidate_id(mail_uid, idx, title),
                    mail_uid=mail_uid,
                    candidate_index_in_mail=idx,
                    raw_title=title,
                    raw_authors=None,
                    raw_source_text=None,
                    raw_link=href,
                    raw_snippet=None,
                    parser_confidence=0.45,
                    template_variant="html_link_fallback",
                    extraction_notes="Extracted from anchor text fallback; author/source/snippet not yet implemented.",
                )
            )
    return candidates
