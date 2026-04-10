from __future__ import annotations

import html
import json
import re
import unicodedata


def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    text = html.unescape(str(value))
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('–', '-').replace('—', '-').replace('−', '-')
    text = text.replace('“', '"').replace('”', '"').replace('’', "'")
    text = re.sub(r'\s+', ' ', text).strip()
    return text or None


def comparison_text(value: str | None) -> str:
    text = clean_text(value) or ''
    text = text.casefold()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_title(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r'\s*([:;,.!?])\s*', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\.+$', '', text).strip()
    return text or None


def clean_venue(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\s+', ' ', text).strip(' .')
    return text or None


def _join_openalex_inverted_index(payload: dict) -> str | None:
    positions: list[tuple[int, str]] = []
    for token, offsets in payload.items():
        if not isinstance(offsets, list):
            continue
        for pos in offsets:
            if isinstance(pos, int):
                positions.append((pos, token))
    if not positions:
        return None
    positions.sort(key=lambda x: x[0])
    text = ' '.join(token for _, token in positions)
    return clean_text(text)


def clean_abstract(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    if text.startswith('{') and text.endswith('}'):
        try:
            payload = json.loads(text)
        except Exception:
            payload = None
        if isinstance(payload, dict):
            joined = _join_openalex_inverted_index(payload)
            if joined:
                return joined
    text = re.sub(r'\b(background|objective|methods|results|conclusion|conclusions)\b\s*:?\s*', lambda m: m.group(1).capitalize() + ': ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text or None
