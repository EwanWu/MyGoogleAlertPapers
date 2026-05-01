#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def merge_update(path: Path, patch: dict) -> dict:
    state = load_state(path)
    state.update(patch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return state


def append_completed_run(path: Path, entry: dict) -> None:
    state = load_state(path)
    runs = list(state.get("completed_runs") or [])
    runs.append(entry)
    state["completed_runs"] = runs
    state["updated_at"] = now_iso()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def run_logged(cmd: list[str], *, cwd: Path, logf, env: dict[str, str] | None = None, banner: str | None = None) -> None:
    if banner:
        print(banner, end="")
        logf.write(banner)
    line = f"CMD: {' '.join(cmd)}\n"
    print(line, end="")
    logf.write(line)
    logf.flush()
    subprocess.run(cmd, cwd=cwd, env=env, check=True, stdout=logf, stderr=subprocess.STDOUT)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: resume_day11_residual_decomposition_arxiv_gate_20260501.py <state-json> <log-path>", file=sys.stderr)
        return 2

    state_path = Path(sys.argv[1]).resolve()
    log_path = Path(sys.argv[2]).resolve()
    project_root = Path(__file__).resolve().parents[1]
    python_bin = sys.executable or "python3"
    profile = project_root / "config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate.yaml"

    large_source = project_root / "data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
    large_partial = project_root / "data/benchmark/day11_residual_decomposition_large_fixed_arxiv_gate_20260501.db"
    large_resume_source = project_root / "data/benchmark/day11_residual_decomposition_large_fixed_arxiv_gate_20260501_resume_source.db"
    large_report = project_root / "docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-20260501.json"
    large_audit = project_root / "docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-audit-20260501.csv"

    fresh_source = project_root / "data/mgap_fresh30_20260410.db"
    fresh_output = project_root / "data/benchmark/day11_residual_decomposition_fresh30_arxiv_gate_20260501.db"
    fresh_report = project_root / "docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-20260501.json"
    fresh_audit = project_root / "docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-audit-20260501.csv"

    merge_update(
        state_path,
        {
            "status": "running",
            "updated_at": now_iso(),
            "current_step": "recovery: resuming large_fixed enrich from partial db",
            "next_step": "finish large_fixed, materialize clean report db, export audit, then run fresh30",
            "recovery_started_at": now_iso(),
            "recovery_reason": "background runner disappeared before completion; partial large_fixed db left with enrich batch_run still marked running and no final report/audit artifacts",
        },
    )

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as logf:
        env = dict(os.environ)
        env["SQLITE_PATH"] = str(large_partial)
        env["MGAP_POLICY_PROFILE"] = str(profile)
        env["PYTHONPATH"] = str(project_root / "src")

        merge_update(
            state_path,
            {
                "updated_at": now_iso(),
                "current_step": "recovery: continue enrich on partial large_fixed db",
                "current_run": {
                    "label": "large_fixed_arxiv_gate",
                    "mode": "resume_enrich",
                    "source_db": str(large_source),
                    "resume_db": str(large_partial),
                    "report_out": str(large_report),
                    "audit_csv": str(large_audit),
                    "policy_profile": str(profile),
                },
            },
        )
        run_logged(
            [python_bin, "-m", "mygooglealertpapers.cli", "enrich-candidates", "--limit", "1000000"],
            cwd=project_root,
            env=env,
            logf=logf,
            banner=f"[{now_iso()}] RESUME enrich large_fixed from partial db\n",
        )

        if large_resume_source.exists():
            large_resume_source.unlink()
        shutil.move(str(large_partial), str(large_resume_source))

        merge_update(
            state_path,
            {
                "updated_at": now_iso(),
                "current_step": "recovery: materialize clean large_fixed replay db with resumed source records",
                "current_run": {
                    "label": "large_fixed_arxiv_gate",
                    "mode": "merge_dedup_report",
                    "source_db": str(large_source),
                    "reuse_source_records_from": str(large_resume_source),
                    "output_db": str(large_partial),
                    "report_out": str(large_report),
                    "audit_csv": str(large_audit),
                    "policy_profile": str(profile),
                },
            },
        )
        run_logged(
            [
                python_bin,
                "scripts/replay_validation.py",
                "--source-db",
                str(large_source),
                "--output-db",
                str(large_partial),
                "--reuse-source-records-from",
                str(large_resume_source),
                "--policy-profile",
                str(profile),
                "--report-out",
                str(large_report),
                "--limit",
                "1000000",
                "--stages",
                "merge",
                "dedup",
                "--stage-timeout-seconds",
                "10800",
            ],
            cwd=project_root,
            logf=logf,
            banner=f"[{now_iso()}] MATERIALIZE large_fixed final replay db from resumed source records\n",
        )

        merge_update(
            state_path,
            {
                "updated_at": now_iso(),
                "current_step": "recovery: export large_fixed residual audit",
            },
        )
        run_logged(
            [
                python_bin,
                "scripts/export_post_openalex_residual_audit.py",
                "--source-db",
                str(large_source),
                "--results-db",
                str(large_partial),
                "--policy-profile",
                str(profile),
                "--out-csv",
                str(large_audit),
                "--slice-name",
                "large_fixed_arxiv_gate",
            ],
            cwd=project_root,
            logf=logf,
            banner=f"[{now_iso()}] EXPORT audit large_fixed\n",
        )
        append_completed_run(
            state_path,
            {
                "label": "large_fixed_arxiv_gate",
                "source_db": str(large_source),
                "resume_source_db": str(large_resume_source),
                "output_db": str(large_partial),
                "report_out": str(large_report),
                "report_md": str(large_report.with_suffix('.md')),
                "audit_csv": str(large_audit),
                "policy_profile": str(profile),
                "candidate_count": 368,
                "completed_at": now_iso(),
                "recovered": True,
            },
        )

        merge_update(
            state_path,
            {
                "updated_at": now_iso(),
                "current_step": "running replay 2/2: fresh30_arxiv_gate",
                "current_run": {
                    "label": "fresh30_arxiv_gate",
                    "mode": "full_replay",
                    "source_db": str(fresh_source),
                    "output_db": str(fresh_output),
                    "report_out": str(fresh_report),
                    "audit_csv": str(fresh_audit),
                    "policy_profile": str(profile),
                },
            },
        )
        run_logged(
            [
                python_bin,
                "scripts/replay_validation.py",
                "--source-db",
                str(fresh_source),
                "--output-db",
                str(fresh_output),
                "--policy-profile",
                str(profile),
                "--report-out",
                str(fresh_report),
                "--limit",
                "1000000",
                "--stages",
                "enrich",
                "merge",
                "dedup",
                "--stage-timeout-seconds",
                "10800",
            ],
            cwd=project_root,
            logf=logf,
            banner=f"[{now_iso()}] START fresh30 full replay\n",
        )

        merge_update(
            state_path,
            {
                "updated_at": now_iso(),
                "current_step": "exporting audit 2/2: fresh30_arxiv_gate",
            },
        )
        run_logged(
            [
                python_bin,
                "scripts/export_post_openalex_residual_audit.py",
                "--source-db",
                str(fresh_source),
                "--results-db",
                str(fresh_output),
                "--policy-profile",
                str(profile),
                "--out-csv",
                str(fresh_audit),
                "--slice-name",
                "fresh30_arxiv_gate",
            ],
            cwd=project_root,
            logf=logf,
            banner=f"[{now_iso()}] EXPORT audit fresh30\n",
        )
        append_completed_run(
            state_path,
            {
                "label": "fresh30_arxiv_gate",
                "source_db": str(fresh_source),
                "output_db": str(fresh_output),
                "report_out": str(fresh_report),
                "report_md": str(fresh_report.with_suffix('.md')),
                "audit_csv": str(fresh_audit),
                "policy_profile": str(profile),
                "candidate_count": 95,
                "completed_at": now_iso(),
                "recovered": False,
            },
        )

    merge_update(
        state_path,
        {
            "status": "completed",
            "updated_at": now_iso(),
            "finished_at": now_iso(),
            "current_step": "residual decomposition replay + audit finished after recovery",
            "next_step": "analyze non-suppression reasons and decide next non-arXiv optimization target",
            "current_run": None,
        },
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        state_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
        if state_path is not None:
            merge_update(
                state_path,
                {
                    "status": "failed",
                    "updated_at": now_iso(),
                    "finished_at": now_iso(),
                    "current_step": "recovery flow failed",
                    "next_step": "inspect recovery log and failing command",
                    "error": {
                        "type": "CalledProcessError",
                        "returncode": exc.returncode,
                        "cmd": exc.cmd,
                    },
                },
            )
        raise
    except Exception as exc:
        state_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
        if state_path is not None:
            merge_update(
                state_path,
                {
                    "status": "failed",
                    "updated_at": now_iso(),
                    "finished_at": now_iso(),
                    "current_step": "recovery flow failed before completion",
                    "next_step": "inspect traceback",
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                },
            )
        raise
