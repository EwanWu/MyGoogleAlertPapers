#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright, Page, Browser, Playwright

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / 'data' / 'task_state' / '163_mail_read_local_state.json'
OUT_DIR = ROOT / 'data' / 'raw_mail_exports' / '163_scholar_local'
DIAG_DIR = OUT_DIR / 'diagnostics'
INDEX_JSONL = OUT_DIR / 'scholar_index.jsonl'
BODY_JSONL = OUT_DIR / 'scholar_body_fetch.jsonl'
BODY_FAILURE_JSONL = OUT_DIR / 'scholar_body_fetch_failures.jsonl'
SOFT_RESET_EVERY_PAGES = 3
SOFT_RESET_WAIT_MS = 2200

LOGIN_HINTS = ['账号登录', '扫码登录', '输入密码', '登录网易邮箱', '其他方式登录']
CAPTCHA_HINTS = ['滑动验证', '请完成验证', '安全验证', '拖动滑块', '验证码', 'captcha', 'nc_']
INBOX_HINTS = ['收件箱', '写 信', '写信', '未读邮件', '邮件全文搜索', '网易邮箱6.0版', '全部设为已读']
ERROR_HINTS = ['糟糕，出现了错误', '服务器开小差了', '返回首页']
UNREAD_TITLE_RE = re.compile(r'\((\d+)封未读\)')


@dataclass
class TaskState:
    status: str = 'idle'
    mode: str = 'index'
    current_step: str = ''
    next_step: str = ''
    cdp_endpoint: str = 'http://127.0.0.1:9222'
    current_url: str = ''
    page_no: int = 1
    indexed_count: int = 0
    body_fetched_count: int = 0
    last_row_key: str = ''
    artifacts: dict[str, Any] | None = None
    note: str = ''
    updated_at: str = ''

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if self.artifacts is None:
            self.artifacts = {}


def load_state() -> TaskState:
    if not STATE_PATH.exists():
        state = TaskState()
        state.touch()
        return state
    raw = json.loads(STATE_PATH.read_text(encoding='utf-8'))
    state = TaskState(**raw)
    state.touch()
    return state


def save_state(state: TaskState) -> None:
    state.touch()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding='utf-8')


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def _body_fetch_list_url(page_url: str) -> str:
    page_url = (page_url or '').strip()
    if not page_url:
        return page_url
    # Full body fetch should search the regular inbox list, not only the unread-filter view.
    # The index was collected from an unread-filter roster, but later fetch runs may target mails
    # that are no longer visible in unread pages.
    page_url = page_url.replace('%22filter%22%3A%7B%22flags%22%3A%7B%22read%22%3Afalse%7D%7D%2C', '')
    page_url = page_url.replace('%2C%22filter%22%3A%7B%22flags%22%3A%7B%22read%22%3Afalse%7D%7D', '')
    page_url = page_url.replace('"filter":{"flags":{"read":false}},', '')
    page_url = page_url.replace(',"filter":{"flags":{"read":false}}', '')
    return page_url


def _resolve_cdp_endpoint(cdp_endpoint: str) -> str:
    if cdp_endpoint.startswith('ws://') or cdp_endpoint.startswith('wss://'):
        return cdp_endpoint
    version_url = cdp_endpoint.rstrip('/') + '/json/version'
    with urllib.request.urlopen(version_url, timeout=5) as r:
        payload = json.loads(r.read().decode('utf-8', 'ignore'))
    ws_url = payload.get('webSocketDebuggerUrl')
    return str(ws_url or cdp_endpoint)


async def connect_browser(cdp_endpoint: str) -> tuple[Playwright, Browser]:
    p = await async_playwright().start()
    browser = await p.chromium.connect_over_cdp(_resolve_cdp_endpoint(cdp_endpoint))
    return p, browser


async def _page_is_usable(page: Page) -> bool:
    if page.is_closed():
        return False
    try:
        await page.wait_for_load_state('domcontentloaded', timeout=5000)
    except Exception:
        pass
    try:
        await page.title()
        return True
    except Exception:
        return False


async def _current_unread_count(page: Page) -> int | None:
    try:
        title = await page.title()
    except Exception:
        return None
    m = UNREAD_TITLE_RE.search(title or '')
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


async def attach_page(browser: Browser, *, prefer_existing_mail_tab: bool = True) -> Page:
    contexts = browser.contexts
    if not contexts:
        raise RuntimeError('No browser contexts found. Open Chrome with remote debugging first.')
    ctx = contexts[0]
    live_pages = [page for page in ctx.pages if not page.is_closed()]

    if prefer_existing_mail_tab:
        for page in live_pages:
            if 'mail.163.com' in page.url and await _page_is_usable(page):
                return page

    page = await ctx.new_page()
    await page.goto('https://mail.163.com/', wait_until='domcontentloaded', timeout=30000)
    if not await _page_is_usable(page):
        raise RuntimeError('Newly opened 163 page became unusable immediately. Keep Chrome open and retry.')
    return page


async def classify_page(page: Page) -> tuple[str, str]:
    url = page.url
    try:
        title = await page.title()
    except Exception:
        title = ''
    body = ''
    try:
        body = await page.locator('body').inner_text(timeout=5000)
    except Exception:
        body = ''
    text = f'{title}\n{body[:4000]}'

    if any(h in text for h in ERROR_HINTS):
        return 'error', text[:1000]

    inbox_like = (
        'js6/main.jsp' in url
        or '#module=mbox.' in url
        or '收件箱(' in text
        or sum(1 for h in INBOX_HINTS if h in text) >= 2
    )
    if inbox_like:
        return 'inbox', text[:1000]

    explicit_login = any(h in text for h in LOGIN_HINTS)
    explicit_verification = any(h in text for h in CAPTCHA_HINTS)
    if explicit_verification or explicit_login:
        return 'manual_verification', text[:1000]

    if '网易电子邮箱' in title and 'mail.163.com' in url:
        return 'unknown', text[:1000]
    return 'unknown', text[:1000]


async def capture_diag(page: Page, prefix: str) -> dict[str, str]:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    html_path = DIAG_DIR / f'{prefix}_{ts}.html'
    png_path = DIAG_DIR / f'{prefix}_{ts}.png'
    try:
        html_path.write_text(await page.content(), encoding='utf-8')
    except Exception:
        pass
    try:
        await page.screenshot(path=str(png_path), full_page=True)
    except Exception:
        pass
    return {'html': str(html_path), 'png': str(png_path)}


VISIBLE_ROW_JS = r'''
() => {
  const isRenderable = (el) => {
    const st = window.getComputedStyle(el);
    if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    if (r.width <= 20 || r.height <= 12) return false;
    return true;
  };

  const textNorm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const coreNorm = (s) => textNorm(s)
    .replace(/^Google 学术搜索快讯\s*/i, '')
    .replace(/^Google Scholar\s*/i, '')
    .replace(/\s+(今日|昨日|星期[一二三四五六日天]|\d+月\d+日|\d{1,2}:\d{2})$/i, '')
    .trim();

  const picked = new Map();
  const letterNodes = [...document.querySelectorAll('[role="link"][sign="letter"]')];

  for (const el of letterNodes) {
    if (!isRenderable(el)) continue;
    const txt = textNorm(el.innerText || '');
    const aria = textNorm(el.getAttribute('aria-label') || '');
    const combined = textNorm(`${txt} ${aria}`);
    if (combined.length < 20 || combined.length > 1200) continue;

    const hasScholarSender = /发件人\s*[：:]\s*google 学术搜索快讯|发件人\s*[：:]\s*google scholar|google 学术搜索快讯|google scholar/i.test(combined);
    if (!hasScholarSender) continue;

    const subjectMatch = combined.match(/(\[收件箱\][^\n]+?|[^\n]+?)(?:\s+(今日|昨日|星期[一二三四五六日天]|\d+月\d+日|\d{1,2}:\d{2})|\s+时间\s*[：:]|\s+发件人\s*[：:]|$)/i);
    const subjectText = subjectMatch ? textNorm(subjectMatch[1]) : textNorm(txt);
    const core = coreNorm(subjectText);
    if (!core) continue;

    const dateMatch = combined.match(/(\d+月\d+日|今日|昨日|星期[一二三四五六日天]|\d{4}年\d+月\d+日)/i);
    const rect = el.getBoundingClientRect();
    const href = el.getAttribute('href') || null;
    const dateHint = dateMatch ? dateMatch[1] : null;
    const dedupeKey = `${core} || ${dateHint || ''}`;
    const isUnread = /未读|aria-checked\s*=\s*"false"/i.test(combined);
    const candidate = {
      text: txt || combined,
      aria_label: aria || null,
      sender_hint: 'Google 学术搜索快讯',
      sender: 'Google 学术搜索快讯',
      subject_core: core,
      subject: core,
      date_hint: dateHint,
      date_text: dateHint,
      node_id: el.id || null,
      mail_key: dedupeKey,
      href,
      url: href,
      row_key: [Math.round(rect.top), Math.round(rect.left), core.slice(0,120)].join('|'),
      unread_guess: isUnread,
      is_unread: isUnread,
      bbox: {x: rect.x, y: rect.y, w: rect.width, h: rect.height},
      _score: 10000 + txt.length
    };

    const prev = picked.get(dedupeKey);
    if (!prev || candidate._score > prev._score) {
      picked.set(dedupeKey, candidate);
    }
  }

  return [...picked.values()]
    .sort((a, b) => (a.bbox.y - b.bbox.y) || (a.bbox.x - b.bbox.x))
    .slice(0, 200)
    .map(({ _score, ...row }) => row);
}
'''


async def extract_visible_rows(page: Page) -> list[dict[str, Any]]:
    rows = await page.evaluate(VISIBLE_ROW_JS)
    return rows if isinstance(rows, list) else []


SCROLL_LIST_JS = r'''
() => {
  const letters = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  let best = null;
  let bestScore = -1;
  for (const letter of letters) {
    let cur = letter.parentElement;
    while (cur) {
      const st = window.getComputedStyle(cur);
      const scrollable = /(auto|scroll)/i.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 100;
      if (scrollable) {
        const count = cur.querySelectorAll('[role="link"][sign="letter"]').length;
        const score = count * 100000 + (cur.clientHeight || 0);
        if (score > bestScore) {
          best = cur;
          bestScore = score;
        }
      }
      cur = cur.parentElement;
    }
  }

  const target = best || document.scrollingElement || document.documentElement;
  const before = target.scrollTop || 0;
  const delta = Math.max(300, Math.floor(((target.clientHeight || window.innerHeight || 800) * 0.8)));
  target.scrollTop = before + delta;
  return {
    moved: (target.scrollTop || 0) > before,
    before,
    after: target.scrollTop || 0,
    delta,
    tag: target.tagName || null,
    id: target.id || null,
    className: target.className || null,
  };
}
'''


RESET_SCROLL_JS = r'''
() => {
  const letters = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  let best = null;
  let bestScore = -1;
  for (const letter of letters) {
    let cur = letter.parentElement;
    while (cur) {
      const st = window.getComputedStyle(cur);
      const scrollable = /(auto|scroll)/i.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 100;
      if (scrollable) {
        const count = cur.querySelectorAll('[role="link"][sign="letter"]').length;
        const score = count * 100000 + (cur.clientHeight || 0);
        if (score > bestScore) {
          best = cur;
          bestScore = score;
        }
      }
      cur = cur.parentElement;
    }
  }
  const target = best || document.scrollingElement || document.documentElement;
  target.scrollTop = 0;
  return {tag: target.tagName || null, id: target.id || null, className: target.className || null};
}
'''


def _row_sort_key(row: dict[str, Any]) -> tuple[float, float, str]:
    bbox = row.get('bbox') or {}
    return (
        float(bbox.get('y', 0.0) or 0.0),
        float(bbox.get('x', 0.0) or 0.0),
        str(row.get('subject_core') or row.get('subject') or row.get('text') or ''),
    )


def _logical_mail_key(row: dict[str, Any]) -> str:
    subject = str(row.get('subject_core') or row.get('subject') or row.get('text') or '').strip()
    date_hint = str(row.get('date_hint') or row.get('date_text') or '').strip()
    return f'{subject} || {date_hint}'


def _rounded_row_y(row: dict[str, Any]) -> int:
    bbox = row.get('bbox') or {}
    return round(float(bbox.get('y', 0.0) or 0.0))


def _row_richness(row: dict[str, Any]) -> int:
    return sum(len(str(row.get(k) or '')) for k in ['text', 'aria_label', 'href', 'subject_core', 'date_hint'])


def _collapse_snapshot_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    picked: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (_logical_mail_key(row), _rounded_row_y(row))
        prev = picked.get(key)
        if prev is None or _row_richness(row) > _row_richness(prev):
            picked[key] = row
    return sorted(picked.values(), key=_row_sort_key)


def _local_sequence_key(rows: list[dict[str, Any]], idx: int, window: int = 3) -> str:
    start = max(0, idx - window)
    end = min(len(rows), idx + window + 1)
    parts: list[str] = []
    for j in range(start, end):
        parts.append(f'{j - idx:+d}:{_logical_mail_key(rows[j])}')
    return ' ### '.join(parts)


def _sequence_dedup_rows(snapshot_batches: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    picked: dict[str, dict[str, Any]] = {}
    for batch_idx, batch in enumerate(snapshot_batches):
        ordered = _collapse_snapshot_rows(batch)
        for row_idx, row in enumerate(ordered):
            sequence_key = _local_sequence_key(ordered, row_idx)
            final_key = sequence_key or _logical_mail_key(row)
            enriched = dict(row)
            enriched['raw_mail_key'] = row.get('mail_key')
            enriched['sequence_key'] = sequence_key
            enriched['mail_key'] = final_key
            enriched['snapshot_batch'] = batch_idx
            prev = picked.get(final_key)
            if prev is None or _row_richness(enriched) > _row_richness(prev):
                picked[final_key] = enriched
    rows = sorted(picked.values(), key=_row_sort_key)
    for idx, row in enumerate(rows, start=1):
        row['row_index'] = idx
    return rows


async def collect_rows_for_current_page(page: Page, max_scroll_steps: int = 20) -> list[dict[str, Any]]:
    try:
        await page.evaluate(RESET_SCROLL_JS)
        await page.wait_for_timeout(300)
    except Exception:
        pass

    snapshot_batches: list[list[dict[str, Any]]] = []
    snapshot_batches.append(await extract_visible_rows(page))
    for _ in range(max_scroll_steps):
        try:
            info = await page.evaluate(SCROLL_LIST_JS)
            await page.wait_for_timeout(500)
        except Exception:
            break
        snapshot_batches.append(await extract_visible_rows(page))
        if not info.get('moved'):
            break
    return _sequence_dedup_rows(snapshot_batches)


async def _click_pager(page: Page, direction: str) -> bool:
    assert direction in {'next', 'prev'}
    if direction == 'next':
        text_candidates = ['下一页', '下页', '后一页', '下一封', 'next', '>']
        selector_candidates = [
            'a[title="下一页"]',
            'button[title="下一页"]',
            '[aria-label="下一页"]',
            'a.nui-page-next',
            '.nui-page-next',
            '.js-component-next',
        ]
    else:
        text_candidates = ['上一页', '上页', '前一页', 'prev', '<']
        selector_candidates = [
            'a[title="上一页"]',
            'button[title="上一页"]',
            '[aria-label="上一页"]',
            'a.nui-page-prev',
            '.nui-page-prev',
            '.js-component-prev',
        ]

    for label in text_candidates:
        loc = page.get_by_text(label, exact=False)
        try:
            if await loc.count() > 0:
                await loc.first.click(timeout=3000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                return True
        except Exception:
            pass

    for selector in selector_candidates:
        try:
            loc = page.locator(selector)
            if await loc.count() > 0 and await loc.first.is_visible():
                await loc.first.click(timeout=3000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                return True
        except Exception:
            pass
    return False


async def click_next_page(page: Page) -> bool:
    return await _click_pager(page, 'next')


async def click_prev_page(page: Page) -> bool:
    return await _click_pager(page, 'prev')


async def _current_list_page_info(page: Page) -> dict[str, int | None]:
    script = r'''
() => {
  const nodes = Array.from(document.querySelectorAll('.nui-select-text, [class*="select-text"]'));
  const texts = nodes.map(n => (n.innerText || n.textContent || '').trim()).filter(Boolean);
  for (const t of texts) {
    const m = t.match(/^(\d+)\/(\d+)$/);
    if (m) {
      return { current: Number(m[1]), total: Number(m[2]) };
    }
  }
  return { current: null, total: null };
}
'''
    try:
        info = await page.evaluate(script)
    except Exception:
        return {'current': None, 'total': None}
    if not isinstance(info, dict):
        return {'current': None, 'total': None}
    return {
        'current': int(info.get('current')) if info.get('current') is not None else None,
        'total': int(info.get('total')) if info.get('total') is not None else None,
    }


async def _reset_to_first_list_page(page: Page, *, max_prev_clicks: int = 3) -> dict[str, Any]:
    info = await _current_list_page_info(page)
    current = info.get('current')
    if current is None or current <= 1:
        return {'ok': True, 'clicks': 0, 'current': current}
    if current > (max_prev_clicks + 1):
        return {'ok': False, 'clicks': 0, 'current': current}
    clicks = 0
    while current is not None and current > 1 and clicks < max_prev_clicks:
        moved = await click_prev_page(page)
        if not moved:
            break
        clicks += 1
        await page.wait_for_timeout(600)
        info = await _current_list_page_info(page)
        current = info.get('current')
    return {'ok': current == 1, 'clicks': clicks, 'current': current}


async def _ensure_list_page(page: Page, target_page: int, *, max_moves: int = 6) -> dict[str, Any]:
    target_page = max(1, int(target_page or 1))
    info = await _current_list_page_info(page)
    current = info.get('current')
    if current is None:
        return {'ok': target_page == 1, 'moves': 0, 'current': None, 'target': target_page}
    moves = 0
    while current != target_page and moves < max_moves:
        if current < target_page:
            moved = await click_next_page(page)
        else:
            moved = await click_prev_page(page)
        if not moved:
            break
        moves += 1
        await page.wait_for_timeout(700)
        info = await _current_list_page_info(page)
        current = info.get('current')
    return {'ok': current == target_page, 'moves': moves, 'current': current, 'target': target_page}


async def _probe_sweep_page(page: Page) -> dict[str, int]:
    script = r'''
() => {
  const textNorm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const isRenderable = (el) => {
    const st = window.getComputedStyle(el);
    if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 20 && r.height > 12;
  };
  const letterNodes = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  const renderable = letterNodes.filter(isRenderable);
  const scholarLike = renderable.filter((el) => {
    const txt = textNorm(el.innerText || '');
    const aria = textNorm(el.getAttribute('aria-label') || '');
    const combined = textNorm(`${txt} ${aria}`);
    return /发件人\s*[：:]\s*google 学术搜索快讯|发件人\s*[：:]\s*google scholar|google 学术搜索快讯|google scholar/i.test(combined);
  });
  return {
    letter_count: letterNodes.length,
    renderable_letter_count: renderable.length,
    scholar_like_count: scholarLike.length,
  };
}
'''
    try:
        result = await page.evaluate(script)
    except Exception:
        return {'letter_count': 0, 'renderable_letter_count': 0, 'scholar_like_count': 0}
    if not isinstance(result, dict):
        return {'letter_count': 0, 'renderable_letter_count': 0, 'scholar_like_count': 0}
    return {
        'letter_count': int(result.get('letter_count') or 0),
        'renderable_letter_count': int(result.get('renderable_letter_count') or 0),
        'scholar_like_count': int(result.get('scholar_like_count') or 0),
    }


async def _wait_for_sweep_page_ready(page: Page, *, timeout_ms: int = 12000, poll_ms: int = 500) -> dict[str, int]:
    deadline = time.perf_counter() + (timeout_ms / 1000.0)
    last = {'letter_count': 0, 'renderable_letter_count': 0, 'scholar_like_count': 0}
    while True:
        last = await _probe_sweep_page(page)
        if last.get('scholar_like_count', 0) > 0 or last.get('renderable_letter_count', 0) > 0:
            return last
        if time.perf_counter() >= deadline:
            return last
        await page.wait_for_timeout(poll_ms)


def _effective_search_page_limit(target: dict[str, Any], default_limit: int) -> int:
    try:
        target_page_no = int(target.get('page_no') or 1)
    except Exception:
        target_page_no = 1
    target_page_no = max(1, target_page_no)
    return max(1, min(default_limit, target_page_no))


def _clean_match_text(value: str | None) -> str:
    if not value:
        return ''
    return ''.join(str(value).replace('[收件箱]', ' ').split()).strip().casefold()


def _date_match(a: str | None, b: str | None) -> bool:
    aa = ''.join(str(a or '').split())
    bb = ''.join(str(b or '').split())
    if not aa or not bb:
        return True
    return aa == bb or aa in bb or bb in aa


def _load_jsonl_records(path: Path, *, start_offset: int = 0, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f'JSONL not found: {path}')
    records: list[dict[str, Any]] = []
    with path.open('r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx < start_offset:
                continue
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                records.append(obj)
            if limit is not None and len(records) >= limit:
                break
    return records


def _load_existing_body_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen: set[str] = set()
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            key = str(obj.get('mail_key') or obj.get('raw_mail_key') or '').strip()
            if key:
                seen.add(key)
    return seen


CLICK_ROW_JS = r'''
({ subject, dateText, nodeId }) => {
  const textNorm = (s) => (s || '').replace(/\s+/g, '').replace(/\[收件箱\]/g, '').trim().toLowerCase();
  const targetSubject = textNorm(subject || '');
  const targetDate = (dateText || '').replace(/\s+/g, '').trim();
  const isRenderable = (el) => {
    const st = window.getComputedStyle(el);
    if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 20 && r.height > 12;
  };

  let matched = null;
  if (nodeId) {
    const direct = document.getElementById(nodeId);
    if (direct && direct.matches('[role="link"][sign="letter"]') && isRenderable(direct)) {
      matched = direct;
    }
  }

  const rows = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  if (!matched) {
    for (const el of rows) {
      if (!isRenderable(el)) continue;
      const combined = `${el.innerText || ''} ${el.getAttribute('aria-label') || ''}`;
      const text = textNorm(combined);
      if (!targetSubject || !text.includes(targetSubject)) continue;

      const rawText = (combined || '').replace(/\s+/g, ' ').trim();
      const dateMatch = rawText.match(/(\d{4}年\d+月\d+日\s*\d{1,2}:\d{2}|\d+月\d+日|今日|昨日|星期[一二三四五六日天])/i);
      const currentDate = dateMatch ? dateMatch[1].replace(/\s+/g, '') : '';
      if (targetDate && currentDate && !(targetDate === currentDate || targetDate.includes(currentDate) || currentDate.includes(targetDate))) {
        continue;
      }
      matched = el;
      break;
    }
  }

  if (!matched) {
    return { clicked: false };
  }
  matched.scrollIntoView({ block: 'center' });
  matched.click();
  return { clicked: true };
}
'''


EXTRACT_MAIL_BODY_JS = r'''
({ targetSubject }) => {
  const textNorm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const subjectNorm = textNorm((targetSubject || '').replace(/^\[收件箱\]/, ''));

  // ── 1. Detect and extract from Scholar email iframe first ──────────────────
  // 163 Scholar alert emails load content inside an iframe (id ends with _frameBody).
  // The outer document is 163 chrome/UI; the iframe holds the actual email body.
  const tryIframe = () => {
    const iframeEl = document.querySelector('iframe[id$="_frameBody"]');
    if (!iframeEl) return null;
    let iframeDoc = null;
    try {
      iframeDoc = iframeEl.contentDocument || iframeEl.contentWindow?.document;
    } catch (_) {
      // cross-origin iframe, cannot access
    }
    if (!iframeDoc || !iframeDoc.body) return null;
    const body = iframeDoc.body;
    const text = textNorm(body.innerText || '');
    if (text.length < 100) return null;
    const linkCount = body.querySelectorAll('a[href]').length;
    const hintMatches = [
      'google scholar', 'google 学术', 'scholaralerts-noreply',
      '新的相关研究工作', '相关文章', '新增了', '引用',
      'new articles', 'related articles', 'new citations',
      'Brian Wandell', 'Stephen M. Smith', 'Kamil Ugurbil',
      'Peter A. Bandettini', 'Arno Villringer'
    ].reduce((acc, h) => acc + (text.toLowerCase().includes(h) ? 1 : 0), 0);
    const rect = body.getBoundingClientRect();
    const score = Math.min(text.length, 15000) + linkCount * 120 + hintMatches * 600;
    return {
      score,
      tag: body.tagName,
      className: body.className || null,
      id: body.id || null,
      text,
      html: body.innerHTML || null,
      link_count: linkCount,
      hint_matches: hintMatches,
      bbox: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
      source: 'iframe',
      iframe_id: iframeEl.id,
      iframe_url: iframeEl.src || null,
    };
  };

  const iframeResult = tryIframe();
  if (iframeResult) return iframeResult;

  // ── 2. Fallback: score elements in the current document ──────────────────
  const isVisible = (el) => {
    const st = window.getComputedStyle(el);
    if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 40 && r.height > 20;
  };

  const selectors = [
    '[class*="mail"]', '[class*="read"]', '[class*="content"]',
    '[class*="article"]', '[class*="viewer"]', '[class*="body"]',
    'article', 'main', 'section', 'div', 'td', 'table', 'body'
  ];

  let best = null;
  const seen = new Set();
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      if (seen.has(el)) continue;
      seen.add(el);
      if (!isVisible(el)) continue;
      const text = textNorm(el.innerText || '');
      if (text.length < 120) continue;
      const linkCount = el.querySelectorAll('a[href]').length;
      const imgCount = el.querySelectorAll('img').length;
      const hintMatches = [
        'google scholar', 'google 学术', 'scholaralerts-noreply',
        '新的相关研究工作', '相关文章', '新增了', '引用',
        'new articles', 'related articles', 'new citations'
      ].reduce((acc, hint) => acc + (text.toLowerCase().includes(hint) ? 1 : 0), 0);
      const rect = el.getBoundingClientRect();
      let score = Math.min(text.length, 12000) + linkCount * 90 + imgCount * 10 + hintMatches * 500;
      if (subjectNorm && text.includes(subjectNorm)) score += 900;
      if (rect.width > 500) score += 120;
      if (rect.height > 300) score += 120;
      if (text.length > 50000) score -= 1000;
      if (linkCount >= 3) score += 200;
      if (!best || score > best.score) {
        best = {
          score,
          tag: el.tagName,
          className: el.className || null,
          id: el.id || null,
          text,
          html: el.outerHTML || null,
          link_count: linkCount,
          hint_matches: hintMatches,
          bbox: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
          source: 'dom',
        };
      }
    }
  }
  return best;
}
'''


async def _return_to_inbox(page: Page, inbox_url: str, *, expected_page_no: int | None = None) -> dict[str, Any]:
    if expected_page_no is not None:
        try:
            await page.go_back(wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(1000)
            status, _ = await classify_page(page)
            if status == 'inbox':
                info = await _current_list_page_info(page)
                readiness = await _wait_for_sweep_page_ready(page, timeout_ms=6000, poll_ms=400)
                current_page = info.get('current')
                page_ok = current_page == expected_page_no and readiness.get('renderable_letter_count', 0) > 0
                if not page_ok and inbox_url:
                    readiness, info = await _reload_list_page(page, inbox_url, wait_ms=2200)
                    current_page = info.get('current')
                    page_ok = current_page == expected_page_no and readiness.get('renderable_letter_count', 0) > 0
                    return {
                        'method': 'history_back+goto_reload',
                        'page_ok': page_ok,
                        'current_page': current_page,
                        'readiness': readiness,
                    }
                return {
                    'method': 'history_back',
                    'page_ok': page_ok,
                    'current_page': current_page,
                    'readiness': readiness,
                }
        except Exception:
            pass

    readiness, info = await _reload_list_page(page, inbox_url, wait_ms=2200)
    current_page = info.get('current')
    return {
        'method': 'goto',
        'page_ok': expected_page_no is not None and current_page == expected_page_no and readiness.get('renderable_letter_count', 0) > 0,
        'current_page': current_page,
        'readiness': readiness,
    }


async def _search_and_open_target(page: Page, target: dict[str, Any], *, search_page_limit: int) -> tuple[bool, str]:
    target_subject = str(target.get('subject') or '').strip()
    target_date = str(target.get('date_text') or '').strip()
    effective_limit = _effective_search_page_limit(target, search_page_limit)

    for _ in range(effective_limit):
        rows, _, _ = await _collect_rows_for_current_page_resilient(
            page,
            current_page_url=page.url,
            expected_page_no=(await _current_list_page_info(page)).get('current'),
            max_scroll_steps=8,
        )
        matched = None
        for row in rows:
            if _clean_match_text(row.get('subject')) != _clean_match_text(target_subject):
                continue
            if not _date_match(row.get('date_text'), target_date):
                continue
            matched = row
            break

        if matched is not None:
            clicked = await page.evaluate(CLICK_ROW_JS, {
                'subject': target_subject,
                'dateText': target_date,
                'nodeId': matched.get('node_id'),
            })
            await page.wait_for_timeout(400)
            return bool(clicked.get('clicked')), str(matched.get('subject') or '')

        next_clicked = await click_next_page(page)
        if not next_clicked:
            break
        await page.wait_for_timeout(900)

    return False, ''


async def _extract_open_mail_payload(page: Page, target: dict[str, Any], *, timeout_ms: int = 6500, poll_ms: int = 300) -> dict[str, Any] | None:
    target_subject = str(target.get('subject') or '')
    deadline = time.perf_counter() + (timeout_ms / 1000.0)
    best: dict[str, Any] | None = None
    while True:
        for frame in page.frames:
            try:
                payload = await frame.evaluate(EXTRACT_MAIL_BODY_JS, {'targetSubject': target_subject})
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            payload = dict(payload)
            payload['frame_url'] = frame.url
            text_len = len(str(payload.get('text') or '').strip())
            html_len = len(str(payload.get('html') or '').strip())
            if text_len < 120 and html_len < 120:
                continue
            if best is None or float(payload.get('score', 0) or 0) > float(best.get('score', 0) or 0):
                best = payload
        if best is not None:
            return best
        if time.perf_counter() >= deadline:
            return best
        await page.wait_for_timeout(poll_ms)


def _stable_body_mail_uid(target: dict[str, Any]) -> str:
    identity = '|'.join(
        str(target.get(k) or '')
        for k in ['raw_mail_key', 'mail_key', 'subject', 'date_text', 'page_no', 'row_index']
    )
    digest = hashlib.sha1(identity.encode('utf-8')).hexdigest()[:16]
    return f'local163_{digest}'


def _source_key(target: dict[str, Any]) -> str:
    return str(target.get('raw_mail_key') or target.get('mail_key') or '').strip()


def _normalized_read_mid_token(value: str | None) -> str:
    return ''.join(str(value or '').replace(':', '').replace('+', '').split()).strip()


def _node_id_mid_token(node_id: str | None) -> str:
    raw = str(node_id or '').strip()
    if not raw:
        return ''
    return re.sub(r'^\d+_|\d+Dom$', '', raw)


def _mid_from_node_id(node_id: str | None) -> str | None:
    token = _node_id_mid_token(node_id)
    if not token:
        return None
    m = re.match(r'^(\d+)([a-zA-Z0-9_-]+)$', token)
    if not m:
        return None
    return f'{m.group(1)}:{m.group(2)}'


async def _page_visible_mid_map(page: Page) -> dict[str, str]:
    try:
        html = await page.content()
    except Exception:
        return {}
    mids = re.findall(r'readhtml3\.jsp\?mid=([^&"\'<> ]+)', html)
    token_to_mid: dict[str, str] = {}
    for raw_mid in mids:
        mid = raw_mid.replace('&amp;', '&').split('&', 1)[0]
        token = _normalized_read_mid_token(mid)
        if token and token not in token_to_mid:
            token_to_mid[token] = mid
    return token_to_mid


def _attach_read_mid_fields(rows: list[dict[str, Any]], token_to_mid: dict[str, str]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        row2 = dict(row)
        token = _node_id_mid_token(row2.get('node_id'))
        if token:
            row2['read_mid_token'] = token
            mid = token_to_mid.get(token)
            if mid:
                row2['read_mid'] = mid
                row2['read_route_id'] = mid
                row2['read_mid_source'] = 'page_source_regex'
            else:
                derived_mid = _mid_from_node_id(row2.get('node_id'))
                if derived_mid:
                    row2['read_mid'] = derived_mid
                    row2['read_route_id'] = derived_mid
                    row2['read_mid_source'] = 'node_id_derived'
        enriched.append(row2)
    return enriched


async def _reload_list_page(page: Page, list_url: str, *, wait_ms: int = 2500) -> tuple[dict[str, int], dict[str, int | None]]:
    await page.goto(list_url, wait_until='domcontentloaded', timeout=30000)
    await page.wait_for_timeout(wait_ms)
    readiness = await _wait_for_sweep_page_ready(page, timeout_ms=6000, poll_ms=400)
    info = await _current_list_page_info(page)
    return readiness, info


async def _soft_reset_list_session(page: Page, current_page_url: str, *, expected_page_no: int | None = None, wait_ms: int = SOFT_RESET_WAIT_MS) -> dict[str, Any]:
    readiness, info = await _reload_list_page(page, current_page_url, wait_ms=wait_ms)
    current_page = info.get('current')
    ok = expected_page_no is None or current_page == expected_page_no
    return {
        'ok': ok and readiness.get('renderable_letter_count', 0) > 0,
        'current_page': current_page,
        'readiness': readiness,
        'method': 'goto_soft_reset',
    }


async def _collect_rows_for_current_page_resilient(page: Page, *, current_page_url: str, expected_page_no: int | None = None, max_scroll_steps: int = 8) -> tuple[list[dict[str, Any]], dict[str, int], str]:
    readiness = await _wait_for_sweep_page_ready(page, timeout_ms=12000, poll_ms=500)
    rows = await collect_rows_for_current_page(page, max_scroll_steps=max_scroll_steps)
    rows = _attach_read_mid_fields(rows, await _page_visible_mid_map(page))
    if rows:
        return rows, readiness, 'direct'
    if current_page_url and (readiness.get('letter_count', 0) > 0 or readiness.get('renderable_letter_count', 0) == 0):
        readiness, info = await _reload_list_page(page, current_page_url, wait_ms=2500)
        if expected_page_no is None or info.get('current') == expected_page_no:
            rows = await collect_rows_for_current_page(page, max_scroll_steps=max_scroll_steps)
            rows = _attach_read_mid_fields(rows, await _page_visible_mid_map(page))
            if rows:
                return rows, readiness, 'goto_reload'
    return rows, readiness, 'direct'


def _update_body_fetch_progress_state(state: TaskState, *, page_no: int | None = None, row_index: int | None = None, phase: str | None = None, note: str | None = None, extra_artifacts: dict[str, Any] | None = None) -> None:
    if page_no is not None:
        state.page_no = int(page_no)
    if row_index is not None:
        state.indexed_count = int(row_index)
    if phase:
        state.current_step = phase
    if note is not None:
        state.note = note
    if extra_artifacts:
        state.artifacts = (state.artifacts or {}) | extra_artifacts
    save_state(state)


def _body_record(target: dict[str, Any], *, input_jsonl: Path | None, page_url: str, opened_page_url: str, payload: dict[str, Any] | None, body_text: str, body_html: str, target_started_at: datetime, elapsed_seconds: float, source_mode: str) -> dict[str, Any]:
    source_key = _source_key(target)
    return {
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'started_at': target_started_at.isoformat(),
        'elapsed_seconds': round(elapsed_seconds, 3),
        'mail_uid': _stable_body_mail_uid(target),
        'mail_key': source_key or str(target.get('subject') or ''),
        'raw_mail_key': source_key,
        'sequence_key': target.get('sequence_key'),
        'message_id': None,
        'subject': target.get('subject'),
        'sender': target.get('sender') or 'Google 学术搜索快讯',
        'from_address': target.get('sender') or 'scholaralerts-noreply@google.com',
        'internal_date': target.get('date_text'),
        'date_text': target.get('date_text'),
        'is_unread': target.get('is_unread'),
        'page_no': target.get('page_no'),
        'row_index': target.get('row_index'),
        'page_url': page_url,
        'opened_page_url': opened_page_url,
        'source_index_path': str(input_jsonl) if input_jsonl is not None else None,
        'source_mode': source_mode,
        'body_text': body_text,
        'body_html': body_html,
        'body_score': (payload or {}).get('score'),
        'body_source_tag': (payload or {}).get('tag'),
        'body_source_class': (payload or {}).get('className'),
        'body_source_id': (payload or {}).get('id'),
        'body_source': (payload or {}).get('source'),
        'body_iframe_id': (payload or {}).get('iframe_id'),
        'body_iframe_url': (payload or {}).get('iframe_url'),
        'body_frame_url': (payload or {}).get('frame_url'),
        'headers': {
            'subject': str(target.get('subject') or ''),
            'from_address': str(target.get('sender') or 'Google 学术搜索快讯'),
            'date_text': str(target.get('date_text') or ''),
            'opened_page_url': opened_page_url,
        },
    }


async def run_body_fetch(
    state: TaskState,
    *,
    input_jsonl: Path,
    output_jsonl: Path,
    limit: int,
    start_offset: int,
    search_page_limit: int,
) -> int:
    run_started_at = datetime.now(timezone.utc)
    run_started_perf = time.perf_counter()
    targets = _load_jsonl_records(input_jsonl, start_offset=start_offset, limit=limit)
    if not targets:
        raise RuntimeError(f'No targets loaded from {input_jsonl}')

    existing_keys = _load_existing_body_keys(output_jsonl)
    skipped_existing = 0
    success_count = 0
    failure_count = 0

    playwright, browser = await connect_browser(state.cdp_endpoint)
    try:
        page = await attach_page(browser, prefer_existing_mail_tab=True)
        state.current_url = page.url
        inbox_url = _body_fetch_list_url(str(targets[0].get('page_url') or '').strip() or page.url)

        status, summary = await classify_page(page)
        if status != 'inbox':
            state.status = 'waiting_manual_verification' if status == 'manual_verification' else status
            state.mode = 'body_fetch'
            state.current_step = 'waiting for inbox before body fetch'
            state.next_step = 'return to 163 inbox in real Chrome, then rerun the same command'
            state.note = summary[:500]
            state.artifacts = (state.artifacts or {}) | {'body_fetch_diagnostics': await capture_diag(page, status)}
            save_state(state)
            print(json.dumps({'status': state.status, 'url': page.url, 'note': state.note, 'artifacts': state.artifacts}, ensure_ascii=False, indent=2))
            return 2

        state.status = 'body_fetching'
        state.mode = 'body_fetch'
        state.current_step = 'opening indexed Scholar mails and extracting body snapshots'
        state.next_step = 'append import-local-bodies-compatible JSONL rows or inspect diagnostics on failures'
        state.artifacts = (state.artifacts or {}) | {
            'body_jsonl': str(output_jsonl),
            'body_failure_jsonl': str(BODY_FAILURE_JSONL),
            'body_fetch_source_index': str(input_jsonl),
        }
        save_state(state)

        for target in targets:
            target_started_at = datetime.now(timezone.utc)
            target_started_perf = time.perf_counter()
            source_key = str(target.get('raw_mail_key') or target.get('mail_key') or '').strip()
            if source_key and source_key in existing_keys:
                skipped_existing += 1
                continue

            await _return_to_inbox(page, inbox_url)
            reset_info = await _reset_to_first_list_page(page, max_prev_clicks=3)
            current_page = reset_info.get('current')
            if not reset_info.get('ok'):
                state.status = 'waiting_manual_reset'
                state.mode = 'body_fetch'
                state.current_step = 'inbox list drifted beyond auto-reset range'
                state.next_step = 'manually return the 163 inbox list to page 1, then rerun the same command'
                state.note = f'current inbox page drifted to {current_page}; auto-reset only handles shallow drift (<= page 4)'
                state.artifacts = (state.artifacts or {}) | {'body_fetch_diagnostics': await capture_diag(page, 'body_fetch_page_drift')}
                save_state(state)
                print(json.dumps({
                    'status': state.status,
                    'note': state.note,
                    'current_page': current_page,
                    'expected_inbox_page': 1,
                    'auto_reset_clicks': reset_info.get('clicks'),
                    'url': page.url,
                    'artifacts': state.artifacts,
                }, ensure_ascii=False, indent=2))
                return 2
            opened, matched_subject = await _search_and_open_target(page, target, search_page_limit=search_page_limit)
            if not opened:
                failure_count += 1
                diag = await capture_diag(page, 'body_fetch_not_found')
                append_jsonl(BODY_FAILURE_JSONL, {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'started_at': target_started_at.isoformat(),
                    'elapsed_seconds': round(time.perf_counter() - target_started_perf, 3),
                    'reason': 'not_found_in_unread_pages',
                    'source_index_path': str(input_jsonl),
                    'page_url': page.url,
                    'target': target,
                    'diagnostics': diag,
                })
                state.note = f'not found: {target.get("subject")}'
                state.artifacts = (state.artifacts or {}) | {'last_failure_diagnostics': diag}
                save_state(state)
                continue

            payload = await _extract_open_mail_payload(page, target)
            body_text = str((payload or {}).get('text') or '').strip()
            body_html = str((payload or {}).get('html') or '').strip()
            if len(body_text) < 120 and len(body_html) < 120:
                failure_count += 1
                diag = await capture_diag(page, 'body_fetch_extract_failed')
                append_jsonl(BODY_FAILURE_JSONL, {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'started_at': target_started_at.isoformat(),
                    'elapsed_seconds': round(time.perf_counter() - target_started_perf, 3),
                    'reason': 'body_extract_failed',
                    'page_url': page.url,
                    'matched_subject': matched_subject,
                    'target': target,
                    'payload_probe': payload,
                    'diagnostics': diag,
                })
                state.note = f'extract failed: {target.get("subject")}'
                state.artifacts = (state.artifacts or {}) | {'last_failure_diagnostics': diag}
                save_state(state)
                continue

            record = {
                'captured_at': datetime.now(timezone.utc).isoformat(),
                'started_at': target_started_at.isoformat(),
                'elapsed_seconds': round(time.perf_counter() - target_started_perf, 3),
                'mail_uid': _stable_body_mail_uid(target),
                'mail_key': source_key or str(target.get('subject') or ''),
                'raw_mail_key': source_key,
                'sequence_key': target.get('sequence_key'),
                'message_id': None,
                'subject': target.get('subject'),
                'sender': target.get('sender') or 'Google 学术搜索快讯',
                'from_address': target.get('sender') or 'scholaralerts-noreply@google.com',
                'internal_date': target.get('date_text'),
                'date_text': target.get('date_text'),
                'is_unread': target.get('is_unread'),
                'page_no': target.get('page_no'),
                'row_index': target.get('row_index'),
                'page_url': inbox_url,
                'opened_page_url': page.url,
                'source_index_path': str(input_jsonl),
                'body_text': body_text,
                'body_html': body_html,
                'body_score': (payload or {}).get('score'),
                'body_source_tag': (payload or {}).get('tag'),
                'body_source_class': (payload or {}).get('className'),
                'body_source_id': (payload or {}).get('id'),
                'body_source': (payload or {}).get('source'),
                'body_iframe_id': (payload or {}).get('iframe_id'),
                'body_iframe_url': (payload or {}).get('iframe_url'),
                'body_frame_url': (payload or {}).get('frame_url'),
                'headers': {
                    'subject': str(target.get('subject') or ''),
                    'from_address': str(target.get('sender') or 'Google 学术搜索快讯'),
                    'date_text': str(target.get('date_text') or ''),
                    'opened_page_url': page.url,
                },
            }
            append_jsonl(output_jsonl, record)
            existing_keys.add(record['mail_key'])
            success_count += 1
            state.body_fetched_count += 1
            state.last_row_key = str(target.get('subject') or '')
            save_state(state)

        state.status = 'completed' if success_count > 0 and failure_count == 0 else 'completed_with_failures'
        state.current_step = 'body fetch run finished'
        state.next_step = 'run import-local-bodies on fetched JSONL or inspect failure diagnostics before retrying'
        state.note = f'success={success_count}; skipped_existing={skipped_existing}; failures={failure_count}'
        state.artifacts = (state.artifacts or {}) | {
            'body_fetch_completion': await capture_diag(page, 'body_fetch_completion')
        }
        save_state(state)
        run_elapsed_seconds = round(time.perf_counter() - run_started_perf, 3)
        print(json.dumps({
            'status': state.status,
            'started_at': run_started_at.isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': run_elapsed_seconds,
            'target_count': len(targets),
            'success': success_count,
            'skipped_existing': skipped_existing,
            'failures': failure_count,
            'avg_seconds_per_success': round(run_elapsed_seconds / success_count, 3) if success_count else None,
            'avg_seconds_per_target': round(run_elapsed_seconds / len(targets), 3) if targets else None,
            'output_jsonl': str(output_jsonl),
            'failure_jsonl': str(BODY_FAILURE_JSONL),
        }, ensure_ascii=False, indent=2))
        return 0 if failure_count == 0 else 1
    finally:
        await playwright.stop()


async def run_body_fetch_sweep(
    state: TaskState,
    *,
    output_jsonl: Path,
    page_limit: int,
    max_targets: int | None,
    start_page: int = 1,
    start_from_current_page: bool = False,
    stop_at_page: int | None = None,
    stop_when_unread_below: int | None = None,
) -> int:
    run_started_at = datetime.now(timezone.utc)
    run_started_perf = time.perf_counter()
    existing_keys = _load_existing_body_keys(output_jsonl)
    skipped_existing = 0
    success_count = 0
    failure_count = 0
    attempted_new = 0
    pages_visited = 0
    reached_target_limit = False
    requested_start_page = max(1, int(start_page or 1))
    effective_start_page = requested_start_page
    page_probes: list[dict[str, Any]] = []
    return_method_counts: dict[str, int] = {'history_back': 0, 'goto': 0, 'goto_soft_reset': 0}
    stop_reason: dict[str, Any] | None = None

    playwright, browser = await connect_browser(state.cdp_endpoint)
    try:
        page = await attach_page(browser, prefer_existing_mail_tab=True)
        state.current_url = page.url

        status, summary = await classify_page(page)
        if status != 'inbox':
            state.status = 'waiting_manual_verification' if status == 'manual_verification' else status
            state.mode = 'body_fetch_sweep'
            state.current_step = 'waiting for inbox before sweep body fetch'
            state.next_step = 'return to the regular 163 inbox in real Chrome, then rerun the same command'
            state.note = summary[:500]
            state.artifacts = (state.artifacts or {}) | {'body_fetch_diagnostics': await capture_diag(page, status)}
            save_state(state)
            print(json.dumps({'status': state.status, 'url': page.url, 'note': state.note, 'artifacts': state.artifacts}, ensure_ascii=False, indent=2))
            return 2

        inbox_url = _body_fetch_list_url(page.url)
        if start_from_current_page:
            start_info = await _current_list_page_info(page)
            current_page = start_info.get('current')
            if current_page is None:
                state.status = 'waiting_manual_reset'
                state.mode = 'body_fetch_sweep'
                state.current_step = 'could not determine current inbox page before sweep start'
                state.next_step = 'open the target inbox page in real Chrome, then rerun with --start-from-current-page'
                state.note = 'current inbox page could not be determined from the visible pager state'
                state.artifacts = (state.artifacts or {}) | {'body_fetch_diagnostics': await capture_diag(page, 'body_fetch_page_unknown')}
                save_state(state)
                print(json.dumps({
                    'status': state.status,
                    'note': state.note,
                    'current_page': current_page,
                    'expected_inbox_page': None,
                    'url': page.url,
                    'artifacts': state.artifacts,
                }, ensure_ascii=False, indent=2))
                return 2
            effective_start_page = max(1, int(current_page))
        else:
            await _return_to_inbox(page, inbox_url)
            ensure_start = await _ensure_list_page(page, requested_start_page, max_moves=max(3, requested_start_page + 1))
            current_page = ensure_start.get('current')
            if not ensure_start.get('ok'):
                state.status = 'waiting_manual_reset'
                state.mode = 'body_fetch_sweep'
                state.current_step = 'failed to reach requested inbox start page before sweep start'
                state.next_step = 'manually open the requested inbox page in real Chrome, then rerun the same command'
                state.note = f'failed to reach requested start page {requested_start_page}; current page={current_page}'
                state.artifacts = (state.artifacts or {}) | {'body_fetch_diagnostics': await capture_diag(page, 'body_fetch_page_drift')}
                save_state(state)
                print(json.dumps({
                    'status': state.status,
                    'note': state.note,
                    'current_page': current_page,
                    'expected_inbox_page': requested_start_page,
                    'auto_reset_clicks': ensure_start.get('moves'),
                    'url': page.url,
                    'artifacts': state.artifacts,
                }, ensure_ascii=False, indent=2))
                return 2
            effective_start_page = requested_start_page

        state.status = 'body_fetching'
        state.mode = 'body_fetch_sweep'
        state.current_step = 'sequentially sweeping inbox pages and extracting Scholar mail bodies'
        state.next_step = 'inspect output JSONL, then run import-local-bodies or enlarge page limit'
        state.artifacts = (state.artifacts or {}) | {
            'body_jsonl': str(output_jsonl),
            'body_failure_jsonl': str(BODY_FAILURE_JSONL),
            'body_fetch_source_index': None,
            'body_fetch_start_page': effective_start_page,
            'body_fetch_started_from_current_page': bool(start_from_current_page),
            'soft_reset_every_pages': SOFT_RESET_EVERY_PAGES,
            'soft_reset_count': 0,
            'stop_at_page': int(stop_at_page) if stop_at_page is not None else None,
            'stop_when_unread_below': int(stop_when_unread_below) if stop_when_unread_below is not None else None,
        }
        save_state(state)

        for page_idx in range(max(1, page_limit)):
            page_info = await _current_list_page_info(page)
            _update_body_fetch_progress_state(state, page_no=page_info.get('current') or (page_idx + 1), row_index=0, phase='body_fetch_sweep:collect_page_rows')
            current_page_no = page_info.get('current') or (page_idx + 1)
            current_page_url = page.url
            rows, readiness, collection_method = await _collect_rows_for_current_page_resilient(
                page,
                current_page_url=current_page_url,
                expected_page_no=current_page_no,
                max_scroll_steps=8,
            )
            pages_visited += 1
            page_probe = {
                'page_no': current_page_no,
                'page_url': current_page_url,
                'collection_method': collection_method,
                **readiness,
                'sweep_rows': len(rows),
            }
            page_probes.append(page_probe)

            if not rows:
                diag = await capture_diag(page, 'body_fetch_sweep_empty_page')
                state.note = f'sweep page {current_page_no} yielded 0 scholar rows'
                state.artifacts = (state.artifacts or {}) | {
                    'body_fetch_diagnostics': diag,
                    'body_fetch_page_probe': page_probe,
                }
                save_state(state)

            current_page_preserved = True
            for row in rows:
                _update_body_fetch_progress_state(state, page_no=current_page_no, row_index=int(row.get('row_index') or 0), phase='body_fetch_sweep:fetch_mail')
                if not current_page_preserved:
                    ensure_info = await _ensure_list_page(page, current_page_no, max_moves=max(3, current_page_no + 1))
                    if not ensure_info.get('ok'):
                        state.status = 'waiting_manual_reset'
                        state.mode = 'body_fetch_sweep'
                        state.current_step = 'failed to restore target inbox page during sweep'
                        state.next_step = 'manually return the 163 inbox list to page 1, then rerun the same command'
                        state.note = f'failed to restore page {current_page_no} during sweep; current page={ensure_info.get("current")}'
                        state.artifacts = (state.artifacts or {}) | {
                            'body_fetch_diagnostics': await capture_diag(page, 'body_fetch_page_drift'),
                            'body_fetch_page_probe': page_probe,
                        }
                        save_state(state)
                        print(json.dumps({
                            'status': state.status,
                            'note': state.note,
                            'current_page': ensure_info.get('current'),
                            'expected_inbox_page': current_page_no,
                            'page_probe': page_probe,
                            'url': page.url,
                            'artifacts': state.artifacts,
                        }, ensure_ascii=False, indent=2))
                        return 2
                    current_page_preserved = True

                row_target = dict(row)
                row_target.setdefault('page_no', current_page_no)
                row_target.setdefault('page_url', current_page_url)
                source_key = _source_key(row_target)
                row_mail_key = str(row_target.get('mail_key') or '').strip()
                if (source_key and source_key in existing_keys) or (row_mail_key and row_mail_key in existing_keys):
                    skipped_existing += 1
                    continue
                if max_targets is not None and attempted_new >= max_targets:
                    reached_target_limit = True
                    break

                attempted_new += 1
                target_started_at = datetime.now(timezone.utc)
                target_started_perf = time.perf_counter()
                clicked = await page.evaluate(CLICK_ROW_JS, {
                    'subject': row_target.get('subject'),
                    'dateText': row_target.get('date_text'),
                    'nodeId': row_target.get('node_id'),
                })
                if clicked.get('clicked'):
                    await page.wait_for_timeout(400)
                else:
                    failure_count += 1
                    diag = await capture_diag(page, 'body_fetch_not_found')
                    append_jsonl(BODY_FAILURE_JSONL, {
                        'captured_at': datetime.now(timezone.utc).isoformat(),
                        'started_at': target_started_at.isoformat(),
                        'elapsed_seconds': round(time.perf_counter() - target_started_perf, 3),
                        'reason': 'not_found_on_sweep_page',
                        'page_url': current_page_url,
                        'target': row_target,
                        'diagnostics': diag,
                    })
                    state.note = f'not found on sweep page: {row_target.get("subject")}'
                    state.artifacts = (state.artifacts or {}) | {'last_failure_diagnostics': diag}
                    save_state(state)
                    continue

                payload = await _extract_open_mail_payload(page, row_target)
                body_text = str((payload or {}).get('text') or '').strip()
                body_html = str((payload or {}).get('html') or '').strip()
                if len(body_text) < 120 and len(body_html) < 120:
                    failure_count += 1
                    diag = await capture_diag(page, 'body_fetch_extract_failed')
                    append_jsonl(BODY_FAILURE_JSONL, {
                        'captured_at': datetime.now(timezone.utc).isoformat(),
                        'started_at': target_started_at.isoformat(),
                        'elapsed_seconds': round(time.perf_counter() - target_started_perf, 3),
                        'reason': 'body_extract_failed',
                        'page_url': page.url,
                        'target': row_target,
                        'payload_probe': payload,
                        'diagnostics': diag,
                    })
                    state.note = f'extract failed: {row_target.get("subject")}'
                    state.artifacts = (state.artifacts or {}) | {'last_failure_diagnostics': diag}
                    save_state(state)
                    return_info = await _return_to_inbox(page, current_page_url, expected_page_no=current_page_no)
                    return_method_counts[str(return_info.get('method') or 'goto')] = return_method_counts.get(str(return_info.get('method') or 'goto'), 0) + 1
                    current_page_preserved = bool(return_info.get('page_ok'))
                    continue

                elapsed_seconds = time.perf_counter() - target_started_perf
                record = _body_record(
                    row_target,
                    input_jsonl=None,
                    page_url=current_page_url,
                    opened_page_url=page.url,
                    payload=payload,
                    body_text=body_text,
                    body_html=body_html,
                    target_started_at=target_started_at,
                    elapsed_seconds=elapsed_seconds,
                    source_mode='sequential_sweep',
                )
                append_jsonl(output_jsonl, record)
                if record['mail_key']:
                    existing_keys.add(record['mail_key'])
                if record['raw_mail_key']:
                    existing_keys.add(record['raw_mail_key'])
                success_count += 1
                state.body_fetched_count += 1
                state.last_row_key = str(row_target.get('subject') or '')
                save_state(state)
                return_info = await _return_to_inbox(page, current_page_url, expected_page_no=current_page_no)
                return_method_counts[str(return_info.get('method') or 'goto')] = return_method_counts.get(str(return_info.get('method') or 'goto'), 0) + 1
                current_page_preserved = bool(return_info.get('page_ok'))

            if reached_target_limit:
                break
            unread_count = await _current_unread_count(page)
            state.artifacts = (state.artifacts or {}) | {
                'current_unread_count': unread_count,
                'last_page_completed': current_page_no,
            }
            save_state(state)
            if stop_when_unread_below is not None and unread_count is not None and unread_count < int(stop_when_unread_below):
                stop_reason = {
                    'kind': 'unread_below_threshold',
                    'threshold': int(stop_when_unread_below),
                    'current_unread_count': int(unread_count),
                    'page_no': int(current_page_no),
                }
                break
            if stop_at_page is not None and current_page_no >= int(stop_at_page):
                stop_reason = {
                    'kind': 'page_threshold_reached',
                    'threshold': int(stop_at_page),
                    'page_no': int(current_page_no),
                    'current_unread_count': unread_count,
                }
                break
            if page_idx >= page_limit - 1:
                break
            if pages_visited % SOFT_RESET_EVERY_PAGES == 0:
                soft_reset_info = await _soft_reset_list_session(page, current_page_url, expected_page_no=current_page_no)
                return_method_counts[str(soft_reset_info.get('method') or 'goto_soft_reset')] = return_method_counts.get(str(soft_reset_info.get('method') or 'goto_soft_reset'), 0) + 1
                state.artifacts = (state.artifacts or {}) | {
                    'soft_reset_count': int((state.artifacts or {}).get('soft_reset_count', 0) or 0) + 1,
                    'last_soft_reset_page': current_page_no,
                    'last_soft_reset_ok': bool(soft_reset_info.get('ok')),
                }
                save_state(state)
                if not soft_reset_info.get('ok'):
                    state.status = 'waiting_manual_reset'
                    state.mode = 'body_fetch_sweep'
                    state.current_step = 'soft reset failed during body fetch sweep'
                    state.next_step = 'manually return the 163 inbox list to the last healthy page, then rerun the same command'
                    state.note = f'soft reset failed at page {current_page_no}; current page={soft_reset_info.get("current_page")}'
                    save_state(state)
                    print(json.dumps({
                        'status': state.status,
                        'note': state.note,
                        'current_page': soft_reset_info.get('current_page'),
                        'expected_inbox_page': current_page_no,
                        'soft_reset_info': soft_reset_info,
                        'url': page.url,
                        'artifacts': state.artifacts,
                    }, ensure_ascii=False, indent=2))
                    return 2
            next_clicked = await click_next_page(page)
            if not next_clicked:
                break
            await page.wait_for_timeout(900)

        if stop_reason is not None:
            state.status = 'completed'
        elif success_count == 0 and failure_count == 0 and attempted_new == 0:
            state.status = 'needs_calibration'
        else:
            state.status = 'completed' if success_count > 0 and failure_count == 0 else 'completed_with_failures'
        state.current_step = 'sequential sweep body fetch finished'
        state.next_step = 'inspect output JSONL, then run import-local-bodies or continue with a larger sweep'
        state.note = f'pages={pages_visited}; success={success_count}; skipped_existing={skipped_existing}; failures={failure_count}'
        if stop_reason is not None:
            if stop_reason.get('kind') == 'unread_below_threshold':
                state.note += f"; stop_reason=unread<{stop_reason.get('threshold')} (current={stop_reason.get('current_unread_count')})"
            elif stop_reason.get('kind') == 'page_threshold_reached':
                state.note += f"; stop_reason=page>={stop_reason.get('threshold')} (current={stop_reason.get('page_no')})"
        state.artifacts = (state.artifacts or {}) | {
            'body_fetch_completion': await capture_diag(page, 'body_fetch_completion'),
            'stop_reason': stop_reason,
        }
        save_state(state)
        run_elapsed_seconds = round(time.perf_counter() - run_started_perf, 3)
        print(json.dumps({
            'status': state.status,
            'started_at': run_started_at.isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds': run_elapsed_seconds,
            'page_limit': page_limit,
            'requested_start_page': requested_start_page,
            'effective_start_page': effective_start_page,
            'started_from_current_page': bool(start_from_current_page),
            'pages_visited': pages_visited,
            'max_targets': max_targets,
            'attempted_new': attempted_new,
            'success': success_count,
            'skipped_existing': skipped_existing,
            'failures': failure_count,
            'avg_seconds_per_success': round(run_elapsed_seconds / success_count, 3) if success_count else None,
            'avg_seconds_per_attempted_new': round(run_elapsed_seconds / attempted_new, 3) if attempted_new else None,
            'reached_target_limit': reached_target_limit,
            'return_method_counts': return_method_counts,
            'page_probes': page_probes,
            'output_jsonl': str(output_jsonl),
            'failure_jsonl': str(BODY_FAILURE_JSONL),
        }, ensure_ascii=False, indent=2))
        return 0 if failure_count == 0 else 1
    finally:
        await playwright.stop()


async def run_index(state: TaskState, page_limit: int) -> int:
    playwright, browser = await connect_browser(state.cdp_endpoint)
    try:
        page = await attach_page(browser, prefer_existing_mail_tab=True)
        if page.is_closed():
            raise RuntimeError('Attached page was already closed. Keep the real Chrome window open and rerun.')
        try:
            status, summary = await classify_page(page)
        except Exception:
            page = await attach_page(browser, prefer_existing_mail_tab=False)
            status, summary = await classify_page(page)
        state.current_url = page.url

        if status != 'inbox':
            state.status = 'waiting_manual_verification' if status == 'manual_verification' else status
            state.current_step = 'waiting for manual login/verification in real Chrome'
            state.next_step = 'after manual verification, rerun the same command'
            state.note = summary[:500]
            state.artifacts = (state.artifacts or {}) | {'diagnostics': await capture_diag(page, status)}
            save_state(state)
            print(json.dumps({'status': state.status, 'url': page.url, 'note': state.note, 'artifacts': state.artifacts}, ensure_ascii=False, indent=2))
            return 2

        state.status = 'indexing'
        state.current_step = 'extracting visible rows from inbox/list pages'
        state.next_step = 'continue next page or refine selectors if extraction quality is poor'
        save_state(state)

        processed_any = False
        seen_mail_keys_this_run: set[str] = set()
        for page_idx in range(page_limit):
            state.current_url = page.url
            rows = await collect_rows_for_current_page(page)
            rows = _attach_read_mid_fields(rows, await _page_visible_mid_map(page))
            if rows:
                processed_any = True
            for row in rows:
                mail_key = row.get('mail_key') or row.get('node_id') or row.get('aria_label') or row.get('row_key', '')
                if mail_key and mail_key in seen_mail_keys_this_run:
                    continue
                if mail_key:
                    seen_mail_keys_this_run.add(mail_key)
                append_jsonl(INDEX_JSONL, {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'page_url': page.url,
                    'page_no': state.page_no,
                    **row,
                })
                state.indexed_count += 1
                state.last_row_key = row.get('row_key', '')
            save_state(state)

            if page_idx >= page_limit - 1:
                break

            next_clicked = await click_next_page(page)
            if next_clicked:
                state.page_no += 1
                state.current_url = page.url
            else:
                break

        state.status = 'completed' if processed_any else 'needs_calibration'
        state.current_step = 'index run finished'
        state.next_step = 'inspect scholar_index.jsonl and diagnostics; if rows are poor, refine selectors on a live inbox page'
        state.artifacts = (state.artifacts or {}) | {
            'index_jsonl': str(INDEX_JSONL),
            'completion_diagnostics': await capture_diag(page, 'index_completion')
        }
        save_state(state)
        print(json.dumps(asdict(state), ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        state.status = 'fatal_error'
        state.current_step = 'run-index crashed before finishing'
        state.next_step = 'inspect diagnostics, keep Chrome open, then rerun after patching'
        state.note = f'{type(e).__name__}: {e}'
        save_state(state)
        raise
    finally:
        await playwright.stop()


def cmd_status() -> int:
    state = load_state()
    print(json.dumps(asdict(state), ensure_ascii=False, indent=2))
    return 0


def cmd_reset() -> int:
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    print('state reset')
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Read 163 scholar mails from a locally logged-in real Chrome with manual-pause support.')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('status')
    sub.add_parser('reset')

    run = sub.add_parser('run-index')
    run.add_argument('--cdp-endpoint', default='http://127.0.0.1:9222')
    run.add_argument('--page-limit', type=int, default=3)

    body = sub.add_parser('run-body-fetch')
    body.add_argument('--cdp-endpoint', default='http://127.0.0.1:9222')
    body.add_argument('--input-jsonl', default=str(INDEX_JSONL))
    body.add_argument('--output-jsonl', default=str(BODY_JSONL))
    body.add_argument('--limit', type=int, default=10)
    body.add_argument('--start-offset', type=int, default=0)
    body.add_argument('--search-page-limit', type=int, default=6)

    sweep = sub.add_parser('run-body-sweep')
    sweep.add_argument('--cdp-endpoint', default='http://127.0.0.1:9222')
    sweep.add_argument('--output-jsonl', default=str(BODY_JSONL))
    sweep.add_argument('--page-limit', type=int, default=1, help='Number of inbox pages to visit starting from the chosen start page')
    sweep.add_argument('--max-targets', type=int)
    sweep.add_argument('--start-page', type=int, default=1, help='1-based inbox page to start from when not using --start-from-current-page')
    sweep.add_argument('--start-from-current-page', action='store_true', help='Start from the currently visible inbox page instead of resetting to page 1 or --start-page')
    sweep.add_argument('--stop-at-page', type=int, help='Stop after finishing a page whose page number is >= this threshold')
    sweep.add_argument('--stop-when-unread-below', type=int, help='Stop after finishing a page once unread count drops below this threshold')
    return p.parse_args()


async def main_async(args: argparse.Namespace) -> int:
    if args.cmd == 'run-index':
        state = load_state()
        state.cdp_endpoint = args.cdp_endpoint
        return await run_index(state, page_limit=args.page_limit)
    if args.cmd == 'run-body-fetch':
        state = load_state()
        state.cdp_endpoint = args.cdp_endpoint
        input_jsonl = Path(args.input_jsonl)
        output_jsonl = Path(args.output_jsonl)
        if not input_jsonl.is_absolute():
            input_jsonl = ROOT / input_jsonl
        if not output_jsonl.is_absolute():
            output_jsonl = ROOT / output_jsonl
        return await run_body_fetch(
            state,
            input_jsonl=input_jsonl,
            output_jsonl=output_jsonl,
            limit=args.limit,
            start_offset=args.start_offset,
            search_page_limit=args.search_page_limit,
        )
    if args.cmd == 'run-body-sweep':
        state = load_state()
        state.cdp_endpoint = args.cdp_endpoint
        output_jsonl = Path(args.output_jsonl)
        if not output_jsonl.is_absolute():
            output_jsonl = ROOT / output_jsonl
        return await run_body_fetch_sweep(
            state,
            output_jsonl=output_jsonl,
            page_limit=args.page_limit,
            max_targets=args.max_targets,
            start_page=args.start_page,
            start_from_current_page=args.start_from_current_page,
            stop_at_page=args.stop_at_page,
            stop_when_unread_below=args.stop_when_unread_below,
        )
    raise RuntimeError('unexpected async command')


def main() -> int:
    args = parse_args()
    if args.cmd == 'status':
        return cmd_status()
    if args.cmd == 'reset':
        return cmd_reset()
    return asyncio.run(main_async(args))


if __name__ == '__main__':
    sys.exit(main())
