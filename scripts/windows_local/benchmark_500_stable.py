#!/usr/bin/env python3
"""
Stable 163 local benchmark.
Priorities: single-tab, bounded retries, incremental result persistence, crash avoidance.

Usage:
  python3 /tmp/benchmark_500_stable.py [start_page=12] [max_targets=500]
"""
import asyncio
import json
import re
import sys
import time
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

MODULE = Path('/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers/scripts/windows_local/read_163_scholar_with_manual_pause.py')
spec = spec_from_file_location('mail163mod', MODULE)
mod = module_from_spec(spec)
sys.modules['mail163mod'] = mod
spec.loader.exec_module(mod)

STATE_FILE = Path('/tmp/benchmark_500_state.json')
OUTPUT_FILE = Path('/tmp/benchmark_500_results.jsonl')
SUMMARY_FILE = Path('/tmp/benchmark_500_summary.json')
CDP = 'http://172.18.240.1:9223'
TIME_LIMIT_S = 4200  # 70 min hard stop, avoids runaway
SOFT_RESET_EVERY_PAGES = 3  # conservative anti-heat cadence
SOFT_RESET_WAIT_MS = 2200


def now_ts() -> float:
    return time.time()


def mid_from_node_id(node_id: str | None) -> str | None:
    raw = re.sub(r'^\d+_|\d+Dom$', '', str(node_id or ''))
    m = re.match(r'^(\d+)([a-zA-Z0-9_-]+)$', raw)
    if not m:
        return None
    return f'{m.group(1)}:{m.group(2)}'


def load_state(start_page: int) -> dict:
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            if isinstance(state, dict):
                state.setdefault('started_at', now_ts())
                state.setdefault('seen_node_ids', [])
                state.setdefault('seen_read_mids', [])
                state.setdefault('pages_done', [])
                state.setdefault('results_count', 0)
                state.setdefault('start_page', start_page)
                state.setdefault('current_phase', 'starting')
                state.setdefault('current_page', start_page)
                state.setdefault('current_page_row_index', 0)
                state.setdefault('last_progress_ts', state.get('started_at', now_ts()))
                state.setdefault('soft_reset_count', 0)
                state.setdefault('last_soft_reset_page', None)
                state.setdefault('last_soft_reset_reason', None)
                return state
        except Exception:
            pass
    return {
        'started_at': now_ts(),
        'start_page': start_page,
        'seen_node_ids': [],
        'seen_read_mids': [],
        'pages_done': [],
        'results_count': 0,
        'current_phase': 'starting',
        'current_page': start_page,
        'current_page_row_index': 0,
        'last_progress_ts': now_ts(),
        'soft_reset_count': 0,
        'last_soft_reset_page': None,
        'last_soft_reset_reason': None,
    }


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def append_result(record: dict) -> None:
    with OUTPUT_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def save_summary(summary: dict) -> None:
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2))


async def close_stale_tabs(browser):
    ctx = browser.contexts[0]
    pages = list(ctx.pages)
    chosen = None
    for page in pages:
        try:
            status, _ = await mod.classify_page(page)
        except Exception:
            status = None
        if status == 'inbox':
            chosen = page
            break
    if chosen is None:
        chosen = pages[0]
    for page in pages:
        if page is chosen:
            continue
        try:
            await page.close()
        except Exception:
            pass
    return chosen


async def hard_reload(page, wait_ms: int = 2500) -> None:
    await page.goto(page.url, wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_timeout(wait_ms)


async def soft_reset(page, current_page: int, *, reason: str, state: dict) -> bool:
    try:
        await hard_reload(page, wait_ms=SOFT_RESET_WAIT_MS)
        ok = await ensure_target_page(page, current_page)
        state['soft_reset_count'] = int(state.get('soft_reset_count', 0) or 0) + 1
        state['last_soft_reset_page'] = current_page
        state['last_soft_reset_reason'] = reason
        state['last_progress_ts'] = now_ts()
        save_state(state)
        return ok
    except Exception:
        return False


async def ensure_target_page(page, target_page: int, max_moves: int = 35) -> bool:
    target_page = max(1, int(target_page))
    info = await mod._current_list_page_info(page)
    cur = info.get('current')
    if cur is None:
        return False
    moves = 0
    while cur != target_page and moves < max_moves:
        moved = await (mod.click_next_page(page) if cur < target_page else mod.click_prev_page(page))
        if not moved:
            return False
        await page.wait_for_timeout(700)
        info = await mod._current_list_page_info(page)
        cur = info.get('current')
        moves += 1
    return cur == target_page


async def stabilize_and_collect(page, expected_page: int, attempts: int = 4):
    last_probe = None
    last_rows = []
    for attempt in range(1, attempts + 1):
        info = await mod._current_list_page_info(page)
        cur = info.get('current')
        if cur != expected_page:
            ok = await ensure_target_page(page, expected_page)
            if not ok:
                await hard_reload(page, wait_ms=3000)
                ok = await ensure_target_page(page, expected_page)
                if not ok:
                    continue
        last_probe = await mod._probe_sweep_page(page)
        if int(last_probe.get('renderable_letter_count', 0) or 0) <= 0:
            await hard_reload(page, wait_ms=3000)
            continue
        rows = await mod.collect_rows_for_current_page(page, max_scroll_steps=8)
        rows = mod._attach_read_mid_fields(rows, await mod._page_visible_mid_map(page))
        for row in rows:
            row.setdefault('read_mid', mid_from_node_id(row.get('node_id')))
            row.setdefault('read_mid_source', 'node_id_derived_benchmark')
        if rows:
            return True, rows, last_probe, attempt
        await hard_reload(page, wait_ms=3000)
        last_rows = rows
    return False, last_rows, last_probe or {}, attempts


async def extract_mail_payload(page, target_subject: str, timeout_ms: int = 6000):
    deadline = time.perf_counter() + (timeout_ms / 1000.0)
    best = None
    while time.perf_counter() < deadline:
        for frame in page.frames:
            try:
                payload = await frame.evaluate(mod.EXTRACT_MAIL_BODY_JS, {'targetSubject': target_subject})
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            text = str(payload.get('text') or '')
            if len(text) < 100:
                continue
            if best is None or float(payload.get('score', 0) or 0) > float(best.get('score', 0) or 0):
                best = dict(payload)
        if best:
            return best
        await page.wait_for_timeout(300)
    return None


async def fetch_one(page, row: dict, expected_page: int):
    nid = str(row.get('node_id') or '')
    subject = str(row.get('subject_core') or row.get('subject') or '')
    list_url = page.url
    started = time.perf_counter()
    el = await page.query_selector(f'[id="{nid}"]')
    if not el:
        return {
            'ok': False,
            'error': 'element_not_found',
            'elapsed_s': round(time.perf_counter() - started, 3),
            'text_len': 0,
            'recover_ok': False,
        }
    try:
        await el.click(timeout=5000)
    except Exception as e:
        return {
            'ok': False,
            'error': f'click_failed:{type(e).__name__}',
            'elapsed_s': round(time.perf_counter() - started, 3),
            'text_len': 0,
            'recover_ok': False,
        }

    payload = await extract_mail_payload(page, subject, timeout_ms=6500)
    elapsed = round(time.perf_counter() - started, 3)
    ok = payload is not None
    text_len = len(str(payload.get('text') or '')) if payload else 0

    recover_ok = False
    try:
        await page.go_back(wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(1200)
        info = await mod._current_list_page_info(page)
        probe = await mod._probe_sweep_page(page)
        recover_ok = info.get('current') == expected_page and int(probe.get('renderable_letter_count', 0) or 0) > 0
    except Exception:
        recover_ok = False

    if not recover_ok:
        try:
            await page.goto(list_url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2500)
            recover_ok = await ensure_target_page(page, expected_page)
        except Exception:
            recover_ok = False

    return {
        'ok': ok,
        'elapsed_s': elapsed,
        'text_len': text_len,
        'recover_ok': recover_ok,
        'error': None if ok else 'payload_not_found',
        'payload_source': payload.get('source') if payload else None,
        'iframe_id': payload.get('iframe_id') if payload else None,
    }


async def main():
    start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    max_targets = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    state = load_state(start_page)

    playwright, browser = await mod.connect_browser(CDP)
    summary = {
        'status': 'running',
        'started_at_ts': state['started_at'],
        'start_page': start_page,
        'target_count': max_targets,
        'pages_scanned': 0,
        'pages_with_rows': 0,
        'pages_empty': 0,
        'results_count': state.get('results_count', 0),
        'ok_count': 0,
        'failure_count': 0,
        'avg_elapsed_s': None,
        'stop_reason': None,
        'soft_reset_every_pages': SOFT_RESET_EVERY_PAGES,
        'soft_reset_count': int(state.get('soft_reset_count', 0) or 0),
        'current_phase': state.get('current_phase'),
        'current_page': state.get('current_page'),
        'last_progress_ts': state.get('last_progress_ts'),
        'output_file': str(OUTPUT_FILE),
        'state_file': str(STATE_FILE),
    }
    save_summary(summary)

    try:
        page = await close_stale_tabs(browser)
        status, summary_text = await mod.classify_page(page)
        print(f'[INIT] status={status}')
        if status != 'inbox':
            print('[FATAL] current page is not inbox')
            summary['status'] = 'failed'
            summary['stop_reason'] = f'not_inbox:{status}'
            SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
            return 2

        target_page = start_page
        consecutive_page_failures = 0
        elapsed_values = []

        while state['results_count'] < max_targets:
            state['current_phase'] = 'select_page'
            state['current_page'] = target_page
            state['current_page_row_index'] = 0
            state['last_progress_ts'] = now_ts()
            save_state(state)
            summary['current_phase'] = state['current_phase']
            summary['current_page'] = state['current_page']
            summary['last_progress_ts'] = state['last_progress_ts']
            save_summary(summary)

            if now_ts() - state['started_at'] > TIME_LIMIT_S:
                summary['stop_reason'] = 'time_limit'
                break

            ok = await ensure_target_page(page, target_page)
            if not ok:
                print(f'[PAGE] failed to reach page {target_page}')
                consecutive_page_failures += 1
                if consecutive_page_failures >= 3:
                    summary['stop_reason'] = 'page_navigation_failed'
                    break
                target_page += 1
                continue

            print(f'\n[PAGE] selected page {target_page}', flush=True)
            state['current_phase'] = 'collect_rows'
            state['last_progress_ts'] = now_ts()
            save_state(state)
            summary['current_phase'] = state['current_phase']
            summary['current_page'] = target_page
            summary['last_progress_ts'] = state['last_progress_ts']
            save_summary(summary)
            stabilize_ok, rows, probe, attempts = await stabilize_and_collect(page, target_page)
            summary['pages_scanned'] += 1
            if not stabilize_ok:
                summary['pages_empty'] += 1
                consecutive_page_failures += 1
                print(f'[SCAN] page={target_page} rows=0 probe={probe} attempts={attempts}', flush=True)
                if consecutive_page_failures >= 3:
                    summary['stop_reason'] = 'repeated_empty_pages'
                    break
                target_page += 1
                continue

            consecutive_page_failures = 0
            summary['pages_with_rows'] += 1
            print(f'[SCAN] page={target_page} rows={len(rows)} renderable={probe.get("renderable_letter_count")} scholar_like={probe.get("scholar_like_count")} attempts={attempts}', flush=True)

            page_processed = 0
            page_success = 0
            page_fail = 0
            page_elapsed_values = []
            for row_idx, row in enumerate(rows, start=1):
                state['current_phase'] = 'fetch_mail'
                state['current_page'] = target_page
                state['current_page_row_index'] = row_idx
                state['last_progress_ts'] = now_ts()
                save_state(state)
                if state['results_count'] >= max_targets:
                    break
                nid = str(row.get('node_id') or '')
                read_mid = row.get('read_mid') or mid_from_node_id(nid)
                if not nid:
                    continue
                if nid in state['seen_node_ids']:
                    continue
                if read_mid and read_mid in state['seen_read_mids']:
                    continue

                result = await fetch_one(page, row, target_page)
                record = {
                    'ts': now_ts(),
                    'page': target_page,
                    'node_id': nid,
                    'read_mid': read_mid,
                    'subject': str(row.get('subject_core') or row.get('subject') or '')[:200],
                    'ok': result['ok'],
                    'elapsed_s': result['elapsed_s'],
                    'text_len': result['text_len'],
                    'recover_ok': result['recover_ok'],
                    'error': result.get('error'),
                    'payload_source': result.get('payload_source'),
                }
                append_result(record)
                state['results_count'] += 1
                state['seen_node_ids'].append(nid)
                if read_mid:
                    state['seen_read_mids'].append(read_mid)
                state['last_progress_ts'] = now_ts()
                save_state(state)
                summary['results_count'] = state['results_count']
                summary['current_phase'] = state['current_phase']
                summary['current_page'] = state['current_page']
                summary['last_progress_ts'] = state['last_progress_ts']
                save_summary(summary)

                elapsed_values.append(result['elapsed_s'])
                page_elapsed_values.append(result['elapsed_s'])
                page_processed += 1
                if result['ok']:
                    page_success += 1
                    summary['ok_count'] += 1
                else:
                    page_fail += 1
                    summary['failure_count'] += 1
                print(f'[PROG] total={state["results_count"]}/{max_targets} page={target_page} ok={result["ok"]} elapsed={result["elapsed_s"]:.2f}s text={result["text_len"]} recover={result["recover_ok"]}', flush=True)

                if not result['recover_ok']:
                    # Strong recovery before next item
                    stabilize_ok, _, probe2, attempts2 = await stabilize_and_collect(page, target_page)
                    print(f'[RECOVER] page={target_page} stabilize_ok={stabilize_ok} renderable={probe2.get("renderable_letter_count") if isinstance(probe2, dict) else None} attempts={attempts2}', flush=True)
                    if not stabilize_ok:
                        page_fail += 1
                        break

            page_mean = round(sum(page_elapsed_values) / len(page_elapsed_values), 3) if page_elapsed_values else None
            state['pages_done'].append({'page': target_page, 'processed': page_processed, 'ok': page_success, 'fail': page_fail, 'mean_elapsed_s': page_mean})
            state['current_phase'] = 'page_complete'
            state['current_page_row_index'] = page_processed
            state['last_progress_ts'] = now_ts()
            save_state(state)

            state['last_page_mean_elapsed_s'] = page_mean
            save_state(state)

            summary['results_count'] = state['results_count']
            summary['avg_elapsed_s'] = round(sum(elapsed_values) / len(elapsed_values), 3) if elapsed_values else None
            summary['last_page_mean_elapsed_s'] = page_mean
            summary['current_phase'] = state['current_phase']
            summary['current_page'] = target_page
            summary['last_progress_ts'] = state['last_progress_ts']
            summary['soft_reset_count'] = int(state.get('soft_reset_count', 0) or 0)
            save_summary(summary)

            if state['results_count'] >= max_targets:
                summary['stop_reason'] = 'target_reached'
                break

            if summary['pages_with_rows'] > 0 and summary['pages_with_rows'] % SOFT_RESET_EVERY_PAGES == 0:
                state['current_phase'] = 'soft_reset'
                state['last_progress_ts'] = now_ts()
                save_state(state)
                reset_ok = await soft_reset(page, target_page, reason=f'every_{SOFT_RESET_EVERY_PAGES}_pages', state=state)
                summary['soft_reset_count'] = int(state.get('soft_reset_count', 0) or 0)
                summary['current_phase'] = state.get('current_phase')
                summary['last_progress_ts'] = state.get('last_progress_ts')
                save_summary(summary)
                print(f'[SOFT_RESET] after page={target_page} ok={reset_ok} count={state.get("soft_reset_count")}', flush=True)
                if not reset_ok:
                    summary['stop_reason'] = 'soft_reset_failed'
                    break

            target_page += 1

        state['current_phase'] = 'finished'
        state['last_progress_ts'] = now_ts()
        save_state(state)
        summary['status'] = 'completed' if summary.get('stop_reason') in {'target_reached', 'time_limit'} else 'stopped'
        summary['completed_at_ts'] = now_ts()
        summary['elapsed_wall_s'] = round(now_ts() - state['started_at'], 3)
        summary['results_count'] = state['results_count']
        summary['avg_elapsed_s'] = round(sum(elapsed_values) / len(elapsed_values), 3) if elapsed_values else None
        save_summary(summary)

        print('\n=== SUMMARY ===')
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        await playwright.stop()


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
