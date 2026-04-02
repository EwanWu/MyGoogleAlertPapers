from __future__ import annotations

import json


def authors_to_json(raw_authors: str | None) -> str | None:
    if not raw_authors:
        return None
    parts = [p.strip() for p in raw_authors.split(',') if p.strip()]
    return json.dumps(parts, ensure_ascii=False) if parts else None


def first_author_family(raw_authors: str | None) -> str | None:
    if not raw_authors:
        return None
    first = raw_authors.split(',')[0].strip()
    if not first:
        return None
    tokens = first.split()
    return tokens[-1] if tokens else None
