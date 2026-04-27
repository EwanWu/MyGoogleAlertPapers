from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from mygooglealertpapers.config import Settings
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.pipeline.enrich import ProviderIntent, _build_provider_intents


IDENTIFIER_QUERY_TYPES = {'doi', 'doi_batch', 'pmid', 'pmcid', 'arxiv_id'}


def _intent_key(intent: ProviderIntent) -> tuple[str, str, str]:
    return intent.provider, intent.query_type, intent.query_key


def _query_family(query_type: str) -> str:
    return 'identifier' if query_type in IDENTIFIER_QUERY_TYPES else 'title_search'


def _sorted_counter_rows(counter: Counter[tuple[str, str]] | Counter[str], *, key_names: tuple[str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        row: dict[str, Any] = {'count': count}
        if isinstance(key, tuple):
            for idx, name in enumerate(key_names):
                row[name] = key[idx]
        else:
            row[key_names[0]] = key
        rows.append(row)
    return rows


def render_enrichment_plan_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Enrichment plan snapshot ({summary['generated_from_db']})",
        '',
        f"- candidate_count: {summary['candidate_count']}",
        f"- provider_intent_count: {summary['provider_intent_count']}",
        f"- unique_intent_count: {summary['unique_intent_count']}",
        f"- duplicate_intent_count: {summary['duplicate_intent_count']}",
        f"- identifier_driven_intents: {summary['identifier_driven_intents']}",
        f"- title_search_intents: {summary['title_search_intents']}",
        f"- identifier_driven_unique_intents: {summary['identifier_driven_unique_intents']}",
        f"- title_search_unique_intents: {summary['title_search_unique_intents']}",
        '',
        '## Provider breakdown',
        '',
        '| provider | total_intents | unique_intents | duplicate_intents |',
        '| --- | ---: | ---: | ---: |',
    ]
    for row in summary['provider_breakdown']:
        lines.append(f"| {row['provider']} | {row['total_intents']} | {row['unique_intents']} | {row['duplicate_intents']} |")
    lines.extend([
        '',
        '## Query-type breakdown',
        '',
        '| provider | query_type | total_intents | unique_intents |',
        '| --- | --- | ---: | ---: |',
    ])
    for row in summary['provider_query_type_breakdown']:
        lines.append(f"| {row['provider']} | {row['query_type']} | {row['total_intents']} | {row['unique_intents']} |")
    return '\n'.join(lines) + '\n'


def build_enrichment_plan(settings: Settings, *, limit: int = 100, output_path: Path | None = None) -> dict[str, Any]:
    repo = Repository(settings.sqlite_path)
    with repo.connect() as conn:
        rows = conn.execute(
            '''
            SELECT pcn.candidate_id, pcn.norm_title, pcn.doi_extracted, pcn.pmid_extracted,
                   pcn.arxiv_id_extracted, pcn.first_author_family, pcn.venue_guess, pcn.year_guess
            FROM paper_candidate_normalized pcn
            ORDER BY pcn.id ASC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()

    all_intents: list[ProviderIntent] = []
    for row in rows:
        all_intents.extend(_build_provider_intents(settings, row))

    unique_intents: dict[tuple[str, str, str], ProviderIntent] = {}
    for intent in all_intents:
        unique_intents.setdefault(_intent_key(intent), intent)
    deduped_intents = list(unique_intents.values())

    provider_total_counter: Counter[str] = Counter(intent.provider for intent in all_intents)
    provider_unique_counter: Counter[str] = Counter(intent.provider for intent in deduped_intents)
    provider_query_total_counter: Counter[tuple[str, str]] = Counter((intent.provider, intent.query_type) for intent in all_intents)
    provider_query_unique_counter: Counter[tuple[str, str]] = Counter((intent.provider, intent.query_type) for intent in deduped_intents)

    provider_breakdown = []
    for provider, total_intents in sorted(provider_total_counter.items(), key=lambda item: (-item[1], item[0])):
        unique_count = provider_unique_counter.get(provider, 0)
        provider_breakdown.append(
            {
                'provider': provider,
                'total_intents': total_intents,
                'unique_intents': unique_count,
                'duplicate_intents': total_intents - unique_count,
            }
        )

    provider_query_type_breakdown = []
    for (provider, query_type), total_intents in sorted(provider_query_total_counter.items(), key=lambda item: (-item[1], item[0])):
        provider_query_type_breakdown.append(
            {
                'provider': provider,
                'query_type': query_type,
                'query_family': _query_family(query_type),
                'total_intents': total_intents,
                'unique_intents': provider_query_unique_counter.get((provider, query_type), 0),
            }
        )

    summary: dict[str, Any] = {
        'generated_from_db': str(settings.sqlite_path),
        'candidate_count': len(rows),
        'provider_intent_count': len(all_intents),
        'unique_intent_count': len(deduped_intents),
        'duplicate_intent_count': len(all_intents) - len(deduped_intents),
        'identifier_driven_intents': sum(1 for intent in all_intents if _query_family(intent.query_type) == 'identifier'),
        'title_search_intents': sum(1 for intent in all_intents if _query_family(intent.query_type) == 'title_search'),
        'identifier_driven_unique_intents': sum(1 for intent in deduped_intents if _query_family(intent.query_type) == 'identifier'),
        'title_search_unique_intents': sum(1 for intent in deduped_intents if _query_family(intent.query_type) == 'title_search'),
        'provider_breakdown': provider_breakdown,
        'provider_query_type_breakdown': provider_query_type_breakdown,
        'query_family_breakdown': _sorted_counter_rows(Counter(_query_family(intent.query_type) for intent in all_intents), key_names=('query_family',)),
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() == '.json':
            output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        else:
            output_path.write_text(render_enrichment_plan_markdown(summary), encoding='utf-8')

    return summary
