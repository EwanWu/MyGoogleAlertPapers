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
        assert 'per-page=5' in url
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
