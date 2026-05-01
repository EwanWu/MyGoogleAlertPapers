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
        print("usage: run_day11_final_promotion_gate_large_20260501.py <state-json> <log-path>", file=sys.stderr)
        return 2

    state_path = Path(sys.argv[1]).resolve()
    log_path = Path(sys.argv[2]).resolve()
    project_root = Path(__file__).resolve().parents[1]
    python_bin = sys.executable or "python3"

    control_profile = project_root / "config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only.yaml"
    treatment_profile = project_root / "config/policy_profiles/openalex_batching_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only.yaml"

    runs = [
        {
            "label": "large_fixed_control",
            "source_db": project_root / "data/mgap_pkgB_large_slice150_seed_20260416_slice150.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_large_fixed_control_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-large-fixed-control-20260501.json",
            "policy_profile": control_profile,
            "candidate_count": 368,
        },
        {
            "label": "large_fixed_treatment",
            "source_db": project_root / "data/mgap_pkgB_large_slice150_seed_20260416_slice150.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_large_fixed_treatment_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-large-fixed-treatment-20260501.json",
            "policy_profile": treatment_profile,
            "candidate_count": 368,
        },
        {
            "label": "fresh30_control",
            "source_db": project_root / "data/mgap_fresh30_20260410.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_fresh30_control_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-fresh30-control-20260501.json",
            "policy_profile": control_profile,
            "candidate_count": 95,
        },
        {
            "label": "fresh30_treatment",
            "source_db": project_root / "data/mgap_fresh30_20260410.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_fresh30_treatment_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-fresh30-treatment-20260501.json",
            "policy_profile": treatment_profile,
            "candidate_count": 95,
        },
        {
            "label": "pkg3_guardrail100_control",
            "source_db": project_root / "data/mgap_pkg3_guardrail_100.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_pkg3_guardrail100_control_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-pkg3-guardrail100-control-20260501.json",
            "policy_profile": control_profile,
            "candidate_count": 249,
        },
        {
            "label": "pkg3_guardrail100_treatment",
            "source_db": project_root / "data/mgap_pkg3_guardrail_100.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_pkg3_guardrail100_treatment_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-pkg3-guardrail100-treatment-20260501.json",
            "policy_profile": treatment_profile,
            "candidate_count": 249,
        },
        {
            "label": "issac100_control",
            "source_db": project_root / "data/mgap_issac_100.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_issac100_control_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-issac100-control-20260501.json",
            "policy_profile": control_profile,
            "candidate_count": 244,
        },
        {
            "label": "issac100_treatment",
            "source_db": project_root / "data/mgap_issac_100.db",
            "output_db": project_root / "data/benchmark/day11_final_promotion_gate_issac100_treatment_20260501.db",
            "report_out": project_root / "docs/validation/day11-final-promotion-gate-issac100-treatment-20260501.json",
            "policy_profile": treatment_profile,
            "candidate_count": 244,
        },
    ]

    merge_update(
        state_path,
        {
            "status": "running",
            "started_at": now_iso(),
            "updated_at": now_iso(),
            "current_step": "launching large-scale final promotion-gate matrix",
            "next_step": "run control/treatment replay matrix across four source slices",
            "artifacts": [str(log_path)],
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
                    "current_step": f"running {idx}/{len(runs)}: {run['label']}",
                    "current_run": {
                        "index": idx,
                        "total": len(runs),
                        "label": run["label"],
                        "source_db": str(run["source_db"]),
                        "output_db": str(run["output_db"]),
                        "report_out": str(run["report_out"]),
                        "policy_profile": str(run["policy_profile"]),
                        "candidate_count": run["candidate_count"],
                        "started_at": now_iso(),
                    },
                },
            )
            cmd = [
                python_bin,
                "scripts/replay_validation.py",
                "--source-db",
                str(run["source_db"]),
                "--output-db",
                str(run["output_db"]),
                "--policy-profile",
                str(run["policy_profile"]),
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
            banner = f"[{now_iso()}] START {idx}/{len(runs)} {run['label']}\nCMD: {' '.join(cmd)}\n"
            print(banner, end="")
            logf.write(banner)
            logf.flush()
            subprocess.run(cmd, cwd=project_root, check=True, stdout=logf, stderr=subprocess.STDOUT)
            append_completed_run(
                state_path,
                {
                    "label": run["label"],
                    "source_db": str(run["source_db"]),
                    "output_db": str(run["output_db"]),
                    "report_out": str(run["report_out"]),
                    "report_md": str(run["report_out"].with_suffix(".md")),
                    "policy_profile": str(run["policy_profile"]),
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
            "current_step": "replay matrix finished",
            "next_step": "analyze control vs treatment and write final promotion-gate memo",
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
                    "current_step": "failed during replay matrix",
                    "next_step": "inspect log and failing report",
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
                    "next_step": "inspect log and traceback",
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                },
            )
        raise
