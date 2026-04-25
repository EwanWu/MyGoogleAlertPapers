from __future__ import annotations

from mygooglealertpapers.normalize.text import clean_title, comparison_text


def normalize_title(title: str | None) -> str | None:
    return clean_title(title)


def make_title_key(title: str | None) -> str | None:
    normalized = normalize_title(title)
    if not normalized:
        return None
    key = comparison_text(normalized)
    return key or None
