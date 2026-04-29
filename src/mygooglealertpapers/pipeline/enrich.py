from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.enrich.base import cache_metadata_from_record, cache_status_from_record, enrichment_record_from_json, enrichment_record_to_json
from mygooglealertpapers.enrich.crossref import build_crossref_record, fetch_crossref_title_item, query_crossref
from mygooglealertpapers.enrich.openalex import _extract_primary_location_fields, build_openalex_record, fetch_openalex_title_item, query_openalex, query_openalex_batch_by_doi
from mygooglealertpapers.enrich.pubmed import query_pubmed
from mygooglealertpapers.enrich.semanticscholar import build_semanticscholar_record, fetch_semanticscholar_title_item, query_semanticscholar
from mygooglealertpapers.enrich.europepmc import query_europepmc
from mygooglealertpapers.enrich.arxiv import query_arxiv
from mygooglealertpapers.enrich.unpaywall import query_unpaywall
from mygooglealertpapers.pipeline.candidate_resolution import (
    cluster_candidates_within_batch,
    library_prelink_enabled,
    prelink_candidates_against_library,
)

logger = logging.getLogger(__name__)

PROGRESS_EVERY = 25
IDENTIFIER_QUERY_TYPES = {'doi', 'doi_batch', 'pmid', 'pmcid', 'arxiv_id'}
DEFAULT_LANE_ORDER = ['identifier_fastpath', 'title_core', 'biomedical_fallback', 'slow_fallback']


@dataclass(slots=True)
class ProviderIntent:
    candidate_id: str
    provider: str
    query_type: str
    query_key: str
    norm_title: str | None
    doi: str | None
    pmid: str | None
    arxiv_id: str | None
    first_author_family: str | None
    venue_guess: str | None
    year_guess: str | None


@dataclass(slots=True)
class DispatchGroup:
    representative: ProviderIntent
    intents: list[ProviderIntent]

    @property
    def provider(self) -> str:
        return self.representative.provider

    @property
    def query_type(self) -> str:
        return self.representative.query_type

    @property
    def query_key(self) -> str:
        return self.representative.query_key


def _clone_intent_for_candidate(intent: ProviderIntent, candidate_id: str) -> ProviderIntent:
    return ProviderIntent(
        candidate_id=candidate_id,
        provider=intent.provider,
        query_type=intent.query_type,
        query_key=intent.query_key,
        norm_title=intent.norm_title,
        doi=intent.doi,
        pmid=intent.pmid,
        arxiv_id=intent.arxiv_id,
        first_author_family=intent.first_author_family,
        venue_guess=intent.venue_guess,
        year_guess=intent.year_guess,
    )


def _build_same_batch_clustered_intents(
    settings: Settings,
    rows: list,
    cluster_summary: dict[str, object],
) -> list[ProviderIntent]:
    follower_to_leader = dict(cluster_summary.get('follower_to_leader') or {})
    leader_to_followers = dict(cluster_summary.get('leader_to_followers') or {})
    intents: list[ProviderIntent] = []
    for row in rows:
        candidate_id = row[0]
        if candidate_id in follower_to_leader:
            continue
        leader_intents = _build_provider_intents(settings, row[:8])
        intents.extend(leader_intents)
        for follower_candidate_id in leader_to_followers.get(candidate_id, []):
            intents.extend(_clone_intent_for_candidate(intent, follower_candidate_id) for intent in leader_intents)
    return intents


def _canonical_query_key(query_type: str, value: str | None) -> str:
    if not value:
        return ''
    text = value.strip()
    if query_type in {'doi', 'doi_batch'}:
        text = text.lower()
        if text.startswith('https://doi.org/'):
            text = text[len('https://doi.org/'):]
        return text
    if query_type in {'pmid', 'pmcid'}:
        return text
    if query_type == 'title':
        return ' '.join(text.split())
    return text


def _looks_biomedical(venue_guess: str | None, norm_title: str | None) -> bool:
    hay = ' '.join(x for x in [venue_guess, norm_title] if x).casefold()
    biomedical_tokens = [
        'mri', 'magnetic resonance', 'stroke', 'brain', 'cerebral', 'neurolog', 'radiolog',
        'cardio', 'vascular', 'medic', 'clinical', 'neuro', 'oncolog', 'disease', 'patient',
    ]
    return any(tok in hay for tok in biomedical_tokens)


def _is_arxiv_native(arxiv_id: str | None, norm_title: str | None) -> bool:
    if arxiv_id:
        return True
    return bool(norm_title and 'arxiv' in norm_title.casefold())


def _provider_enabled(settings: Settings, provider: str, default: bool = True) -> bool:
    return settings.policy_profile.provider_enabled(provider, default)


def _provider_value(settings: Settings, provider: str, key: str, default: object = None) -> object:
    return settings.policy_profile.provider_value(provider, key, default)


def _runtime_value(settings: Settings, key: str, default: object = None) -> object:
    return settings.policy_profile.runtime_value(key, default)


def _lane_for_group(group: DispatchGroup) -> str:
    provider = group.provider
    query_type = group.query_type
    if provider == 'semanticscholar':
        return 'slow_fallback'
    if query_type in IDENTIFIER_QUERY_TYPES:
        return 'identifier_fastpath'
    if provider in {'crossref', 'openalex', 'arxiv'}:
        return 'title_core'
    if provider in {'pubmed', 'europepmc'}:
        return 'biomedical_fallback'
    return 'slow_fallback'


def _lane_order(settings: Settings) -> list[str]:
    value = _runtime_value(settings, 'lane_order', DEFAULT_LANE_ORDER)
    if isinstance(value, list) and value:
        return [str(x) for x in value]
    return list(DEFAULT_LANE_ORDER)


def _enabled_lanes(settings: Settings) -> set[str] | None:
    value = _runtime_value(settings, 'enabled_lanes', None)
    if value in (None, [], ()):
        return None
    if isinstance(value, (list, tuple, set)):
        return {str(x) for x in value}
    return {str(value)}


def _lane_request_budgets(settings: Settings) -> dict[str, int]:
    value = _runtime_value(settings, 'lane_request_budgets', {})
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for lane, budget in value.items():
        if budget in (None, ''):
            continue
        result[str(lane)] = int(budget)
    return result


def _lane_runtime_budget_seconds(settings: Settings) -> dict[str, float]:
    value = _runtime_value(settings, 'lane_runtime_budget_seconds', {})
    if not isinstance(value, dict):
        return {}
    result: dict[str, float] = {}
    for lane, budget in value.items():
        if budget in (None, ''):
            continue
        result[str(lane)] = float(budget)
    return result


def _refresh_lane_elapsed(dispatch_stats: dict[str, object], lane_runtime_state: dict[str, dict[str, float] | str | None]) -> None:
    lane_started_at = lane_runtime_state.get('lane_started_at', {})
    lane_ended_at = lane_runtime_state.get('lane_ended_at', {})
    now = time.perf_counter()
    dispatch_stats['lane_elapsed_ms'] = {
        lane: int(((lane_ended_at.get(lane) or now) - started_at) * 1000)
        for lane, started_at in lane_started_at.items()
    }


def _record_lane_stop(dispatch_stats: dict[str, object], lane: str, reason: str) -> str:
    stop_reasons = dispatch_stats.setdefault('lane_stop_reasons', {})
    stop_reasons.setdefault(lane, reason)
    return stop_reasons[lane]


def _record_lane_skip(dispatch_stats: dict[str, object], group: DispatchGroup, *, reason: str) -> None:
    lane = _lane_for_group(group)
    skipped_groups = dispatch_stats.setdefault('lane_skipped_group_count', {})
    skipped_intents = dispatch_stats.setdefault('lane_skipped_intents', {})
    skip_reasons = dispatch_stats.setdefault('lane_skip_reasons', {})
    skipped_groups[lane] = int(skipped_groups.get(lane, 0) or 0) + 1
    skipped_intents[lane] = int(skipped_intents.get(lane, 0) or 0) + len(group.intents)
    skip_reasons.setdefault(lane, reason)


def _lane_budget_stop_reason(
    settings: Settings,
    dispatch_stats: dict[str, object],
    lane_runtime_state: dict[str, dict[str, float] | str | None],
    lane: str,
    *,
    next_request_cost: int = 1,
) -> str | None:
    existing = (dispatch_stats.get('lane_stop_reasons') or {}).get(lane)
    if existing:
        return str(existing)

    request_budgets = _lane_request_budgets(settings)
    current_requests = int((dispatch_stats.get('lane_dispatch_request_count') or {}).get(lane, 0) or 0)
    request_budget = request_budgets.get(lane)
    if request_budget is not None and current_requests + next_request_cost > request_budget:
        lane_ended_at = lane_runtime_state.setdefault('lane_ended_at', {})
        if isinstance(lane_ended_at, dict):
            lane_ended_at.setdefault(lane, time.perf_counter())
        return _record_lane_stop(dispatch_stats, lane, 'request_budget_exhausted')

    runtime_budgets = _lane_runtime_budget_seconds(settings)
    runtime_budget = runtime_budgets.get(lane)
    lane_started_at = lane_runtime_state.get('lane_started_at', {}).get(lane)
    if runtime_budget is not None and lane_started_at is not None:
        if (time.perf_counter() - lane_started_at) >= runtime_budget:
            lane_ended_at = lane_runtime_state.setdefault('lane_ended_at', {})
            if isinstance(lane_ended_at, dict):
                lane_ended_at.setdefault(lane, time.perf_counter())
            return _record_lane_stop(dispatch_stats, lane, 'runtime_budget_exhausted')

    return None


def _mark_lane_request_started(lane_runtime_state: dict[str, dict[str, float] | str | None], lane: str) -> None:
    now = time.perf_counter()
    active_lane = lane_runtime_state.get('active_lane')
    lane_ended_at = lane_runtime_state.setdefault('lane_ended_at', {})
    if isinstance(active_lane, str) and active_lane != lane and isinstance(lane_ended_at, dict):
        lane_ended_at.setdefault(active_lane, now)
    lane_started_at = lane_runtime_state.setdefault('lane_started_at', {})
    if isinstance(lane_started_at, dict):
        lane_started_at.setdefault(lane, now)
    lane_runtime_state['active_lane'] = lane


def _prepare_dispatch_groups(settings: Settings, runnable_intents: list[ProviderIntent]) -> tuple[list[DispatchGroup], dict[str, int], dict[str, int]]:
    base_groups = _build_dispatch_groups(settings, runnable_intents)
    enabled_lanes = _enabled_lanes(settings)
    lane_order = _lane_order(settings)
    known_lanes = list(dict.fromkeys([*lane_order, *DEFAULT_LANE_ORDER]))
    lane_groups: dict[str, list[DispatchGroup]] = {lane: [] for lane in known_lanes}

    for group in base_groups:
        lane = _lane_for_group(group)
        if enabled_lanes is not None and lane not in enabled_lanes:
            continue
        lane_groups.setdefault(lane, []).append(group)

    ordered_groups: list[DispatchGroup] = []
    seen_lanes: set[str] = set()
    for lane in lane_order:
        ordered_groups.extend(lane_groups.get(lane, []))
        seen_lanes.add(lane)
    for lane, groups in lane_groups.items():
        if lane in seen_lanes:
            continue
        ordered_groups.extend(groups)

    lane_group_counts = {lane: len(groups) for lane, groups in lane_groups.items() if groups}
    lane_intent_counts = {lane: sum(len(group.intents) for group in groups) for lane, groups in lane_groups.items() if groups}
    return ordered_groups, lane_group_counts, lane_intent_counts


def _bump_lane_processed(dispatch_stats: dict[str, object], group: DispatchGroup, delta: int) -> None:
    lane = _lane_for_group(group)
    lane_processed = dispatch_stats.setdefault('lane_processed_intents', {})
    lane_processed[lane] = int(lane_processed.get(lane, 0) or 0) + delta


def _bump_lane_request(dispatch_stats: dict[str, object], lane: str, delta: int = 1) -> None:
    lane_requests = dispatch_stats.setdefault('lane_dispatch_request_count', {})
    lane_requests[lane] = int(lane_requests.get(lane, 0) or 0) + delta


def _build_provider_intents(settings: Settings, row) -> list[ProviderIntent]:
    candidate_id, norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess = row
    intents: list[ProviderIntent] = []
    if doi or norm_title:
        query_type = 'doi' if doi else 'title'
        query_key = _canonical_query_key(query_type, doi or norm_title)
        for provider in ['crossref', 'openalex', 'semanticscholar']:
            if _provider_enabled(settings, provider, True):
                intents.append(
                    ProviderIntent(candidate_id, provider, query_type, query_key, norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
                )

    is_biomedical = _looks_biomedical(venue_guess, norm_title)
    if _provider_enabled(settings, 'pubmed', True):
        if pmid:
            intents.append(
                ProviderIntent(candidate_id, 'pubmed', 'pmid', _canonical_query_key('pmid', pmid), norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
            )
        elif norm_title and not doi and is_biomedical:
            intents.append(
                ProviderIntent(candidate_id, 'pubmed', 'title', _canonical_query_key('title', norm_title), norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
            )

    if _provider_enabled(settings, 'europepmc', True):
        europepmc_trigger_mode = str(_provider_value(settings, 'europepmc', 'trigger_mode', 'narrowed_biomedical_fallback') or 'narrowed_biomedical_fallback')
        if pmid:
            intents.append(
                ProviderIntent(candidate_id, 'europepmc', 'pmid', _canonical_query_key('pmid', pmid), norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
            )
        elif norm_title and is_biomedical:
            allow_title_fallback = not doi and europepmc_trigger_mode in {'narrowed_biomedical_fallback', 'broad_biomedical'}
            allow_doi_biomedical = bool(doi) and europepmc_trigger_mode == 'broad_biomedical'
            if allow_title_fallback or allow_doi_biomedical:
                query_type = 'doi' if allow_doi_biomedical and doi else 'title'
                query_key = _canonical_query_key(query_type, doi if query_type == 'doi' else norm_title)
                intents.append(
                    ProviderIntent(candidate_id, 'europepmc', query_type, query_key, norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
                )

    if _provider_enabled(settings, 'arxiv', True):
        arxiv_trigger_mode = str(_provider_value(settings, 'arxiv', 'trigger_mode', 'arxiv_native_only') or 'arxiv_native_only')
        should_run_arxiv = _is_arxiv_native(arxiv_id, norm_title) if arxiv_trigger_mode == 'arxiv_native_only' else bool(arxiv_id or norm_title)
        if should_run_arxiv:
            arxiv_query_type = 'arxiv_id' if arxiv_id else 'title'
            arxiv_query_key = _canonical_query_key(arxiv_query_type if arxiv_query_type != 'arxiv_id' else 'title', arxiv_id or norm_title)
            intents.append(
                ProviderIntent(candidate_id, 'arxiv', arxiv_query_type, arxiv_query_key, norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
            )

    if _provider_enabled(settings, 'unpaywall', False):
        if doi:
            intents.append(
                ProviderIntent(candidate_id, 'unpaywall', 'doi', _canonical_query_key('doi', doi), norm_title, doi, pmid, arxiv_id, first_author_family, venue_guess, year_guess)
            )

    return intents


def _should_run_provider(repo: Repository, conn, intent: ProviderIntent) -> bool:
    status_row = repo.get_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider)
    if status_row is None:
        repo.bootstrap_enrichment_status_from_source_record(conn, candidate_id=intent.candidate_id, provider=intent.provider)
        status_row = repo.get_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider)
    if status_row is None:
        return True
    status = status_row[1]
    return status == 'error'


def _record_from_cache(intent: ProviderIntent, payload: str):
    rec = enrichment_record_from_json(payload)
    return type(rec)(
        candidate_id=intent.candidate_id,
        source_name=rec.source_name,
        query_type=rec.query_type,
        query_string=rec.query_string,
        matched=rec.matched,
        match_score=rec.match_score,
        external_id=rec.external_id,
        title=rec.title,
        authors_json=rec.authors_json,
        abstract=rec.abstract,
        venue=rec.venue,
        year=rec.year,
        publication_type=rec.publication_type,
        doi=rec.doi,
        pmid=rec.pmid,
        pmcid=rec.pmcid,
        url=rec.url,
        raw_payload_json=rec.raw_payload_json,
        latency_ms=0,
    )


def _clone_record_for_candidate(rec, candidate_id: str, *, latency_ms: int | None = None):
    return type(rec)(
        candidate_id=candidate_id,
        source_name=rec.source_name,
        query_type=rec.query_type,
        query_string=rec.query_string,
        matched=rec.matched,
        match_score=rec.match_score,
        external_id=rec.external_id,
        title=rec.title,
        authors_json=rec.authors_json,
        abstract=rec.abstract,
        venue=rec.venue,
        year=rec.year,
        publication_type=rec.publication_type,
        doi=rec.doi,
        pmid=rec.pmid,
        pmcid=rec.pmcid,
        url=rec.url,
        raw_payload_json=rec.raw_payload_json,
        latency_ms=rec.latency_ms if latency_ms is None else latency_ms,
    )


def _insert_source_record(repo: Repository, conn, rec) -> int:
    repo.insert_source_record(conn, rec)
    return conn.execute('SELECT last_insert_rowid()').fetchone()[0]


def _dispatch_signature(intent: ProviderIntent) -> tuple[object, ...]:
    return (
        intent.provider,
        intent.query_type,
        intent.query_key,
        intent.norm_title,
        intent.doi,
        intent.pmid,
        intent.arxiv_id,
        intent.first_author_family,
        intent.venue_guess,
        intent.year_guess,
    )


def _cache_field_set_hash(intent: ProviderIntent) -> str:
    if intent.query_type in IDENTIFIER_QUERY_TYPES:
        return 'default'
    payload = {
        'query_type': intent.query_type,
        'norm_title': intent.norm_title or '',
        'doi': intent.doi or '',
        'pmid': intent.pmid or '',
        'arxiv_id': intent.arxiv_id or '',
        'first_author_family': intent.first_author_family or '',
        'venue_guess': intent.venue_guess or '',
        'year_guess': intent.year_guess or '',
    }
    digest = hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return f'ctx_{digest[:16]}'


def _build_dispatch_groups(settings: Settings, runnable_intents: list[ProviderIntent]) -> list[DispatchGroup]:
    grouped: dict[tuple[str, str, str], list[ProviderIntent]] = {}
    ordered_keys: list[tuple[str, str, str]] = []
    for intent in runnable_intents:
        key = (intent.provider, intent.query_type, intent.query_key)
        if key not in grouped:
            grouped[key] = []
            ordered_keys.append(key)
        grouped[key].append(intent)

    dispatch_groups: list[DispatchGroup] = []
    for key in ordered_keys:
        intents = grouped[key]
        representative = intents[0]
        if len(intents) == 1:
            dispatch_groups.append(DispatchGroup(representative=representative, intents=intents))
            continue
        if representative.query_type == 'title' and _provider_title_payload_reuse_enabled(settings, representative.provider):
            dispatch_groups.append(DispatchGroup(representative=representative, intents=intents))
            continue
        dedup_safe = representative.query_type in IDENTIFIER_QUERY_TYPES or len({_dispatch_signature(intent) for intent in intents}) == 1
        if dedup_safe:
            dispatch_groups.append(DispatchGroup(representative=representative, intents=intents))
        else:
            for intent in intents:
                dispatch_groups.append(DispatchGroup(representative=intent, intents=[intent]))
    return dispatch_groups


def _start_group_statuses(repo: Repository, conn, group: DispatchGroup, *, query_type_override: str | None = None, notes: str | None = None) -> None:
    for intent in group.intents:
        repo.start_enrichment_status(
            conn,
            candidate_id=intent.candidate_id,
            provider=intent.provider,
            query_type=query_type_override or intent.query_type,
            query_key=intent.query_key,
            notes=notes,
        )


def _fanout_records_to_group(repo: Repository, tracker: CostTracker, conn, group: DispatchGroup, records: list, *, cache_hit: bool, notes: str | None = None) -> int:
    for idx, (intent, rec) in enumerate(zip(group.intents, records, strict=True)):
        status = 'ok' if rec.matched else 'no_match'
        emitted_rec = _clone_record_for_candidate(rec, intent.candidate_id, latency_ms=0 if cache_hit or idx > 0 else rec.latency_ms)
        source_record_id = _insert_source_record(repo, conn, emitted_rec)
        repo.finish_enrichment_status(
            conn,
            candidate_id=intent.candidate_id,
            provider=intent.provider,
            status=status,
            source_record_id=source_record_id,
            cache_hit=cache_hit,
            latency_ms=emitted_rec.latency_ms,
            notes=notes,
        )
        tracker.record_stage_cost(
            conn,
            stage='enrich_candidates',
            status='cache_hit' if cache_hit else status,
            candidate_id=intent.candidate_id,
            provider=intent.provider,
            latency_ms=emitted_rec.latency_ms,
            notes=notes,
        )
    return len(records)


def _fanout_result_to_group(repo: Repository, tracker: CostTracker, conn, group: DispatchGroup, rec, *, cache_hit: bool, notes: str | None = None) -> int:
    return _fanout_records_to_group(repo, tracker, conn, group, [rec for _ in group.intents], cache_hit=cache_hit, notes=notes)


def _persist_dispatch_progress(repo: Repository, conn, *, run_id: str, started_at: float, processed_intents: int, dispatch_stats: dict[str, object]) -> None:
    payload = dict(dispatch_stats)
    payload['dispatch_request_count'] = payload.get('openalex_batch_request_count', 0) + payload.get('non_batch_dispatch_request_count', 0)
    payload['request_savings_vs_runnable_intents'] = payload.get('runnable_provider_intents', 0) - payload['dispatch_request_count']
    payload['processed_runnable_intents'] = processed_intents
    repo.update_batch_run_progress(
        conn,
        run_id=run_id,
        duration_ms=int((time.perf_counter() - started_at) * 1000),
        processed_count=processed_intents,
        notes=json.dumps(payload, ensure_ascii=False),
    )


def _fanout_error_to_group(repo: Repository, tracker: CostTracker, conn, group: DispatchGroup, *, error_summary: str, notes: str | None = None) -> int:
    for intent in group.intents:
        repo.finish_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider, status='error', latency_ms=0, error_summary=error_summary, notes=notes)
        tracker.record_stage_cost(conn, stage='enrich_candidates', status='error', candidate_id=intent.candidate_id, provider=intent.provider, latency_ms=0, notes=notes or error_summary)
    return len(group.intents)


def _group_field_set_hash(group: DispatchGroup) -> str:
    return _cache_field_set_hash(group.representative)


def _provider_title_payload_reuse_enabled(settings: Settings, provider: str) -> bool:
    return bool(_provider_value(settings, provider, 'title_payload_reuse_enabled', False))


def _build_title_reused_records(settings: Settings, group: DispatchGroup):
    title = group.representative.norm_title
    if not title:
        return None
    provider = group.provider
    if provider == 'crossref':
        item, raw_payload_json, latency_ms = fetch_crossref_title_item(title, mailto=settings.crossref_mailto)
        return [
            build_crossref_record(
                intent.candidate_id,
                query_type='title',
                query_string=title,
                doi=intent.doi,
                item=item,
                raw_payload_json=raw_payload_json,
                latency_ms=latency_ms,
                first_author_family=intent.first_author_family,
                venue_hint=intent.venue_guess,
                query_year=intent.year_guess,
            )
            for intent in group.intents
        ]
    if provider == 'openalex':
        item, raw_payload_json, latency_ms = fetch_openalex_title_item(title, email=settings.openalex_email)
        return [
            build_openalex_record(
                intent.candidate_id,
                query_type='title',
                query_string=title,
                doi=intent.doi,
                item=item,
                raw_payload_json=raw_payload_json,
                latency_ms=latency_ms,
                first_author_family=intent.first_author_family,
                venue_hint=intent.venue_guess,
                query_year=intent.year_guess,
            )
            for intent in group.intents
        ]
    if provider == 'semanticscholar':
        item, raw_payload_json, latency_ms = fetch_semanticscholar_title_item(title, api_key=settings.semantic_scholar_api_key)
        return [
            build_semanticscholar_record(
                intent.candidate_id,
                query_type='title',
                query_string=title,
                doi=intent.doi,
                item=item,
                raw_payload_json=raw_payload_json,
                latency_ms=latency_ms,
                first_author_family=intent.first_author_family,
                venue_hint=intent.venue_guess,
                query_year=intent.year_guess,
            )
            for intent in group.intents
        ]
    return None


def _execute_provider_query(settings: Settings, intent: ProviderIntent):
    if intent.provider == 'pubmed':
        return query_pubmed(intent.candidate_id, pmid=intent.pmid, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, candidate_doi=intent.doi)
    if intent.provider == 'europepmc':
        return query_europepmc(intent.candidate_id, doi=intent.doi, pmid=intent.pmid, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess)
    if intent.provider == 'arxiv':
        return query_arxiv(intent.candidate_id, arxiv_id=intent.arxiv_id, title=intent.norm_title if intent.query_type == 'title' else None, first_author_family=intent.first_author_family, query_year=intent.year_guess)
    if intent.provider == 'semanticscholar':
        return query_semanticscholar(intent.candidate_id, doi=intent.doi, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, api_key=settings.semantic_scholar_api_key)
    if intent.provider == 'crossref':
        return query_crossref(intent.candidate_id, doi=intent.doi, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, mailto=settings.crossref_mailto)
    if intent.provider == 'openalex':
        return query_openalex(intent.candidate_id, doi=intent.doi, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, email=settings.openalex_email)
    if intent.provider == 'unpaywall':
        return query_unpaywall(intent.candidate_id, doi=intent.doi, email=settings.unpaywall_email)
    return None


def enrich_candidates(settings: Settings, *, limit: int) -> None:
    repo = Repository(settings.sqlite_path)
    tracker = CostTracker(repo, settings.sqlite_path)
    run_id = 'enrich_candidates_' + uuid.uuid4().hex[:12]
    started_at = time.perf_counter()
    with repo.connect() as conn:
        repo.start_batch_run(conn, run_id=run_id, stage='enrich_candidates', requested_limit=limit, notes=None)
        rows = conn.execute(
            '''
            SELECT pcn.candidate_id, pcn.norm_title, pcn.doi_extracted, pcn.pmid_extracted,
                   pcn.arxiv_id_extracted, pcn.first_author_family, pcn.venue_guess, pcn.year_guess,
                   pcn.pmcid_extracted, pcn.url_canonical, pcn.scholar_cluster_hint
            FROM paper_candidate_normalized pcn
            LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id
            WHERE cpl.id IS NULL
            ORDER BY pcn.id ASC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()

        all_intents: list[ProviderIntent] = []
        for row in rows:
            all_intents.extend(_build_provider_intents(settings, row[:8]))

        prelink_summary = prelink_candidates_against_library(settings, repo, tracker, conn, rows)
        prelinked_candidate_ids = set(prelink_summary['prelinked_candidate_ids'])
        unresolved_rows = [row for row in rows if row[0] not in prelinked_candidate_ids]

        naive_unresolved_intents: list[ProviderIntent] = []
        for row in unresolved_rows:
            naive_unresolved_intents.extend(_build_provider_intents(settings, row[:8]))

        cluster_summary = cluster_candidates_within_batch(settings, repo, conn, unresolved_rows)
        unresolved_intents = _build_same_batch_clustered_intents(settings, unresolved_rows, cluster_summary)

        runnable_intents = [intent for intent in unresolved_intents if _should_run_provider(repo, conn, intent)]
        dispatch_groups, lane_group_counts, lane_intent_counts = _prepare_dispatch_groups(settings, runnable_intents)
        naive_dispatch_groups, _, _ = _prepare_dispatch_groups(settings, naive_unresolved_intents)
        clustered_dispatch_groups, _, _ = _prepare_dispatch_groups(settings, unresolved_intents)
        logger.info(
            'Planned %s provider intent(s); %s need work; %s dispatch group(s) after safe dedup; lanes=%s',
            len(all_intents),
            len(runnable_intents),
            len(dispatch_groups),
            lane_group_counts,
        )

        openalex_doi_batch_enabled = bool(_provider_value(settings, 'openalex', 'doi_batch_enabled', True))
        planned_provider_intents = len(all_intents)
        dispatch_stats = {
            'candidate_count': len(rows),
            'unresolved_candidate_count': len(unresolved_rows),
            'library_prelink_enabled': library_prelink_enabled(settings),
            'library_prelinked_candidate_count': prelink_summary['prelinked_candidate_count'],
            'library_prelink_rule_counts': prelink_summary['rule_counts'],
            'same_batch_clustering_enabled': bool(cluster_summary.get('enabled')),
            'same_batch_cluster_group_count': int(cluster_summary.get('cluster_group_count', 0) or 0),
            'same_batch_clustered_candidate_count': int(cluster_summary.get('clustered_candidate_count', 0) or 0),
            'same_batch_cluster_rule_counts': dict(cluster_summary.get('rule_counts') or {}),
            'same_batch_cluster_naive_group_count': len(naive_dispatch_groups),
            'same_batch_cluster_effective_group_count': len(clustered_dispatch_groups),
            'same_batch_cluster_group_savings_estimate': len(naive_dispatch_groups) - len(clustered_dispatch_groups),
            'planned_provider_intents': planned_provider_intents,
            'prelink_skipped_provider_intents': planned_provider_intents - len(naive_unresolved_intents),
            'unresolved_provider_intents': len(unresolved_intents),
            'runnable_provider_intents': len(runnable_intents),
            'dispatch_group_count': len(dispatch_groups),
            'lane_order': _lane_order(settings),
            'enabled_lanes': sorted(_enabled_lanes(settings)) if _enabled_lanes(settings) is not None else None,
            'lane_group_counts': lane_group_counts,
            'lane_intent_counts': lane_intent_counts,
            'lane_processed_intents': {lane: 0 for lane in lane_intent_counts},
            'lane_dispatch_request_count': {lane: 0 for lane in lane_group_counts},
            'lane_request_budgets': _lane_request_budgets(settings) or None,
            'lane_runtime_budget_seconds': _lane_runtime_budget_seconds(settings) or None,
            'lane_stop_reasons': {},
            'lane_skipped_group_count': {},
            'lane_skipped_intents': {},
            'lane_skip_reasons': {},
            'lane_elapsed_ms': {},
            'openalex_batch_request_count': 0,
            'non_batch_dispatch_request_count': 0,
            'cache_hit_group_count': 0,
            'fanout_candidate_count': sum(max(len(group.intents) - 1, 0) for group in dispatch_groups),
            'shared_title_reuse_group_count': 0,
            'shared_title_reuse_intent_count': 0,
            'shared_title_reuse_request_count': 0,
            'shared_title_reuse_request_savings': 0,
        }
        lane_runtime_state: dict[str, dict[str, float] | str | None] = {
            'lane_started_at': {},
            'lane_ended_at': {},
            'active_lane': None,
        }
        _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
        _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=0, dispatch_stats=dispatch_stats)
        conn.commit()
        openalex_doi_groups = [
            group for group in dispatch_groups
            if openalex_doi_batch_enabled and group.provider == 'openalex' and group.query_type == 'doi' and group.representative.doi
        ]
        handled_group_keys: set[tuple[str, str, str]] = set()
        processed_intents = 0

        if openalex_doi_groups:
            doi_to_group: dict[str, DispatchGroup] = {}
            for group in openalex_doi_groups:
                doi_val = (group.representative.doi or '').lower()
                if not doi_val:
                    continue
                doi_to_group[doi_val] = group
            doi_values = list(doi_to_group.keys())
            for i in range(0, len(doi_values), 50):
                chunk = doi_values[i:i + 50]
                lane = 'identifier_fastpath'
                stop_reason = _lane_budget_stop_reason(settings, dispatch_stats, lane_runtime_state, lane)
                if stop_reason is not None:
                    for doi_val in chunk:
                        group = doi_to_group[doi_val]
                        _record_lane_skip(dispatch_stats, group, reason=stop_reason)
                        handled_group_keys.add((group.provider, group.query_type, group.query_key))
                    continue
                _mark_lane_request_started(lane_runtime_state, lane)
                for doi_val in chunk:
                    group = doi_to_group[doi_val]
                    _start_group_statuses(repo, conn, group, query_type_override='doi_batch', notes='planned_batch')
                dispatch_stats['openalex_batch_request_count'] += 1
                _bump_lane_request(dispatch_stats, lane)
                logger.info('OpenAlex DOI batch chunk %s-%s / %s DOI(s)', i + 1, i + len(chunk), len(doi_values))
                try:
                    results = query_openalex_batch_by_doi(chunk, email=settings.openalex_email)
                except Exception as exc:
                    for doi_val in chunk:
                        group = doi_to_group[doi_val]
                        delta = _fanout_error_to_group(repo, tracker, conn, group, error_summary=str(exc), notes='doi_batch_error')
                        processed_intents += delta
                        _bump_lane_processed(dispatch_stats, group, delta)
                        handled_group_keys.add((group.provider, group.query_type, group.query_key))
                    continue

                matched_dois: set[str] = set()
                for item in results:
                    ids = item.get('ids') or {}
                    doi_val = (ids.get('doi') or '').replace('https://doi.org/', '').lower()
                    if not doi_val or doi_val not in doi_to_group:
                        continue
                    matched_dois.add(doi_val)
                    authors = [a.get('author', {}).get('display_name') for a in item.get('authorships', []) if a.get('author', {}).get('display_name')]
                    venue, url = _extract_primary_location_fields(item)
                    from mygooglealertpapers.enrich.base import EnrichmentRecord
                    group = doi_to_group[doi_val]
                    rec = EnrichmentRecord(
                        candidate_id=group.representative.candidate_id,
                        source_name='openalex',
                        query_type='doi_batch',
                        query_string=doi_val,
                        matched=True,
                        match_score=1.0,
                        external_id=item.get('id'),
                        title=item.get('display_name'),
                        authors_json=json.dumps(authors, ensure_ascii=False),
                        abstract=item.get('abstract_inverted_index') and json.dumps(item.get('abstract_inverted_index')),
                        venue=venue,
                        year=str(item.get('publication_year')) if item.get('publication_year') else None,
                        publication_type=item.get('type'),
                        doi=doi_val,
                        pmid=(ids.get('pmid') or '').replace('https://pubmed.ncbi.nlm.nih.gov/', '').strip('/') or None,
                        pmcid=(ids.get('pmcid') or '').replace('https://www.ncbi.nlm.nih.gov/pmc/articles/', '').strip('/') or None,
                        url=url,
                        raw_payload_json=json.dumps(item, ensure_ascii=False),
                        latency_ms=0,
                    )
                    repo.put_query_cache(conn, provider='openalex', query_type='doi', query_key=doi_val, response_json=enrichment_record_to_json(rec), **cache_metadata_from_record(rec, field_set_hash=_group_field_set_hash(group)))
                    delta = _fanout_result_to_group(repo, tracker, conn, group, rec, cache_hit=False, notes='doi_batch')
                    processed_intents += delta
                    _bump_lane_processed(dispatch_stats, group, delta)
                    handled_group_keys.add((group.provider, group.query_type, group.query_key))

                for doi_val in chunk:
                    if doi_val in matched_dois:
                        continue
                    from mygooglealertpapers.enrich.base import EnrichmentRecord
                    group = doi_to_group[doi_val]
                    rec = EnrichmentRecord(
                        candidate_id=group.representative.candidate_id,
                        source_name='openalex',
                        query_type='doi_batch',
                        query_string=doi_val,
                        matched=False,
                        match_score=None,
                        external_id=None,
                        title=None,
                        authors_json=None,
                        abstract=None,
                        venue=None,
                        year=None,
                        publication_type=None,
                        doi=doi_val,
                        pmid=None,
                        pmcid=None,
                        url=None,
                        raw_payload_json=json.dumps({'doi': doi_val, 'status': 'no_match', 'provider': 'openalex'}, ensure_ascii=False),
                        latency_ms=0,
                    )
                    repo.put_query_cache(conn, provider='openalex', query_type='doi', query_key=doi_val, response_json=enrichment_record_to_json(rec), **cache_metadata_from_record(rec, field_set_hash=_group_field_set_hash(group)))
                    delta = _fanout_result_to_group(repo, tracker, conn, group, rec, cache_hit=False, notes='doi_batch_no_match')
                    processed_intents += delta
                    _bump_lane_processed(dispatch_stats, group, delta)
                    handled_group_keys.add((group.provider, group.query_type, group.query_key))
                _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                conn.commit()

        for group in dispatch_groups:
            group_key = (group.provider, group.query_type, group.query_key)
            if group_key in handled_group_keys:
                continue

            lane = _lane_for_group(group)

            logger.info(
                'Enrich dispatch %s/%s: provider=%s query_type=%s query_key=%s fanout=%s',
                processed_intents + 1,
                len(runnable_intents),
                group.provider,
                group.query_type,
                group.query_key,
                len(group.intents),
            )
            _start_group_statuses(repo, conn, group)
            field_set_hash = _group_field_set_hash(group)
            cached = repo.get_query_cache(conn, provider=group.provider, query_type=group.query_type, query_key=group.query_key, field_set_hash=field_set_hash)
            if cached:
                cached_rec = enrichment_record_from_json(cached[0])
                if cache_status_from_record(cached_rec) != 'transient_error':
                    dispatch_stats['cache_hit_group_count'] += 1
                    rec = _record_from_cache(group.representative, cached[0])
                    delta = _fanout_result_to_group(repo, tracker, conn, group, rec, cache_hit=True)
                    processed_intents += delta
                    _bump_lane_processed(dispatch_stats, group, delta)
                    if processed_intents % PROGRESS_EVERY == 0:
                        logger.info('Enrich progress: processed %s / %s runnable intent(s)', processed_intents, len(runnable_intents))
                        _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                        _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                        conn.commit()
                    continue

            stop_reason = _lane_budget_stop_reason(settings, dispatch_stats, lane_runtime_state, lane)
            if stop_reason is not None:
                _record_lane_skip(dispatch_stats, group, reason=stop_reason)
                continue

            _mark_lane_request_started(lane_runtime_state, lane)
            dispatch_stats['non_batch_dispatch_request_count'] += 1
            _bump_lane_request(dispatch_stats, lane)
            shared_title_reuse = group.query_type == 'title' and len(group.intents) > 1 and _provider_title_payload_reuse_enabled(settings, group.provider)
            if shared_title_reuse:
                try:
                    records = _build_title_reused_records(settings, group)
                except Exception as exc:
                    from mygooglealertpapers.enrich.base import EnrichmentRecord
                    rec = EnrichmentRecord(
                        candidate_id=group.representative.candidate_id,
                        source_name=group.provider,
                        query_type=group.query_type,
                        query_string=group.query_key,
                        matched=False,
                        match_score=None,
                        external_id=None,
                        title=None,
                        authors_json=None,
                        abstract=None,
                        venue=None,
                        year=None,
                        publication_type=None,
                        doi=group.representative.doi,
                        pmid=group.representative.pmid,
                        pmcid=None,
                        url=None,
                        raw_payload_json=json.dumps({'status': 'error', 'provider': group.provider, 'error': str(exc)}, ensure_ascii=False),
                        latency_ms=0,
                    )
                    repo.put_query_cache(conn, provider=group.provider, query_type=group.query_type, query_key=group.query_key, response_json=enrichment_record_to_json(rec), **cache_metadata_from_record(rec, field_set_hash=field_set_hash))
                    delta = _fanout_error_to_group(repo, tracker, conn, group, error_summary=str(exc), notes='shared_title_reuse_error')
                    processed_intents += delta
                    _bump_lane_processed(dispatch_stats, group, delta)
                    if processed_intents % PROGRESS_EVERY == 0:
                        logger.info('Enrich progress: processed %s / %s runnable intent(s)', processed_intents, len(runnable_intents))
                        _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                        _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                        conn.commit()
                    continue

                if records is not None:
                    dispatch_stats['shared_title_reuse_group_count'] += 1
                    dispatch_stats['shared_title_reuse_intent_count'] += len(group.intents)
                    dispatch_stats['shared_title_reuse_request_count'] += 1
                    dispatch_stats['shared_title_reuse_request_savings'] += max(len(group.intents) - 1, 0)
                    for intent, rec in zip(group.intents, records, strict=True):
                        repo.put_query_cache(
                            conn,
                            provider=group.provider,
                            query_type=group.query_type,
                            query_key=group.query_key,
                            response_json=enrichment_record_to_json(rec),
                            **cache_metadata_from_record(rec, field_set_hash=_cache_field_set_hash(intent)),
                        )
                    delta = _fanout_records_to_group(repo, tracker, conn, group, records, cache_hit=False, notes='shared_title_reuse')
                    processed_intents += delta
                    _bump_lane_processed(dispatch_stats, group, delta)
                    if processed_intents % PROGRESS_EVERY == 0:
                        logger.info('Enrich progress: processed %s / %s runnable intent(s)', processed_intents, len(runnable_intents))
                        _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                        _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                        conn.commit()
                    continue

            try:
                rec = _execute_provider_query(settings, group.representative)
            except Exception as exc:
                from mygooglealertpapers.enrich.base import EnrichmentRecord
                rec = EnrichmentRecord(
                    candidate_id=group.representative.candidate_id,
                    source_name=group.provider,
                    query_type=group.query_type,
                    query_string=group.query_key,
                    matched=False,
                    match_score=None,
                    external_id=None,
                    title=None,
                    authors_json=None,
                    abstract=None,
                    venue=None,
                    year=None,
                    publication_type=None,
                    doi=group.representative.doi if group.query_type == 'doi' else None,
                    pmid=group.representative.pmid if group.query_type == 'pmid' else None,
                    pmcid=None,
                    url=None,
                    raw_payload_json=json.dumps({'status': 'error', 'provider': group.provider, 'error': str(exc)}, ensure_ascii=False),
                    latency_ms=0,
                )
                repo.put_query_cache(conn, provider=group.provider, query_type=group.query_type, query_key=group.query_key, response_json=enrichment_record_to_json(rec), **cache_metadata_from_record(rec, field_set_hash=field_set_hash))
                delta = _fanout_error_to_group(repo, tracker, conn, group, error_summary=str(exc))
                processed_intents += delta
                _bump_lane_processed(dispatch_stats, group, delta)
                if processed_intents % PROGRESS_EVERY == 0:
                    logger.info('Enrich progress: processed %s / %s runnable intent(s)', processed_intents, len(runnable_intents))
                    _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                    _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                    conn.commit()
                continue

            if rec is None:
                from mygooglealertpapers.enrich.base import EnrichmentRecord
                rec = EnrichmentRecord(
                    candidate_id=group.representative.candidate_id,
                    source_name=group.provider,
                    query_type=group.query_type,
                    query_string=group.query_key,
                    matched=False,
                    match_score=None,
                    external_id=None,
                    title=None,
                    authors_json=None,
                    abstract=None,
                    venue=None,
                    year=None,
                    publication_type=None,
                    doi=group.representative.doi if group.query_type == 'doi' else None,
                    pmid=group.representative.pmid if group.query_type == 'pmid' else None,
                    pmcid=None,
                    url=None,
                    raw_payload_json=json.dumps({'status': 'no_match', 'provider': group.provider, 'query_key': group.query_key}, ensure_ascii=False),
                    latency_ms=0,
                )
                repo.put_query_cache(conn, provider=group.provider, query_type=group.query_type, query_key=group.query_key, response_json=enrichment_record_to_json(rec), **cache_metadata_from_record(rec, field_set_hash=field_set_hash))
                delta = _fanout_result_to_group(repo, tracker, conn, group, rec, cache_hit=False, notes='no_record_returned')
                processed_intents += delta
                _bump_lane_processed(dispatch_stats, group, delta)
                if processed_intents % PROGRESS_EVERY == 0:
                    logger.info('Enrich progress: processed %s / %s runnable intent(s)', processed_intents, len(runnable_intents))
                    _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                    _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                    conn.commit()
                continue

            repo.put_query_cache(conn, provider=group.provider, query_type=group.query_type, query_key=group.query_key, response_json=enrichment_record_to_json(rec), **cache_metadata_from_record(rec, field_set_hash=field_set_hash))
            delta = _fanout_result_to_group(repo, tracker, conn, group, rec, cache_hit=False)
            processed_intents += delta
            _bump_lane_processed(dispatch_stats, group, delta)
            if processed_intents % PROGRESS_EVERY == 0:
                logger.info('Enrich progress: processed %s / %s runnable intent(s)', processed_intents, len(runnable_intents))
                _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
                _persist_dispatch_progress(repo, conn, run_id=run_id, started_at=started_at, processed_intents=processed_intents, dispatch_stats=dispatch_stats)
                conn.commit()

        _refresh_lane_elapsed(dispatch_stats, lane_runtime_state)
        dispatch_stats['dispatch_request_count'] = dispatch_stats['openalex_batch_request_count'] + dispatch_stats['non_batch_dispatch_request_count']
        dispatch_stats['request_savings_vs_runnable_intents'] = dispatch_stats['runnable_provider_intents'] - dispatch_stats['dispatch_request_count']
        dispatch_stats['processed_runnable_intents'] = processed_intents
        repo.finish_batch_run(
            conn,
            run_id=run_id,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            processed_count=processed_intents,
            status='ok',
            notes=json.dumps(dispatch_stats, ensure_ascii=False),
        )
        conn.commit()
