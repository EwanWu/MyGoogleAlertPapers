#!/usr/bin/env python3
from __future__ import annotations

import json
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


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: run_day11_residual_decomposition_arxiv_gate_20260501.py <state-json> <log-path>", file=sys.stderr)
        return 2

    state_path = Path(sys.argv[1]).resolve()
    log_path = Path(sys.argv[2]).resolve()
    project_root = Path(__file__).resolve().parents[1]
    python_bin = sys.executable or "python3"

    profile = project_root / "config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate.yaml"

    runs = [
        {
            "label": "large_fixed_arxiv_gate",
            "source_db": project_root / "data/mgap_pkgB_large_slice150_seed_20260416_slice150.db",
            "output_db": project_root / "data/benchmark/day11_residual_decomposition_large_fixed_arxiv_gate_20260501.db",
            "report_out": project_root / "docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-20260501.json",
            "audit_csv": project_root / "docs/validation/day11-residual-decomposition-large-fixed-arxiv-gate-audit-20260501.csv",
            "candidate_count": 368,
        },
        {
            "label": "fresh30_arxiv_gate",
            "source_db": project_root / "data/mgap_fresh30_20260410.db",
            "output_db": project_root / "data/benchmark/day11_residual_decomposition_fresh30_arxiv_gate_20260501.db",
            "report_out": project_root / "docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-20260501.json",
            "audit_csv": project_root / "docs/validation/day11-residual-decomposition-fresh30-arxiv-gate-audit-20260501.csv",
            "candidate_count": 95,
        },
    ]

    merge_update(
        state_path,
        {
            "flow_id": "day11_residual_decomposition_arxiv_gate_20260501",
            "status": "running",
            "started_at": now_iso(),
            "updated_at": now_iso(),
            "current_step": "launching residual decomposition replay runs",
            "next_step": "run retained arXiv-gated profile on large_fixed and fresh30, then export residual audits",
            "artifacts": [str(log_path)],
            "policy_profile": str(profile),
            "completed_runs": [],
            "planned_run_labels": [run["label"] for run in runs],
        },
    )

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as logf:
        for idx, run in enumerate(runs, start=1):
            merge_update(
                state_path,
                {
                    "updated_at": now_iso(),
                    "current_step": f"running replay {idx}/{len(runs)}: {run['label']}",
                    "current_run": {
                        "index": idx,
                        "total": len(runs),
                        "label": run["label"],
                        "source_db": str(run["source_db"]),
                        "output_db": str(run["output_db"]),
                        "report_out": str(run["report_out"]),
                        "audit_csv": str(run["audit_csv"]),
                        "policy_profile": str(profile),
                        "candidate_count": run["candidate_count"],
                        "started_at": now_iso(),
                    },
                },
            )
            replay_cmd = [
                python_bin,
                "scripts/replay_validation.py",
                "--source-db",
                str(run["source_db"]),
                "--output-db",
                str(run["output_db"]),
                "--policy-profile",
                str(profile),
                "--report-out",
                str(run["report_out"]),
                "--limit",
                "1000000",
                "--stages",
                "enrich",
                "merge",
                "dedup",
                "--stage-timeout-seconds",
                "10800",
            ]
            replay_banner = f"[{now_iso()}] START replay {idx}/{len(runs)} {run['label']}\nCMD: {' '.join(replay_cmd)}\n"
            print(replay_banner, end="")
            logf.write(replay_banner)
            logf.flush()
            subprocess.run(replay_cmd, cwd=project_root, check=True, stdout=logf, stderr=subprocess.STDOUT)

            merge_update(
                state_path,
                {
                    "updated_at": now_iso(),
                    "current_step": f"exporting audit {idx}/{len(runs)}: {run['label']}",
                    "current_run": {
                        "index": idx,
                        "total": len(runs),
                        "label": run["label"],
                        "source_db": str(run["source_db"]),
                        "output_db": str(run["output_db"]),
                        "report_out": str(run["report_out"]),
                        "audit_csv": str(run["audit_csv"]),
                        "policy_profile": str(profile),
                        "candidate_count": run["candidate_count"],
                        "stage": "audit_export",
                    },
                },
            )
            audit_cmd = [
                python_bin,
                "scripts/export_post_openalex_residual_audit.py",
                "--source-db",
                str(run["source_db"]),
                "--results-db",
                str(run["output_db"]),
                "--policy-profile",
                str(profile),
                "--out-csv",
                str(run["audit_csv"]),
                "--slice-name",
                run["label"],
            ]
            audit_banner = f"[{now_iso()}] START audit {idx}/{len(runs)} {run['label']}\nCMD: {' '.join(audit_cmd)}\n"
            print(audit_banner, end="")
            logf.write(audit_banner)
            logf.flush()
            subprocess.run(audit_cmd, cwd=project_root, check=True, stdout=logf, stderr=subprocess.STDOUT)

            append_completed_run(
                state_path,
                {
                    "label": run["label"],
                    "source_db": str(run["source_db"]),
                    "output_db": str(run["output_db"]),
                    "report_out": str(run["report_out"]),
                    "report_md": str(run["report_out"].with_suffix(".md")),
                    "audit_csv": str(run["audit_csv"]),
                    "policy_profile": str(profile),
                    "candidate_count": run["candidate_count"],
                    "completed_at": now_iso(),
                },
            )
            tail = f"[{now_iso()}] DONE {idx}/{len(runs)} {run['label']}\n"
            print(tail, end="")
            logf.write(tail)
            logf.flush()

    merge_update(
        state_path,
        {
            "status": "completed",
            "updated_at": now_iso(),
            "finished_at": now_iso(),
            "current_step": "residual decomposition replay + audit finished",
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
                    "current_step": "failed during residual decomposition run",
                    "next_step": "inspect log and failing replay/audit command",
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
                    "current_step": "failed before completion",
                    "next_step": "inspect traceback",
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                },
            )
        raise
