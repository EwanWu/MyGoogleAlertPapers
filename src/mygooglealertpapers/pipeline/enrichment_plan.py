from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mygooglealertpapers.config import Settings
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.pipeline.enrich import ProviderIntent, _build_provider_intents


IDENTIFIER_QUERY_TYPES = {'doi', 'doi_batch', 'pmid', 'pmcid', 'arxiv_id'}
BATCH_CAPABILITIES: dict[tuple[str, str], dict[str, Any]] = {
    ('openalex', 'doi'): {
        'batch_size': 50,
        'mode': 'batch_after_dedup',
        'note': 'Batch DOI lookups after dedup to match the current OpenAlex multi-DOI fetch path.',
    },
}
TOP_DUPLICATE_GROUP_LIMIT = 10


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


def _recommendation_row(provider: str, query_type: str, total_intents: int, unique_intents: int) -> dict[str, Any]:
    duplicate_intents = total_intents - unique_intents
    capability = BATCH_CAPABILITIES.get((provider, query_type))
    batch_size = int(capability['batch_size']) if capability else None
    recommended_execution_mode = str(capability['mode']) if capability else 'dedup_only'
    recommended_request_count = math.ceil(unique_intents / batch_size) if batch_size else unique_intents
    request_savings_vs_naive = total_intents - recommended_request_count
    request_savings_vs_dedup_only = unique_intents - recommended_request_count
    row = {
        'provider': provider,
        'query_type': query_type,
        'query_family': _query_family(query_type),
        'total_intents': total_intents,
        'unique_intents': unique_intents,
        'duplicate_intents': duplicate_intents,
        'recommended_execution_mode': recommended_execution_mode,
        'batch_size': batch_size,
        'recommended_request_count': recommended_request_count,
        'request_savings_vs_naive': request_savings_vs_naive,
        'request_savings_vs_dedup_only': request_savings_vs_dedup_only,
        'note': capability['note'] if capability else 'Dedup repeated query keys before dispatching provider requests.',
    }
    return row


def _build_execution_recommendations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (-item['request_savings_vs_naive'], item['provider'], item['query_type'])):
        if row['request_savings_vs_naive'] <= 0:
            continue
        recommendation = {
            'provider': row['provider'],
            'query_type': row['query_type'],
            'recommended_execution_mode': row['recommended_execution_mode'],
            'recommended_request_count': row['recommended_request_count'],
            'request_savings_vs_naive': row['request_savings_vs_naive'],
            'request_savings_vs_dedup_only': row['request_savings_vs_dedup_only'],
            'summary': (
                f"{row['provider']} {row['query_type']}: "
                f"{row['total_intents']} intents -> {row['recommended_request_count']} recommended request(s)"
            ),
            'note': row['note'],
        }
        recommendations.append(recommendation)
    return recommendations


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
        f"- dedup_only_request_count: {summary['dedup_only_request_count']}",
        f"- recommended_request_count: {summary['recommended_request_count']}",
        f"- request_savings_vs_naive: {summary['request_savings_vs_naive']}",
        f"- request_savings_vs_dedup_only: {summary['request_savings_vs_dedup_only']}",
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
    lines.extend([
        '',
        '## Execution recommendations',
        '',
        '| provider | query_type | mode | total_intents | unique_intents | recommended_request_count | savings_vs_naive | savings_vs_dedup_only |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |',
    ])
    for row in summary['request_strategy_breakdown']:
        lines.append(
            f"| {row['provider']} | {row['query_type']} | {row['recommended_execution_mode']} | {row['total_intents']} | {row['unique_intents']} | {row['recommended_request_count']} | {row['request_savings_vs_naive']} | {row['request_savings_vs_dedup_only']} |"
        )
    if summary['top_duplicate_query_groups']:
        lines.extend([
            '',
            '## Top duplicate query groups',
            '',
            '| provider | query_type | query_key | candidate_count | extra_intents |',
            '| --- | --- | --- | ---: | ---: |',
        ])
        for row in summary['top_duplicate_query_groups']:
            lines.append(
                f"| {row['provider']} | {row['query_type']} | {row['query_key']} | {row['candidate_count']} | {row['extra_intents']} |"
            )
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
    grouped_candidate_ids: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for intent in all_intents:
        key = _intent_key(intent)
        unique_intents.setdefault(key, intent)
        grouped_candidate_ids[key].append(intent.candidate_id)
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
    request_strategy_breakdown = []
    for (provider, query_type), total_intents in sorted(provider_query_total_counter.items(), key=lambda item: (-item[1], item[0])):
        unique_count = provider_query_unique_counter.get((provider, query_type), 0)
        provider_query_type_breakdown.append(
            {
                'provider': provider,
                'query_type': query_type,
                'query_family': _query_family(query_type),
                'total_intents': total_intents,
                'unique_intents': unique_count,
            }
        )
        request_strategy_breakdown.append(_recommendation_row(provider, query_type, total_intents, unique_count))

    request_strategy_breakdown.sort(key=lambda item: (-item['request_savings_vs_naive'], item['provider'], item['query_type']))
    top_duplicate_query_groups = [
        {
            'provider': provider,
            'query_type': query_type,
            'query_key': query_key,
            'candidate_count': len(candidate_ids),
            'extra_intents': len(candidate_ids) - 1,
            'candidate_ids': candidate_ids,
        }
        for (provider, query_type, query_key), candidate_ids in sorted(
            grouped_candidate_ids.items(),
            key=lambda item: (-(len(item[1]) - 1), item[0]),
        )
        if len(candidate_ids) > 1
    ][:TOP_DUPLICATE_GROUP_LIMIT]

    recommended_request_count = sum(row['recommended_request_count'] for row in request_strategy_breakdown)
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
        'dedup_only_request_count': len(deduped_intents),
        'recommended_request_count': recommended_request_count,
        'request_savings_vs_naive': len(all_intents) - recommended_request_count,
        'request_savings_vs_dedup_only': len(deduped_intents) - recommended_request_count,
        'provider_breakdown': provider_breakdown,
        'provider_query_type_breakdown': provider_query_type_breakdown,
        'query_family_breakdown': _sorted_counter_rows(Counter(_query_family(intent.query_type) for intent in all_intents), key_names=('query_family',)),
        'request_strategy_breakdown': request_strategy_breakdown,
        'execution_recommendations': _build_execution_recommendations(request_strategy_breakdown),
        'top_duplicate_query_groups': top_duplicate_query_groups,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() == '.json':
            output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        else:
            output_path.write_text(render_enrichment_plan_markdown(summary), encoding='utf-8')

    return summary
