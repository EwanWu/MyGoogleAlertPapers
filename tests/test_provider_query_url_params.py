from __future__ import annotations

from mygooglealertpapers.config import load_settings
from mygooglealertpapers.enrich.crossref import fetch_crossref_title_item, query_crossref
from mygooglealertpapers.enrich.openalex import query_openalex, query_openalex_batch_by_doi


class DummyResponse:
    def __init__(self, payload: dict, *, latency_ms: int = 9):
        self.ok = True
        self.json_data = payload
        self.latency_ms = latency_ms

    def to_error_payload(self):
        return {'error': 'unexpected'}


def test_load_settings_reads_openalex_api_key(monkeypatch):
    monkeypatch.setenv('OPENALEX_API_KEY', 'unit-key')
    monkeypatch.setenv('OPENALEX_EMAIL', 'unit@example.com')
    settings = load_settings()

    assert settings.openalex_api_key == 'unit-key'
    assert settings.openalex_email == 'unit@example.com'


def test_query_openalex_uses_api_key_and_select(monkeypatch):
    seen: list[str] = []

    def fake_request_json(provider: str, url: str, **kwargs):
        seen.append(url)
        return DummyResponse({'results': []})

    monkeypatch.setattr('mygooglealertpapers.enrich.openalex.request_json', fake_request_json)

    query_openalex(
        'cand1',
        doi=None,
        title='Example title',
        email='unit@example.com',
        api_key='unit-key',
        title_per_page=5,
        title_pick_best_accepted=True,
    )

    assert len(seen) == 1
    url = seen[0]
    assert 'api_key=unit-key' in url
    assert 'mailto=unit%40example.com' in url
    assert 'per_page=5' in url


def test_query_openalex_batch_by_doi_uses_api_key_and_select(monkeypatch):
    seen: list[str] = []

    def fake_request_json(provider: str, url: str, **kwargs):
        seen.append(url)
        return DummyResponse({'results': []})

    monkeypatch.setattr('mygooglealertpapers.enrich.openalex.request_json', fake_request_json)

    query_openalex_batch_by_doi(['10.1/a', '10.1/b'], email='unit@example.com', api_key='unit-key')

    assert len(seen) == 1
    url = seen[0]
    assert 'api_key=unit-key' in url
    assert 'mailto=unit%40example.com' in url
    assert 'per_page=2' in url
    assert 'filter=' in url


def test_crossref_queries_use_mailto_and_select(monkeypatch):
    seen: list[str] = []

    def fake_request_json(provider: str, url: str, **kwargs):
        seen.append(url)
        return DummyResponse({'message': {'items': []}})

    monkeypatch.setattr('mygooglealertpapers.enrich.crossref.request_json', fake_request_json)

    fetch_crossref_title_item('Example title', mailto='unit@example.com')
    query_crossref('cand2', doi='10.1/example', title=None, mailto='unit@example.com')

    assert len(seen) == 2
    title_url, doi_url = seen
    assert 'mailto=unit%40example.com' in title_url
    assert 'query.title=Example+title' in title_url
    assert 'mailto=unit%40example.com' in doi_url
