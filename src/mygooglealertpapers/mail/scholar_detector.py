from __future__ import annotations

from dataclasses import dataclass

from mygooglealertpapers.mail.message_parser import ParsedEmail


SCHOLAR_FROM_HINTS = [
    "scholaralerts-noreply@google.com",
]

SCHOLAR_TEXT_HINTS = [
    "google scholar",
    "google 学术",
    "new articles",
    "new citations",
    "new results",
    "related articles",
]


@dataclass(slots=True)
class DetectionResult:
    is_match: bool
    reason: str


def detect_google_scholar_alert(parsed_email: ParsedEmail) -> DetectionResult:
    from_value = (parsed_email.from_address or "").lower()
    subject_value = (parsed_email.subject or "").lower()
    body_probe = f"{parsed_email.body_text}\n{parsed_email.body_html}".lower()

    if any(hint in from_value for hint in SCHOLAR_FROM_HINTS):
        return DetectionResult(True, "from_address_match")
    if any(hint in subject_value for hint in SCHOLAR_TEXT_HINTS):
        return DetectionResult(True, "subject_hint_match")
    if any(hint in body_probe for hint in SCHOLAR_TEXT_HINTS):
        return DetectionResult(True, "body_hint_match")
    return DetectionResult(False, "no_match")
