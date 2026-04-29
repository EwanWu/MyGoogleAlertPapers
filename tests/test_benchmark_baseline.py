from __future__ import annotations

from pathlib import Path

from mygooglealertpapers.benchmark_baseline import build_baseline_manifest, get_baseline_preset


def test_get_baseline_preset_known_names():
    assert get_baseline_preset('small-fixed').limit == 60
    assert get_baseline_preset('large-fixed').source_db.endswith('mgap_pkgB_large_slice150_seed_20260416_slice150.db')
    assert get_baseline_preset('fresh-like').source_db.endswith('mgap_fresh30_20260410.db')


def test_build_baseline_manifest_uses_current_runtime_default_profile_and_standard_outputs(tmp_path: Path):
    manifest = build_baseline_manifest(tmp_path, preset_name='small-fixed', run_tag='unit', python_bin='python3')

    assert manifest['preset'] == 'small-fixed'
    assert manifest['limit'] == 60
    assert manifest['policy_profile'].endswith('config/policy_profiles/openalex_batching_identifier_plus_title_core.yaml')
    assert manifest['source_db'].endswith('data/mgap_pkgB_large_slice150_seed_20260416_slice150.db')
    assert manifest['output_db'].endswith('data/benchmark/day2_baseline_small-fixed_unit.db')
    assert manifest['report_out'].endswith('docs/validation/day2-baseline-small-fixed-unit.json')
    assert manifest['command'][0] == 'python3'
    assert manifest['command'][1] == 'scripts/replay_validation.py'
    assert '--stages' in manifest['command']
    assert manifest['stages'] == ['enrich', 'merge', 'dedup']
