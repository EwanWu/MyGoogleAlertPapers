from __future__ import annotations

import re

from mygooglealertpapers.normalize.text import clean_title


def normalize_title(title: str | None) -> str | None:
    return clean_title(title)


def make_title_key(title: str | None) -> str | None:
    normalized = normalize_title(title)
    if not normalized:
        return None
    key = normalized.casefold()
    key = re.sub(r"[^\w\s]", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    return key or None
