from __future__ import annotations

import json

from mygooglealertpapers.enrich.openalex import query_openalex


class DummyResponse:
    def __init__(self, payload: dict, *, latency_ms: int = 17):
        self.ok = True
        self.json_data = payload
        self.latency_ms = latency_ms

    def to_error_payload(self):
        return {'error': 'unexpected'}


def test_query_openalex_title_can_select_later_accepted_result_from_topk(monkeypatch):
    payload = {
        'results': [
            {
                'id': 'https://openalex.org/W-bad',
                'display_name': 'Obesity and Cardiovascular Disease: Pathophysiology, Evaluation, and Effect of Weight Loss',
                'publication_year': 2006,
                'type': 'article',
                'ids': {'doi': 'https://doi.org/10.1161/circulationaha.106.171016'},
                'authorships': [
                    {'author': {'display_name': 'Someone Else'}},
                ],
                'primary_location': {'source': {'display_name': 'Circulation'}},
            },
            {
                'id': 'https://openalex.org/W-good',
                'display_name': 'The Effect of Preoperative Epicardial Adipose Tissue Thickness on Postoperative Morbidity and Mortality in Patients Undergoing Isolated Coronary Artery Bypass Grafting',
                'publication_year': 2026,
                'type': 'article',
                'ids': {'doi': 'https://doi.org/10.3390/jcm15062207'},
                'authorships': [
                    {'author': {'display_name': 'Topuz A'}},
                ],
                'primary_location': {
                    'source': {'display_name': 'Journal of Clinical Medicine'},
                    'landing_page_url': 'https://www.mdpi.com/2077-0383/15/6/2207',
                },
            },
        ]
    }

    def fake_request_json(provider: str, url: str, **kwargs):
        assert provider == 'openalex'
        assert 'per_page=5' in url
        return DummyResponse(payload)

    monkeypatch.setattr('mygooglealertpapers.enrich.openalex.request_json', fake_request_json)

    rec = query_openalex(
        'cand_topk',
        doi=None,
        title='The Effect of Preoperative Epicardial Adipose Tissue Thickness on Postoperative Morbidity and Mortality in Patients Undergoing Isolated Coronary Artery Bypass. .',
        first_author_family='Topuz',
        venue_hint='Journal of Clinical Medicine',
        query_year='2026',
        title_per_page=5,
        title_pick_best_accepted=True,
    )

    assert rec is not None
    assert rec.matched is True
    assert rec.doi == '10.3390/jcm15062207'
    assert rec.external_id == 'https://openalex.org/W-good'
    payload_dict = json.loads(rec.raw_payload_json)
    assert isinstance(payload_dict.get('results'), list)
    assert len(payload_dict['results']) == 2


def test_query_openalex_title_auto_retries_topk_for_repository_shadow_result(monkeypatch):
    initial_payload = {
        'results': [
            {
                'id': 'https://openalex.org/W-repo',
                'display_name': 'Grayscale-inverted bright-blood late gadolinium enhancement improves reader confidence in ischemic scar detection: a multivendor study',
                'publication_year': 2026,
                'type': 'article',
                'ids': {'doi': 'https://doi.org/10.5167/uzh-433681'},
                'authorships': [
                    {'author': {'display_name': 'Mihály Károlyi'}},
                ],
                'primary_location': {
                    'source': {'display_name': 'Universität Zürich, ZORA', 'type': 'repository'},
                    'landing_page_url': 'https://doi.org/10.5167/uzh-433681',
                    'raw_type': 'article-journal',
                },
            },
        ]
    }
    retry_payload = {
        'results': [
            initial_payload['results'][0],
            {
                'id': 'https://openalex.org/W-journal',
                'display_name': 'Grayscale-inverted bright-blood late gadolinium enhancement improves reader confidence in ischemic scar detection: a multivendor study',
                'publication_year': 2026,
                'type': 'article',
                'ids': {'doi': 'https://doi.org/10.1016/j.ejrad.2026.112801'},
                'authorships': [
                    {'author': {'display_name': 'Mihály Károlyi'}},
                ],
                'primary_location': {
                    'source': {'display_name': 'European Journal of Radiology', 'type': 'journal'},
                    'landing_page_url': 'https://doi.org/10.1016/j.ejrad.2026.112801',
                    'raw_type': 'journal-article',
                },
            },
        ]
    }
    calls: list[str] = []

    def fake_request_json(provider: str, url: str, **kwargs):
        assert provider == 'openalex'
        calls.append(url)
        if 'per_page=1' in url:
            return DummyResponse(initial_payload, latency_ms=11)
        if 'per_page=5' in url:
            return DummyResponse(retry_payload, latency_ms=13)
        raise AssertionError(url)

    monkeypatch.setattr('mygooglealertpapers.enrich.openalex.request_json', fake_request_json)

    rec = query_openalex(
        'cand_repo_shadow',
        doi=None,
        title='Grayscale-inverted bright-blood late gadolinium enhancement improves reader confidence in ischemic scar Detection: A multivendor study',
        first_author_family='Károlyi',
        venue_hint='European Journal of',
        query_year='2026',
    )

    assert rec is not None
    assert rec.matched is True
    assert rec.doi == '10.1016/j.ejrad.2026.112801'
    assert rec.external_id == 'https://openalex.org/W-journal'
    assert len(calls) == 2
    assert 'per_page=1' in calls[0]
    assert 'per_page=5' in calls[1]
    payload_dict = json.loads(rec.raw_payload_json)
    assert isinstance(payload_dict.get('results'), list)
    assert len(payload_dict['results']) == 2
    assert rec.latency_ms == 24


def test_query_openalex_title_does_not_auto_retry_for_repository_preprint(monkeypatch):
    payload = {
        'results': [
            {
                'id': 'https://openalex.org/W-preprint',
                'display_name': 'Preoperative Prediction of Persistent Type II Endoleaks After Endovascular Aortic Repair Using Multiregional Perianeurysmal Computed Tomography Angiography Radiomics: A Multicenter Study',
                'publication_year': 2026,
                'type': 'preprint',
                'ids': {'doi': 'https://doi.org/10.21203/rs.3.rs-9018408/v1'},
                'authorships': [
                    {'author': {'display_name': 'Xinlei Yu'}},
                ],
                'primary_location': {
                    'source': {'display_name': 'Research Square', 'type': 'repository'},
                    'landing_page_url': 'https://doi.org/10.21203/rs.3.rs-9018408/v1',
                    'raw_type': 'posted-content',
                },
            },
        ]
    }
    calls: list[str] = []

    def fake_request_json(provider: str, url: str, **kwargs):
        assert provider == 'openalex'
        calls.append(url)
        return DummyResponse(payload, latency_ms=17)

    monkeypatch.setattr('mygooglealertpapers.enrich.openalex.request_json', fake_request_json)

    rec = query_openalex(
        'cand_repo_preprint',
        doi=None,
        title='Preoperative Prediction of Persistent Type II Endoleaks After Endovascular Aortic Repair Using Multiregional Perianeurysmal Computed Tomography Angiography. .',
        first_author_family='Yu',
        venue_hint=None,
        query_year='2026',
    )

    assert rec is not None
    assert rec.matched is False
    assert rec.doi == '10.21203/rs.3.rs-9018408/v1'
    assert len(calls) == 1
    assert 'per_page=1' in calls[0]
