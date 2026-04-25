#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def count_jsonl(path: Path) -> int:
    return len(load_jsonl(path))


def main() -> int:
    ap = argparse.ArgumentParser(description='Summarize timed 163 local body-fetch + pipeline runs and extrapolate to full roster size.')
    ap.add_argument('--fetch-timing', required=True)
    ap.add_argument('--fetch-jsonl', required=True)
    ap.add_argument('--pipeline-timing', required=False)
    ap.add_argument('--full-mail-count', type=int, default=277)
    args = ap.parse_args()

    fetch_timing = load_json(Path(args.fetch_timing))
    fetch_rows = load_jsonl(Path(args.fetch_jsonl))
    fetch_success_count = len(fetch_rows)
    fetch_elapsed = float(fetch_timing.get('elapsed_seconds') or 0.0)
    expected_target_count = int(fetch_timing.get('expected_target_count') or 0)
    record_elapsed_sum = round(sum(float(r.get('elapsed_seconds') or 0.0) for r in fetch_rows), 3)
    avg_record_seconds = round(record_elapsed_sum / fetch_success_count, 3) if fetch_success_count else None

    result: dict[str, object] = {
        'full_mail_count': args.full_mail_count,
        'fetch': {
            'timing_json': args.fetch_timing,
            'success_jsonl': args.fetch_jsonl,
            'elapsed_seconds_wall': fetch_elapsed,
            'expected_target_count': expected_target_count,
            'success_count': fetch_success_count,
            'record_elapsed_seconds_sum': record_elapsed_sum,
            'avg_seconds_per_success_wall': round(fetch_elapsed / fetch_success_count, 3) if fetch_success_count else None,
            'avg_seconds_per_success_record': avg_record_seconds,
            'estimated_full_fetch_seconds_wall': round(fetch_elapsed / fetch_success_count * args.full_mail_count, 3) if fetch_success_count else None,
            'estimated_full_fetch_seconds_record': round(avg_record_seconds * args.full_mail_count, 3) if avg_record_seconds is not None else None,
        },
    }

    if args.pipeline_timing:
        pipeline_timing = load_json(Path(args.pipeline_timing))
        pipeline_elapsed = float(pipeline_timing.get('elapsed_seconds') or 0.0)
        imported_count = None
        input_jsonl = pipeline_timing.get('input_jsonl')
        if input_jsonl:
            imported_count = count_jsonl(Path(input_jsonl))
        result['pipeline'] = {
            'timing_json': args.pipeline_timing,
            'elapsed_seconds': pipeline_elapsed,
            'imported_mail_count': imported_count,
            'avg_seconds_per_mail': round(pipeline_elapsed / imported_count, 3) if imported_count else None,
            'estimated_full_pipeline_seconds': round(pipeline_elapsed / imported_count * args.full_mail_count, 3) if imported_count else None,
            'stages': pipeline_timing.get('stages') or [],
        }
        fetch_est_record = result['fetch']['estimated_full_fetch_seconds_record']
        pipe_est = result['pipeline']['estimated_full_pipeline_seconds']
        if isinstance(fetch_est_record, (int, float)) and isinstance(pipe_est, (int, float)):
            result['combined_estimate_seconds_record_based'] = round(fetch_est_record + pipe_est, 3)
        fetch_est_wall = result['fetch']['estimated_full_fetch_seconds_wall']
        if isinstance(fetch_est_wall, (int, float)) and isinstance(pipe_est, (int, float)):
            result['combined_estimate_seconds_wall_based'] = round(fetch_est_wall + pipe_est, 3)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
