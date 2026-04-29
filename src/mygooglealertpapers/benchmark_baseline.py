from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_POLICY_PROFILE = 'config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster.yaml'
DEFAULT_STAGES = ('enrich', 'merge', 'dedup')


@dataclass(frozen=True)
class BaselinePreset:
    name: str
    description: str
    source_db: str
    limit: int


BASELINE_PRESETS: dict[str, BaselinePreset] = {
    'small-fixed': BaselinePreset(
        name='small-fixed',
        description='Small fixed replay slice from the validated slice150 seed, capped for fast comparison.',
        source_db='data/mgap_pkgB_large_slice150_seed_20260416_slice150.db',
        limit=60,
    ),
    'large-fixed': BaselinePreset(
        name='large-fixed',
        description='Full fixed replay slice150 seed for current mainline comparison.',
        source_db='data/mgap_pkgB_large_slice150_seed_20260416_slice150.db',
        limit=1000000,
    ),
    'fresh-like': BaselinePreset(
        name='fresh-like',
        description='Best currently available fresh-like cached slice for drift-sensitive smoke comparison.',
        source_db='data/mgap_fresh30_20260410.db',
        limit=1000000,
    ),
}


def get_baseline_preset(name: str) -> BaselinePreset:
    try:
        return BASELINE_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f'unknown baseline preset: {name}') from exc


def build_baseline_manifest(
    project_root: Path,
    *,
    preset_name: str,
    run_tag: str = 'baseline',
    python_bin: str = 'python3',
    policy_profile: str = DEFAULT_POLICY_PROFILE,
    stage_timeout_seconds: int = 0,
    stages: tuple[str, ...] = DEFAULT_STAGES,
) -> dict[str, Any]:
    preset = get_baseline_preset(preset_name)
    project_root = project_root.resolve()
    source_db = (project_root / preset.source_db).resolve()
    policy_path = (project_root / policy_profile).resolve()
    output_db = (project_root / 'data' / 'benchmark' / f'day2_baseline_{preset.name}_{run_tag}.db').resolve()
    report_out = (project_root / 'docs' / 'validation' / f'day2-baseline-{preset.name}-{run_tag}.json').resolve()
    command = [
        python_bin,
        'scripts/replay_validation.py',
        '--source-db', str(source_db),
        '--output-db', str(output_db),
        '--policy-profile', str(policy_path),
        '--report-out', str(report_out),
        '--limit', str(preset.limit),
        '--stages', *stages,
    ]
    if stage_timeout_seconds:
        command.extend(['--stage-timeout-seconds', str(stage_timeout_seconds)])
    return {
        'preset': preset.name,
        'description': preset.description,
        'source_db': str(source_db),
        'policy_profile': str(policy_path),
        'limit': preset.limit,
        'stages': list(stages),
        'output_db': str(output_db),
        'report_out': str(report_out),
        'markdown_out': str(report_out.with_suffix('.md')),
        'command': command,
        'command_shell': ' '.join(json.dumps(part, ensure_ascii=False) for part in command),
    }


def run_baseline_manifest(manifest: dict[str, Any], *, cwd: Path) -> None:
    subprocess.run(manifest['command'], cwd=cwd, check=True)
