from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass

from mygooglealertpapers.config import Settings
from mygooglealertpapers.cost.tracker import CostTracker
from mygooglealertpapers.db.repository import Repository
from mygooglealertpapers.enrich.base import enrichment_record_from_json, enrichment_record_to_json
from mygooglealertpapers.enrich.crossref import query_crossref
from mygooglealertpapers.enrich.openalex import query_openalex, query_openalex_batch_by_doi
from mygooglealertpapers.enrich.pubmed import query_pubmed
from mygooglealertpapers.enrich.semanticscholar import query_semanticscholar
from mygooglealertpapers.enrich.europepmc import query_europepmc
from mygooglealertpapers.enrich.arxiv import query_arxiv

logger = logging.getLogger(__name__)


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


def _insert_source_record(repo: Repository, conn, rec) -> int:
    repo.insert_source_record(conn, rec)
    return conn.execute('SELECT last_insert_rowid()').fetchone()[0]


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

        runnable_intents = [intent for intent in all_intents if _should_run_provider(repo, conn, intent)]
        logger.info('Planned %s provider intent(s); %s need work', len(all_intents), len(runnable_intents))

        openalex_doi_batch_enabled = bool(_provider_value(settings, 'openalex', 'doi_batch_enabled', True))
        openalex_doi_intents = [
            intent for intent in runnable_intents
            if openalex_doi_batch_enabled and intent.provider == 'openalex' and intent.query_type == 'doi' and intent.doi
        ]
        handled_openalex_candidates: set[str] = set()
        if openalex_doi_intents:
            doi_to_candidate_ids: dict[str, list[str]] = {}
            for intent in openalex_doi_intents:
                doi_val = (intent.doi or '').lower()
                if not doi_val:
                    continue
                doi_to_candidate_ids.setdefault(doi_val, []).append(intent.candidate_id)
                repo.start_enrichment_status(conn, candidate_id=intent.candidate_id, provider='openalex', query_type='doi_batch', query_key=doi_val, notes='planned_batch')
            doi_values = list(doi_to_candidate_ids.keys())
            for i in range(0, len(doi_values), 50):
                chunk = doi_values[i:i + 50]
                try:
                    results = query_openalex_batch_by_doi(chunk, email=settings.openalex_email)
                except Exception as exc:
                    for doi_val in chunk:
                        for candidate_id in doi_to_candidate_ids.get(doi_val, []):
                            repo.finish_enrichment_status(conn, candidate_id=candidate_id, provider='openalex', status='error', latency_ms=0, error_summary=str(exc), notes='doi_batch_error')
                            tracker.record_stage_cost(conn, stage='enrich_candidates', status='error', candidate_id=candidate_id, provider='openalex', latency_ms=0, notes='doi_batch_error')
                    continue

                matched_in_chunk: set[tuple[str, str]] = set()
                for item in results:
                    ids = item.get('ids') or {}
                    doi_val = (ids.get('doi') or '').replace('https://doi.org/', '').lower()
                    if not doi_val or doi_val not in doi_to_candidate_ids:
                        continue
                    authors = [a.get('author', {}).get('display_name') for a in item.get('authorships', []) if a.get('author', {}).get('display_name')]
                    venue = (item.get('primary_location') or {}).get('source', {}).get('display_name')
                    from mygooglealertpapers.enrich.base import EnrichmentRecord
                    for candidate_id in doi_to_candidate_ids[doi_val]:
                        rec = EnrichmentRecord(
                            candidate_id=candidate_id,
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
                            url=(item.get('primary_location') or {}).get('landing_page_url'),
                            raw_payload_json=json.dumps(item, ensure_ascii=False),
                            latency_ms=0,
                        )
                        source_record_id = _insert_source_record(repo, conn, rec)
                        repo.put_query_cache(conn, provider='openalex', query_type='doi', query_key=doi_val, response_json=enrichment_record_to_json(rec))
                        repo.finish_enrichment_status(conn, candidate_id=candidate_id, provider='openalex', status='ok', source_record_id=source_record_id, cache_hit=False, latency_ms=0, notes='doi_batch')
                        tracker.record_stage_cost(conn, stage='enrich_candidates', status='ok', candidate_id=candidate_id, provider='openalex', latency_ms=0, notes='doi_batch')
                        handled_openalex_candidates.add(candidate_id)
                        matched_in_chunk.add((candidate_id, doi_val))

                for doi_val in chunk:
                    for candidate_id in doi_to_candidate_ids.get(doi_val, []):
                        if (candidate_id, doi_val) not in matched_in_chunk:
                            from mygooglealertpapers.enrich.base import EnrichmentRecord
                            rec = EnrichmentRecord(
                                candidate_id=candidate_id,
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
                            source_record_id = _insert_source_record(repo, conn, rec)
                            repo.put_query_cache(conn, provider='openalex', query_type='doi', query_key=doi_val, response_json=enrichment_record_to_json(rec))
                            repo.finish_enrichment_status(conn, candidate_id=candidate_id, provider='openalex', status='no_match', source_record_id=source_record_id, latency_ms=0, notes='doi_batch_no_match')
                            tracker.record_stage_cost(conn, stage='enrich_candidates', status='no_match', candidate_id=candidate_id, provider='openalex', latency_ms=0, notes='doi_batch_no_match')
                            handled_openalex_candidates.add(candidate_id)

        processed_intents = 0
        for intent in runnable_intents:
            if intent.provider == 'openalex' and intent.candidate_id in handled_openalex_candidates and intent.query_type == 'doi':
                continue

            repo.start_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider, query_type=intent.query_type, query_key=intent.query_key)
            cached = repo.get_query_cache(conn, provider=intent.provider, query_type=intent.query_type, query_key=intent.query_key)
            if cached:
                rec = _record_from_cache(intent, cached[0])
                source_record_id = _insert_source_record(repo, conn, rec)
                status = 'ok' if rec.matched else 'no_match'
                repo.finish_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider, status=status, source_record_id=source_record_id, cache_hit=True, latency_ms=0)
                tracker.record_stage_cost(conn, stage='enrich_candidates', status='cache_hit', candidate_id=intent.candidate_id, provider=intent.provider, latency_ms=0)
                processed_intents += 1
                continue

            try:
                if intent.provider == 'pubmed':
                    rec = query_pubmed(intent.candidate_id, pmid=intent.pmid, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, candidate_doi=intent.doi)
                elif intent.provider == 'europepmc':
                    rec = query_europepmc(intent.candidate_id, doi=intent.doi, pmid=intent.pmid, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess)
                elif intent.provider == 'arxiv':
                    rec = query_arxiv(intent.candidate_id, arxiv_id=intent.arxiv_id, title=intent.norm_title if intent.query_type == 'title' else None, first_author_family=intent.first_author_family, query_year=intent.year_guess)
                elif intent.provider == 'semanticscholar':
                    rec = query_semanticscholar(intent.candidate_id, doi=intent.doi, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, api_key=settings.semantic_scholar_api_key)
                elif intent.provider == 'crossref':
                    rec = query_crossref(intent.candidate_id, doi=intent.doi, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess, mailto=settings.crossref_mailto)
                elif intent.provider == 'openalex':
                    rec = query_openalex(intent.candidate_id, doi=intent.doi, title=intent.norm_title, first_author_family=intent.first_author_family, venue_hint=intent.venue_guess, query_year=intent.year_guess)
                else:
                    rec = None
            except Exception as exc:
                from mygooglealertpapers.enrich.base import EnrichmentRecord
                rec = EnrichmentRecord(
                    candidate_id=intent.candidate_id,
                    source_name=intent.provider,
                    query_type=intent.query_type,
                    query_string=intent.query_key,
                    matched=False,
                    match_score=None,
                    external_id=None,
                    title=None,
                    authors_json=None,
                    abstract=None,
                    venue=None,
                    year=None,
                    publication_type=None,
                    doi=intent.doi if intent.query_type == 'doi' else None,
                    pmid=intent.pmid if intent.query_type == 'pmid' else None,
                    pmcid=None,
                    url=None,
                    raw_payload_json=json.dumps({'status': 'error', 'provider': intent.provider, 'error': str(exc)}, ensure_ascii=False),
                    latency_ms=0,
                )
                repo.put_query_cache(conn, provider=intent.provider, query_type=intent.query_type, query_key=intent.query_key, response_json=enrichment_record_to_json(rec))
                repo.finish_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider, status='error', latency_ms=0, error_summary=str(exc))
                tracker.record_stage_cost(conn, stage='enrich_candidates', status='error', candidate_id=intent.candidate_id, provider=intent.provider, latency_ms=0, notes=str(exc))
                processed_intents += 1
                continue

            if rec is None:
                from mygooglealertpapers.enrich.base import EnrichmentRecord
                rec = EnrichmentRecord(
                    candidate_id=intent.candidate_id,
                    source_name=intent.provider,
                    query_type=intent.query_type,
                    query_string=intent.query_key,
                    matched=False,
                    match_score=None,
                    external_id=None,
                    title=None,
                    authors_json=None,
                    abstract=None,
                    venue=None,
                    year=None,
                    publication_type=None,
                    doi=intent.doi if intent.query_type == 'doi' else None,
                    pmid=intent.pmid if intent.query_type == 'pmid' else None,
                    pmcid=None,
                    url=None,
                    raw_payload_json=json.dumps({'status': 'no_match', 'provider': intent.provider, 'query_key': intent.query_key}, ensure_ascii=False),
                    latency_ms=0,
                )
                repo.put_query_cache(conn, provider=intent.provider, query_type=intent.query_type, query_key=intent.query_key, response_json=enrichment_record_to_json(rec))
                source_record_id = _insert_source_record(repo, conn, rec)
                repo.finish_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider, status='no_match', source_record_id=source_record_id, latency_ms=0, notes='no_record_returned')
                tracker.record_stage_cost(conn, stage='enrich_candidates', status='no_match', candidate_id=intent.candidate_id, provider=intent.provider, latency_ms=0, notes='no_record_returned')
                processed_intents += 1
                continue

            repo.put_query_cache(conn, provider=intent.provider, query_type=intent.query_type, query_key=intent.query_key, response_json=enrichment_record_to_json(rec))
            source_record_id = _insert_source_record(repo, conn, rec)
            status = 'ok' if rec.matched else 'no_match'
            repo.finish_enrichment_status(conn, candidate_id=intent.candidate_id, provider=intent.provider, status=status, source_record_id=source_record_id, cache_hit=False, latency_ms=rec.latency_ms)
            tracker.record_stage_cost(conn, stage='enrich_candidates', status=status, candidate_id=intent.candidate_id, provider=intent.provider, latency_ms=rec.latency_ms)
            processed_intents += 1

        repo.finish_batch_run(conn, run_id=run_id, duration_ms=int((time.perf_counter() - started_at) * 1000), processed_count=processed_intents, status='ok')
        conn.commit()
