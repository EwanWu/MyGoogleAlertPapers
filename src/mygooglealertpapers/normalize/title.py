from __future__ import annotations

import re
import unicodedata


def normalize_title(title: str | None) -> str | None:
    if not title:
        return None
    text = unicodedata.normalize("NFKC", title)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def make_title_key(title: str | None) -> str | None:
    normalized = normalize_title(title)
    if not normalized:
        return None
    key = normalized.casefold()
    key = re.sub(r"[^\w\s]", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    return key or None
