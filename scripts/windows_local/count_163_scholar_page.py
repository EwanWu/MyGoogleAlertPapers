#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

COUNT_JS = r'''
() => {
  const isRenderable = (el) => {
    const st = window.getComputedStyle(el);
    if (!st || st.display === 'none' || st.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return !(r.width <= 20 || r.height <= 12);
  };
  const textNorm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const coreKey = (el) => {
    const aria = textNorm(el.getAttribute('aria-label') || '');
    const txt = textNorm(el.innerText || '');
    const combined = textNorm(`${aria} ${txt}`);
    const subjectMatch = combined.match(/(\[收件箱\][^\n]+?)(?:\s+(今日|昨日|星期[一二三四五六日天]|\d+月\d+日|\d{1,2}:\d{2})|\s+发件人\s*[：:]|$)/i);
    const core = textNorm(subjectMatch ? subjectMatch[1] : txt)
      .replace(/^Google 学术搜索快讯\s*/i, '')
      .replace(/^Google Scholar\s*/i, '')
      .replace(/\s+(今日|昨日|星期[一二三四五六日天]|\d+月\d+日|\d{1,2}:\d{2})$/i, '')
      .trim();
    const dateMatch = combined.match(/(\d+月\d+日|今日|昨日|星期[一二三四五六日天]|\d{4}年\d+月\d+日)/i);
    return `${core || aria || txt} || ${(dateMatch && dateMatch[1]) || ''}`;
  };
  const letters = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  const eligible = letters.filter(isRenderable);
  const scholar = eligible.filter(el => /发件人\s*[：:]\s*google 学术搜索快讯|发件人\s*[：:]\s*google scholar|google 学术搜索快讯|google scholar/i.test(textNorm((el.getAttribute('aria-label')||'') + ' ' + (el.innerText||''))));
  return {
    total_letter_nodes_visible: eligible.length,
    scholar_sender_visible: scholar.length,
    rows: scholar.map(el => ({
      key: coreKey(el),
      id: el.id || null,
      aria: textNorm(el.getAttribute('aria-label') || ''),
      text: textNorm(el.innerText || ''),
      y: Math.round(el.getBoundingClientRect().top),
      x: Math.round(el.getBoundingClientRect().left)
    }))
  };
}
'''

SCROLL_HELPER_JS = r'''
() => {
  const letters = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  let best = null, bestScore = -1;
  for (const letter of letters) {
    let cur = letter.parentElement;
    while (cur) {
      const st = window.getComputedStyle(cur);
      const scrollable = /(auto|scroll)/i.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 100;
      if (scrollable) {
        const count = cur.querySelectorAll('[role="link"][sign="letter"]').length;
        const score = count * 100000 + (cur.clientHeight || 0);
        if (score > bestScore) { best = cur; bestScore = score; }
      }
      cur = cur.parentElement;
    }
  }
  const target = best || document.scrollingElement || document.documentElement;
  return {
    tag: target.tagName || null,
    id: target.id || null,
    className: target.className || null,
    scrollTop: target.scrollTop || 0,
    clientHeight: target.clientHeight || 0,
    scrollHeight: target.scrollHeight || 0,
  };
}
'''

RESET_SCROLL_JS = r'''
() => {
  const info = (%SCROLL_HELPER_JS%)();
  const letters = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  let best = null, bestScore = -1;
  for (const letter of letters) {
    let cur = letter.parentElement;
    while (cur) {
      const st = window.getComputedStyle(cur);
      const scrollable = /(auto|scroll)/i.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 100;
      if (scrollable) {
        const count = cur.querySelectorAll('[role="link"][sign="letter"]').length;
        const score = count * 100000 + (cur.clientHeight || 0);
        if (score > bestScore) { best = cur; bestScore = score; }
      }
      cur = cur.parentElement;
    }
  }
  const target = best || document.scrollingElement || document.documentElement;
  target.scrollTop = 0;
  return {
    tag: target.tagName || null,
    id: target.id || null,
    className: target.className || null,
    scrollTop: target.scrollTop || 0,
    clientHeight: target.clientHeight || 0,
    scrollHeight: target.scrollHeight || 0,
  };
}
'''.replace('%SCROLL_HELPER_JS%', "() => { const letters = [...document.querySelectorAll('[role=\"link\"][sign=\"letter\"]')]; let best = null, bestScore = -1; for (const letter of letters) { let cur = letter.parentElement; while (cur) { const st = window.getComputedStyle(cur); const scrollable = /(auto|scroll)/i.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 100; if (scrollable) { const count = cur.querySelectorAll('[role=\"link\"][sign=\"letter\"]').length; const score = count * 100000 + (cur.clientHeight || 0); if (score > bestScore) { best = cur; bestScore = score; } } cur = cur.parentElement; } } const target = best || document.scrollingElement || document.documentElement; return { tag: target.tagName || null, id: target.id || null, className: target.className || null, scrollTop: target.scrollTop || 0, clientHeight: target.clientHeight || 0, scrollHeight: target.scrollHeight || 0 }; }")

SCROLL_JS = r'''
() => {
  const letters = [...document.querySelectorAll('[role="link"][sign="letter"]')];
  let best = null, bestScore = -1;
  for (const letter of letters) {
    let cur = letter.parentElement;
    while (cur) {
      const st = window.getComputedStyle(cur);
      const scrollable = /(auto|scroll)/i.test(st.overflowY || '') && cur.scrollHeight > cur.clientHeight + 100;
      if (scrollable) {
        const count = cur.querySelectorAll('[role="link"][sign="letter"]').length;
        const score = count * 100000 + (cur.clientHeight || 0);
        if (score > bestScore) { best = cur; bestScore = score; }
      }
      cur = cur.parentElement;
    }
  }
  const target = best || document.scrollingElement || document.documentElement;
  const before = target.scrollTop || 0;
  const delta = Math.max(300, Math.floor(((target.clientHeight || window.innerHeight || 800) * 0.8)));
  target.scrollTop = before + delta;
  return {before, after: target.scrollTop || 0, moved: (target.scrollTop || 0) > before, clientHeight: target.clientHeight || 0, scrollHeight: target.scrollHeight || 0};
}
'''

def _row_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (int(row.get('y', 0) or 0), int(row.get('x', 0) or 0), str(row.get('key') or ''))


def _row_richness(row: dict[str, Any]) -> int:
    return sum(len(str(row.get(k) or '')) for k in ['aria', 'text', 'id', 'key'])


def _collapse_snapshot_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    picked: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get('key') or ''), int(row.get('y', 0) or 0))
        prev = picked.get(key)
        if prev is None or _row_richness(row) > _row_richness(prev):
            picked[key] = row
    return sorted(picked.values(), key=_row_sort_key)


def _local_sequence_key(rows: list[dict[str, Any]], idx: int, window: int = 3) -> str:
    start = max(0, idx - window)
    end = min(len(rows), idx + window + 1)
    return ' ### '.join(f'{j - idx:+d}:{rows[j].get("key") or ""}' for j in range(start, end))


def _sequence_dedup_rows(snapshot_batches: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    picked: dict[str, dict[str, Any]] = {}
    for batch_idx, batch in enumerate(snapshot_batches):
        ordered = _collapse_snapshot_rows(batch)
        for row_idx, row in enumerate(ordered):
            sequence_key = _local_sequence_key(ordered, row_idx)
            final_key = sequence_key or str(row.get('key') or '')
            enriched = dict(row)
            enriched['sequence_key'] = sequence_key
            enriched['snapshot_batch'] = batch_idx
            prev = picked.get(final_key)
            if prev is None or _row_richness(enriched) > _row_richness(prev):
                picked[final_key] = enriched
    return sorted(picked.values(), key=_row_sort_key)


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--cdp-endpoint', default='http://127.0.0.1:9222')
    ap.add_argument('--scroll-steps', type=int, default=0)
    args = ap.parse_args()

    p = await async_playwright().start()
    try:
        browser = await p.chromium.connect_over_cdp(args.cdp_endpoint)
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if 'mail.163.com' in pg.url:
                page = pg
                break
        if page is None:
            raise RuntimeError('No 163 mail page found')
        out = {'reset': await page.evaluate(RESET_SCROLL_JS), 'initial': {}, 'scrolled': []}
        snapshot_batches: list[list[dict[str, Any]]] = []

        initial = await page.evaluate(COUNT_JS)
        initial_rows = initial.pop('rows', [])
        snapshot_batches.append(initial_rows)
        initial_collapsed = _collapse_snapshot_rows(initial_rows)
        out['initial'] = {
            **initial,
            'dedup_within_snapshot': len(initial_collapsed),
            'samples': initial_collapsed[:12],
        }

        for _ in range(args.scroll_steps):
            info = await page.evaluate(SCROLL_JS)
            await page.wait_for_timeout(400)
            count = await page.evaluate(COUNT_JS)
            rows = count.pop('rows', [])
            snapshot_batches.append(rows)
            collapsed = _collapse_snapshot_rows(rows)
            deduped_so_far = _sequence_dedup_rows(snapshot_batches)
            out['scrolled'].append({
                'scroll': info,
                'count': {
                    **count,
                    'dedup_within_snapshot': len(collapsed),
                    'samples': collapsed[:8],
                },
                'unique_sequence_dedup_so_far': len(deduped_so_far),
            })
            if not info.get('moved'):
                break
        out['unique_scholar_sequence_dedup_across_scan'] = len(_sequence_dedup_rows(snapshot_batches))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    finally:
        await p.stop()

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
