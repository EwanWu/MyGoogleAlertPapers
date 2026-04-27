from __future__ import annotations

import json
import random
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_STATUSES = frozenset({408, 429, 500, 502, 503, 504})
DEFAULT_TOOL_NAME = 'MyGoogleAlertPapers'
DEFAULT_TOOL_VERSION = '0.1'


@dataclass(slots=True)
class HttpResult:
    ok: bool
    provider: str
    url: str
    status_code: int | None
    body_text: str | None
    json_data: Any | None
    error: str | None
    error_type: str | None
    retry_after_seconds: int | None
    attempts: int
    latency_ms: int
    headers: dict[str, str]

    def to_error_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'provider': self.provider,
            'url': self.url,
            'attempts': self.attempts,
            'latency_ms': self.latency_ms,
        }
        if self.status_code is not None:
            payload['http_error'] = self.status_code
        if self.error:
            payload['error'] = self.error
        if self.error_type:
            payload['error_type'] = self.error_type
        if self.retry_after_seconds is not None:
            payload['retry_after_seconds'] = self.retry_after_seconds
        if self.body_text:
            payload['body'] = self.body_text[:1000]
        return payload


def _build_user_agent(
    provider: str,
    *,
    contact_email: str | None = None,
    tool_name: str = DEFAULT_TOOL_NAME,
    tool_version: str = DEFAULT_TOOL_VERSION,
) -> str:
    details = [provider]
    if contact_email:
        details.append(f'contact={contact_email}')
    return f"{tool_name}/{tool_version} ({'; '.join(details)})"


def build_headers(
    provider: str,
    *,
    contact_email: str | None = None,
    extra_headers: dict[str, str] | None = None,
    tool_name: str = DEFAULT_TOOL_NAME,
    tool_version: str = DEFAULT_TOOL_VERSION,
) -> dict[str, str]:
    headers = {
        'Accept': 'application/json',
        'User-Agent': _build_user_agent(
            provider,
            contact_email=contact_email,
            tool_name=tool_name,
            tool_version=tool_version,
        ),
    }
    if contact_email:
        headers['From'] = contact_email
    if extra_headers:
        headers.update(extra_headers)
    return headers


def _parse_retry_after(value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return max(0, int(value))
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = (dt - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(delta))


def _sleep_seconds(attempt: int, retry_after_seconds: int | None) -> float:
    if retry_after_seconds is not None:
        return float(min(retry_after_seconds, 30))
    base = min(2 ** max(attempt - 1, 0), 8)
    jitter = random.random() * 0.25 * base
    return float(base + jitter)


def _open(request: urllib.request.Request, *, timeout: int, opener=None):
    if opener is not None:
        return opener.open(request, timeout=timeout)
    return urllib.request.urlopen(request, timeout=timeout)


def request_text(
    provider: str,
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    contact_email: str | None = None,
    extra_headers: dict[str, str] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_statuses: set[int] | frozenset[int] = DEFAULT_RETRY_STATUSES,
    opener=None,
) -> HttpResult:
    started_at = time.perf_counter()
    attempts = 0
    headers = build_headers(provider, contact_email=contact_email, extra_headers=extra_headers)

    while True:
        attempts += 1
        request = urllib.request.Request(url, headers=headers)
        try:
            with _open(request, timeout=timeout, opener=opener) as response:
                body_text = response.read().decode('utf-8', errors='replace')
                return HttpResult(
                    ok=True,
                    provider=provider,
                    url=url,
                    status_code=getattr(response, 'status', None) or response.getcode(),
                    body_text=body_text,
                    json_data=None,
                    error=None,
                    error_type=None,
                    retry_after_seconds=None,
                    attempts=attempts,
                    latency_ms=int((time.perf_counter() - started_at) * 1000),
                    headers={k: str(v) for k, v in response.headers.items()},
                )
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode('utf-8', errors='replace') if exc.fp else None
            retry_after_seconds = _parse_retry_after(exc.headers.get('Retry-After')) if exc.headers else None
            if exc.code in retry_statuses and attempts <= max_retries:
                time.sleep(_sleep_seconds(attempts, retry_after_seconds))
                continue
            return HttpResult(
                ok=False,
                provider=provider,
                url=url,
                status_code=exc.code,
                body_text=body_text,
                json_data=None,
                error=f'HTTP {exc.code}',
                error_type='http_error',
                retry_after_seconds=retry_after_seconds,
                attempts=attempts,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                headers={k: str(v) for k, v in (exc.headers.items() if exc.headers else [])},
            )
        except urllib.error.URLError as exc:
            message = str(exc.reason or exc)
            is_timeout = isinstance(exc.reason, (TimeoutError, socket.timeout)) or 'timed out' in message.casefold()
            error_type = 'timeout' if is_timeout else 'network_error'
            if attempts <= max_retries:
                time.sleep(_sleep_seconds(attempts, None))
                continue
            return HttpResult(
                ok=False,
                provider=provider,
                url=url,
                status_code=None,
                body_text=None,
                json_data=None,
                error=message,
                error_type=error_type,
                retry_after_seconds=None,
                attempts=attempts,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                headers={},
            )
        except socket.timeout as exc:
            if attempts <= max_retries:
                time.sleep(_sleep_seconds(attempts, None))
                continue
            return HttpResult(
                ok=False,
                provider=provider,
                url=url,
                status_code=None,
                body_text=None,
                json_data=None,
                error=str(exc),
                error_type='timeout',
                retry_after_seconds=None,
                attempts=attempts,
                latency_ms=int((time.perf_counter() - started_at) * 1000),
                headers={},
            )


def request_json(
    provider: str,
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    contact_email: str | None = None,
    extra_headers: dict[str, str] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_statuses: set[int] | frozenset[int] = DEFAULT_RETRY_STATUSES,
    opener=None,
) -> HttpResult:
    result = request_text(
        provider,
        url,
        timeout=timeout,
        contact_email=contact_email,
        extra_headers=extra_headers,
        max_retries=max_retries,
        retry_statuses=retry_statuses,
        opener=opener,
    )
    if not result.ok:
        return result
    try:
        payload = json.loads(result.body_text or '')
    except json.JSONDecodeError as exc:
        return HttpResult(
            ok=False,
            provider=result.provider,
            url=result.url,
            status_code=result.status_code,
            body_text=result.body_text,
            json_data=None,
            error=f'invalid JSON: {exc}',
            error_type='invalid_json',
            retry_after_seconds=result.retry_after_seconds,
            attempts=result.attempts,
            latency_ms=result.latency_ms,
            headers=result.headers,
        )
    result.json_data = payload
    return result
