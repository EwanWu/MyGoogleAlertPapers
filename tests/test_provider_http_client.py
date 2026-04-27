from __future__ import annotations

import io
import urllib.error
from email.message import Message

from mygooglealertpapers.enrich.http_client import request_json


class _FakeResponse:
    def __init__(self, body: str, *, status: int = 200, headers: dict[str, str] | None = None):
        self._body = body.encode('utf-8')
        self.status = status
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_request_json_retries_on_429_and_injects_identity_headers(monkeypatch):
    calls: list[dict[str, str | None]] = []
    sleeps: list[float] = []

    def fake_open(request, *, timeout: int, opener=None):
        calls.append(
            {
                'user_agent': request.get_header('User-agent'),
                'from_header': request.get_header('From'),
            }
        )
        if len(calls) == 1:
            headers = Message()
            headers['Retry-After'] = '1'
            raise urllib.error.HTTPError(request.full_url, 429, 'Too Many Requests', headers, io.BytesIO(b'{"error":"rate"}'))
        return _FakeResponse('{"ok": true}', status=200)

    monkeypatch.setattr('mygooglealertpapers.enrich.http_client._open', fake_open)
    monkeypatch.setattr('mygooglealertpapers.enrich.http_client.time.sleep', lambda seconds: sleeps.append(seconds))

    result = request_json('openalex', 'https://api.openalex.org/works?search=test', contact_email='unit@test.example')

    assert result.ok is True
    assert result.json_data == {'ok': True}
    assert result.attempts == 2
    assert sleeps == [1.0]
    assert calls[0]['user_agent'] is not None and 'openalex' in calls[0]['user_agent']
    assert calls[0]['from_header'] == 'unit@test.example'


def test_request_json_marks_invalid_json(monkeypatch):
    monkeypatch.setattr(
        'mygooglealertpapers.enrich.http_client._open',
        lambda request, *, timeout, opener=None: _FakeResponse('not-json', status=200),
    )

    result = request_json('crossref', 'https://api.crossref.org/works/test')

    assert result.ok is False
    assert result.error_type == 'invalid_json'
    assert result.status_code == 200
