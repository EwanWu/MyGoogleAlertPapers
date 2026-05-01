from __future__ import annotations

from types import SimpleNamespace

from mygooglealertpapers.pipeline.enrich import (
    DispatchGroup,
    ProviderIntent,
    TITLE_LANE_REASON_IDENTIFIER_GAP,
    _openalex_title_query_per_page,
    _openalex_title_should_pick_best_accepted,
)


class DummyPolicyProfile:
    def __init__(self, runtime_rules: dict[str, object]):
        self._runtime_rules = runtime_rules

    def runtime_value(self, key: str, default: object = None) -> object:
        return self._runtime_rules.get(key, default)


def _settings(runtime_rules: dict[str, object]):
    return SimpleNamespace(policy_profile=DummyPolicyProfile(runtime_rules))


def _group(*, arxiv_id: str | None) -> DispatchGroup:
    intent = ProviderIntent(
        candidate_id='cand_1',
        provider='openalex',
        query_type='title',
        query_key='title:demo',
        norm_title='Demo title',
        doi=None,
        pmid=None,
        arxiv_id=arxiv_id,
        first_author_family='Zhang',
        venue_guess='arXiv preprint arXiv:2601.00001' if arxiv_id else 'Journal of Demo',
        year_guess='2026',
    )
    return DispatchGroup(representative=intent, intents=[intent])


def test_openalex_topk_gate_blocks_url_only_expansion_without_arxiv_id():
    settings = _settings(
        {
            'openalex_title_per_page_by_subreason': {'url_canonical_only': 5},
            'openalex_title_pick_best_accepted_subreasons': ['url_canonical_only'],
            'openalex_title_extra_result_require_arxiv_id_subreasons': ['url_canonical_only'],
        }
    )
    group = _group(arxiv_id=None)

    assert _openalex_title_query_per_page(
        settings,
        group,
        TITLE_LANE_REASON_IDENTIFIER_GAP,
        'url_canonical_only',
    ) == 1
    assert _openalex_title_should_pick_best_accepted(
        settings,
        group,
        TITLE_LANE_REASON_IDENTIFIER_GAP,
        'url_canonical_only',
    ) is False


def test_openalex_topk_gate_allows_url_only_expansion_with_arxiv_id():
    settings = _settings(
        {
            'openalex_title_per_page_by_subreason': {'url_canonical_only': 5},
            'openalex_title_pick_best_accepted_subreasons': ['url_canonical_only'],
            'openalex_title_extra_result_require_arxiv_id_subreasons': ['url_canonical_only'],
        }
    )
    group = _group(arxiv_id='2601.00001')

    assert _openalex_title_query_per_page(
        settings,
        group,
        TITLE_LANE_REASON_IDENTIFIER_GAP,
        'url_canonical_only',
    ) == 5
    assert _openalex_title_should_pick_best_accepted(
        settings,
        group,
        TITLE_LANE_REASON_IDENTIFIER_GAP,
        'url_canonical_only',
    ) is True
