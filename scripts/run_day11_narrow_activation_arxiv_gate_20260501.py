#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    python_bin = sys.executable or 'python3'
    profile = project_root / 'config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate.yaml'
    log_path = project_root / 'logs/day11_narrow_activation_arxiv_gate_20260501.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    runs = [
        {
            'label': 'large_fixed_narrow_arxiv_gate',
            'source_db': project_root / 'data/mgap_pkgB_large_slice150_seed_20260416_slice150.db',
            'output_db': project_root / 'data/benchmark/day11_narrow_activation_large_fixed_arxiv_gate_20260501.db',
            'report_out': project_root / 'docs/validation/day11-narrow-activation-large-fixed-arxiv-gate-20260501.json',
        },
        {
            'label': 'fresh30_narrow_arxiv_gate',
            'source_db': project_root / 'data/mgap_fresh30_20260410.db',
            'output_db': project_root / 'data/benchmark/day11_narrow_activation_fresh30_arxiv_gate_20260501.db',
            'report_out': project_root / 'docs/validation/day11-narrow-activation-fresh30-arxiv-gate-20260501.json',
        },
        {
            'label': 'pkg3_guardrail100_narrow_arxiv_gate',
            'source_db': project_root / 'data/mgap_pkg3_guardrail_100.db',
            'output_db': project_root / 'data/benchmark/day11_narrow_activation_pkg3_guardrail100_arxiv_gate_20260501.db',
            'report_out': project_root / 'docs/validation/day11-narrow-activation-pkg3-guardrail100-arxiv-gate-20260501.json',
        },
        {
            'label': 'issac100_narrow_arxiv_gate',
            'source_db': project_root / 'data/mgap_issac_100.db',
            'output_db': project_root / 'data/benchmark/day11_narrow_activation_issac100_arxiv_gate_20260501.db',
            'report_out': project_root / 'docs/validation/day11-narrow-activation-issac100-arxiv-gate-20260501.json',
        },
    ]

    with log_path.open('a', encoding='utf-8') as logf:
        for idx, run in enumerate(runs, start=1):
            cmd = [
                python_bin,
                'scripts/replay_validation.py',
                '--source-db',
                str(run['source_db']),
                '--output-db',
                str(run['output_db']),
                '--policy-profile',
                str(profile),
                '--report-out',
                str(run['report_out']),
                '--limit',
                '1000000',
                '--stages',
                'enrich',
                'merge',
                'dedup',
                '--stage-timeout-seconds',
                '10800',
            ]
            banner = f"[{now_iso()}] START {idx}/{len(runs)} {run['label']}\nCMD: {' '.join(cmd)}\n"
            print(banner, end='')
            logf.write(banner)
            logf.flush()
            subprocess.run(cmd, cwd=project_root, check=True, stdout=logf, stderr=subprocess.STDOUT)
            tail = f"[{now_iso()}] DONE {idx}/{len(runs)} {run['label']}\n"
            print(tail, end='')
            logf.write(tail)
            logf.flush()

    print({'status': 'ok', 'log_path': str(log_path)})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
