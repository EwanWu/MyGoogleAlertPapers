from __future__ import annotations

import hashlib
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage


@dataclass(slots=True)
class ParsedEmail:
    message_id: str | None
    subject: str | None
    from_address: str | None
    headers: dict[str, str]
    body_text: str
    body_html: str
    body_hash: str


def _extract_bodies(message: EmailMessage) -> tuple[str, str]:
    body_text_parts: list[str] = []
    body_html_parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if part.get_content_disposition() == "attachment":
                continue
            try:
                payload = part.get_content()
            except Exception:
                continue
            if not isinstance(payload, str):
                continue
            if content_type == "text/plain":
                body_text_parts.append(payload)
            elif content_type == "text/html":
                body_html_parts.append(payload)
    else:
        payload = message.get_content()
        if isinstance(payload, str):
            if message.get_content_type() == "text/html":
                body_html_parts.append(payload)
            else:
                body_text_parts.append(payload)
    return "\n".join(body_text_parts).strip(), "\n".join(body_html_parts).strip()


def parse_raw_email(raw_bytes: bytes) -> ParsedEmail:
    message = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    body_text, body_html = _extract_bodies(message)
    body_hash = hashlib.sha256(raw_bytes).hexdigest()
    headers = {k: str(v) for k, v in message.items()}
    return ParsedEmail(
        message_id=message.get("Message-Id"),
        subject=message.get("Subject"),
        from_address=message.get("From"),
        headers=headers,
        body_text=body_text,
        body_html=body_html,
        body_hash=body_hash,
    )
