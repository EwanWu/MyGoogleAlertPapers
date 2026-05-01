#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from mygooglealertpapers.db.schema import create_schema

DIRTY_DOI_SQL = """
SELECT COUNT(*)
FROM paper_candidate_normalized
WHERE doi_extracted LIKE '%.pdf%'
   OR doi_extracted LIKE '%/download%'
   OR doi_extracted LIKE '%_reference.pdf%'
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay validation on a fixed candidate set")
    parser.add_argument("--source-db", required=True, help="Baseline DB containing the candidate set")
    parser.add_argument("--output-db", required=True, help="Replay DB to create/reset and execute against")
    parser.add_argument("--policy-profile", required=True, help="Policy profile YAML path")
    parser.add_argument("--report-out", required=True, help="Where to write the replay summary JSON")
    parser.add_argument("--limit", type=int, default=1000000, help="Candidate limit for stage reruns")
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["enrich", "merge", "dedup"],
        choices=["normalize", "enrich", "merge", "dedup"],
        help="Stages to rerun",
    )
    parser.add_argument("--python", default="python3", help="Python interpreter for mgap CLI calls")
    parser.add_argument("--workspace", default=None, help="Project root, auto-detected when omitted")
    parser.add_argument("--reuse-source-records-from", type=str, default=None, help="Path to a DB whose source_record/candidate_enrichment_status/query_cache tables will be copied into output-db before running stages. Skips enrich stage automatically. Enables stable merge-only profile comparison without re-running enrich.")
    parser.add_argument("--stage-timeout-seconds", type=int, default=0, help="Wall-clock timeout for each mgap stage; 0 disables timeout")
    parser.add_argument("--http-fixture-record", type=str, default=None, help="Record provider HTTP responses to a JSONL fixture during enrich")
    parser.add_argument("--http-fixture-replay", type=str, default=None, help="Replay provider HTTP responses from a JSONL fixture during enrich")
    return parser.parse_args()


def reset_tables(conn: sqlite3.Connection, tables: Iterable[str]) -> None:
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in tables:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def _copy_source_records(src_conn: sqlite3.Connection, dst_conn: sqlite3.Connection) -> None:
    """Copy source_record, candidate_enrichment_status, and query_cache from src to dst."""
    for table in ['source_record', 'candidate_enrichment_status', 'query_cache']:
        dst_conn.execute(f"DELETE FROM {table}")
        src_rows = src_conn.execute(f"SELECT * FROM {table}").fetchall()
        if not src_rows:
            continue
        col_count = len(src_rows[0])
        placeholders = ','.join(['?'] * col_count)
        dst_conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", src_rows)
    dst_conn.commit()


def tables_for_stages(stages: list[str]) -> list[str]:
    ordered: list[str] = []

    def add(*tables: str) -> None:
        for table in tables:
            if table not in ordered:
                ordered.append(table)

    if "normalize" in stages:
        add("paper_candidate_normalized")
    if "normalize" in stages or "enrich" in stages:
        add("query_cache", "source_record", "candidate_enrichment_status")
    if any(stage in stages for stage in ["normalize", "enrich", "merge"]):
        add("merged_metadata_proposal", "merge_review_queue")
    if any(stage in stages for stage in ["normalize", "enrich", "merge", "dedup"]):
        add("canonical_paper", "candidate_paper_link")
    add("cost_event", "batch_run")
    return ordered


def count_scalar(conn: sqlite3.Connection, sql: str) -> int:
    row = conn.execute(sql).fetchone()
    return int(row[0] or 0) if row else 0


def provider_summary(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        SELECT COALESCE(provider, 'none') AS provider,
               COUNT(*) AS events,
               COALESCE(SUM(latency_ms),0) AS total_latency_ms,
               COALESCE(SUM(estimated_cost_usd),0) AS estimated_cost_usd
        FROM cost_event
        GROUP BY COALESCE(provider, 'none')
        ORDER BY provider
        """
    ).fetchall()
    return [
        {
            "provider": row[0],
            "events": int(row[1]),
            "total_latency_ms": int(row[2] or 0),
            "estimated_cost_usd": float(row[3] or 0.0),
        }
        for row in rows
    ]


def enrich_dispatch_summary(conn: sqlite3.Connection) -> dict[str, object] | None:
    row = conn.execute(
        "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row or not row[0]:
        return None
    try:
        payload = json.loads(row[0])
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def severe_doi_conflict_count(conn: sqlite3.Connection) -> int:
    rows = conn.execute("SELECT conflict_flags_json FROM merged_metadata_proposal").fetchall()
    count = 0
    for (payload,) in rows:
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except Exception:
            continue
        graded = data.get("graded_conflicts") or {}
        doi = graded.get("doi") or {}
        if doi.get("grade") == "C":
            count += 1
    return count


def normalized_only_fallback_count(conn: sqlite3.Connection) -> int:
    rows = conn.execute("SELECT source_priority_trace, conflict_flags_json FROM merged_metadata_proposal").fetchall()
    count = 0
    for source_priority_trace, conflict_flags_json in rows:
        payloads = [source_priority_trace, conflict_flags_json]
        for payload in payloads:
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except Exception:
                continue
            if data.get("fallback_mode") == "normalized_only":
                count += 1
                break
    return count


def run_mgap(project_root: Path, python_bin: str, sqlite_path: Path, policy_profile: Path, command: str, limit: int, timeout_seconds: int = 0, http_fixture_record: Path | None = None, http_fixture_replay: Path | None = None) -> None:
    env = dict(**__import__("os").environ)
    env["SQLITE_PATH"] = str(sqlite_path)
    env["MGAP_POLICY_PROFILE"] = str(policy_profile)
    env["PYTHONPATH"] = str(project_root / 'src')
    if http_fixture_record:
        env["MGAP_HTTP_FIXTURE_RECORD_PATH"] = str(http_fixture_record)
    else:
        env.pop("MGAP_HTTP_FIXTURE_RECORD_PATH", None)
    if http_fixture_replay:
        env["MGAP_HTTP_FIXTURE_REPLAY_PATH"] = str(http_fixture_replay)
    else:
        env.pop("MGAP_HTTP_FIXTURE_REPLAY_PATH", None)
    cmd = [python_bin, "-m", "mygooglealertpapers.cli", command, "--limit", str(limit)]
    subprocess.run(cmd, cwd=project_root, env=env, check=True, timeout=timeout_seconds or None)


def _normalize_dispatch_summary(dispatch: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(dispatch, dict):
        return {}
    payload = dict(dispatch)
    runnable = int(payload.get('runnable_provider_intents') or 0)
    processed = int(payload.get('processed_runnable_intents') or runnable or 0)
    requests = payload.get('dispatch_request_count')
    if requests is not None:
        requests = int(requests)
        payload['dispatch_request_count'] = requests
        payload['request_savings_vs_total_planned_intents'] = runnable - requests
        payload['request_savings_vs_processed_intents'] = processed - requests
    payload['processed_runnable_intents'] = processed
    if runnable:
        payload['processed_runnable_fraction'] = processed / runnable
    return payload


def render_markdown(summary: dict[str, object]) -> str:
    provider_lines = []
    for row in summary["provider_summary"]:
        provider_lines.append(
            f"- {row['provider']}: events={row['events']}, total_latency_ms={row['total_latency_ms']}, estimated_cost_usd={row['estimated_cost_usd']:.6f}"
        )
    llm = summary.get("paid_llm_usage") or {}
    dispatch = _normalize_dispatch_summary(summary.get("enrich_dispatch_summary"))
    if summary.get("status") == "failed":
        return "\n".join(
            [
                f"# Replay validation failure: {summary['policy_profile_name']}",
                "",
                "## Run context",
                f"- source_db: `{summary['source_db']}`",
                f"- output_db: `{summary['output_db']}`",
                f"- policy_profile: `{summary['policy_profile']}`",
                f"- http_fixture_record: `{summary.get('http_fixture_record')}`",
                f"- http_fixture_replay: `{summary.get('http_fixture_replay')}`",
                f"- stages: `{', '.join(summary['stages'])}`",
                "",
                "## Failure",
                f"- status: `{summary['status']}`",
                f"- failed_stage: `{summary.get('failed_stage')}`",
                f"- error_message: `{summary.get('error_message')}`",
                "",
                "## Partial counts at failure",
                f"- replay_candidate_count: `{summary['replay_candidate_count']}`",
                f"- provider_intent_count: `{summary['provider_intent_count']}`",
                f"- source_record_count: `{summary['source_record_count']}`",
                f"- matched_source_record_count: `{summary['matched_source_record_count']}`",
                f"- merged_metadata_proposal_count: `{summary['merged_metadata_proposal_count']}`",
                f"- canonical_paper_count: `{summary['canonical_paper_count']}`",
                f"- merge_review_queue_count: `{summary['merge_review_queue_count']}`",
                f"- cost_event_count: `{summary['cost_event_count']}`",
                f"- batch_run_count: `{summary['batch_run_count']}`",
                "",
                "## Runtime and accounting",
                f"- total_batch_duration_ms: `{summary['total_batch_duration_ms']}`",
                f"- total_provider_latency_ms: `{summary['total_provider_latency_ms']}`",
                f"- paid_llm_usage_present: `{llm.get('present', False)}`",
                f"- paid_llm_note: `{llm.get('note', 'n/a')}`",
                f"- dispatch_request_count: `{dispatch.get('dispatch_request_count', 'n/a')}`",
                f"- processed_runnable_intents: `{dispatch.get('processed_runnable_intents', 'n/a')}` / `{dispatch.get('runnable_provider_intents', 'n/a')}`",
                f"- pre_experimental_runnable_provider_intents: `{dispatch.get('pre_experimental_runnable_provider_intents', 'n/a')}`",
                f"- experimental_skipped_provider_intents: `{dispatch.get('experimental_skipped_provider_intents', 'n/a')}`",
                f"- request_savings_vs_processed_intents: `{dispatch.get('request_savings_vs_processed_intents', 'n/a')}`",
                f"- request_savings_vs_total_planned_intents: `{dispatch.get('request_savings_vs_total_planned_intents', dispatch.get('request_savings_vs_runnable_intents', 'n/a'))}`",
                f"- shared_title_reuse_group_count: `{dispatch.get('shared_title_reuse_group_count', 'n/a')}`",
                f"- shared_title_reuse_request_savings: `{dispatch.get('shared_title_reuse_request_savings', 'n/a')}`",
                f"- shared_title_reuse_request_savings_by_provider: `{dispatch.get('shared_title_reuse_request_savings_by_provider', 'n/a')}`",
                f"- title_lane_group_count: `{dispatch.get('title_lane_group_count', 'n/a')}`",
                f"- title_lane_request_count: `{dispatch.get('title_lane_request_count', 'n/a')}`",
                f"- title_lane_group_counts_by_reason: `{dispatch.get('title_lane_group_counts_by_reason', 'n/a')}`",
                f"- title_lane_request_counts_by_reason: `{dispatch.get('title_lane_request_counts_by_reason', 'n/a')}`",
                f"- title_lane_group_counts_by_provider: `{dispatch.get('title_lane_group_counts_by_provider', 'n/a')}`",
                f"- title_lane_request_counts_by_provider: `{dispatch.get('title_lane_request_counts_by_provider', 'n/a')}`",
                f"- title_lane_group_counts_by_provider_reason: `{dispatch.get('title_lane_group_counts_by_provider_reason', 'n/a')}`",
                f"- title_lane_request_counts_by_provider_reason: `{dispatch.get('title_lane_request_counts_by_provider_reason', 'n/a')}`",
                f"- title_lane_identifier_gap_group_counts_by_subreason: `{dispatch.get('title_lane_identifier_gap_group_counts_by_subreason', 'n/a')}`",
                f"- title_lane_identifier_gap_request_counts_by_subreason: `{dispatch.get('title_lane_identifier_gap_request_counts_by_subreason', 'n/a')}`",
                f"- title_lane_identifier_gap_group_counts_by_provider_subreason: `{dispatch.get('title_lane_identifier_gap_group_counts_by_provider_subreason', 'n/a')}`",
                f"- title_lane_identifier_gap_request_counts_by_provider_subreason: `{dispatch.get('title_lane_identifier_gap_request_counts_by_provider_subreason', 'n/a')}`",
                f"- title_lane_cache_hit_group_count: `{dispatch.get('title_lane_cache_hit_group_count', 'n/a')}`",
                f"- experimental_title_skip_subreasons_by_provider: `{dispatch.get('experimental_title_skip_subreasons_by_provider', 'n/a')}`",
                f"- openalex_title_per_page_by_subreason: `{dispatch.get('openalex_title_per_page_by_subreason', 'n/a')}`",
                f"- openalex_title_pick_best_accepted_subreasons: `{dispatch.get('openalex_title_pick_best_accepted_subreasons', 'n/a')}`",
                f"- openalex_title_extra_result_require_arxiv_id_subreasons: `{dispatch.get('openalex_title_extra_result_require_arxiv_id_subreasons', 'n/a')}`",
                f"- openalex_title_extra_result_targeted_group_count: `{dispatch.get('openalex_title_extra_result_targeted_group_count', 'n/a')}`",
                f"- openalex_title_extra_result_targeted_group_counts_by_gate_status: `{dispatch.get('openalex_title_extra_result_targeted_group_counts_by_gate_status', 'n/a')}`",
                f"- openalex_title_extra_result_effective_group_count: `{dispatch.get('openalex_title_extra_result_effective_group_count', 'n/a')}`",
                f"- openalex_title_extra_result_blocked_group_count: `{dispatch.get('openalex_title_extra_result_blocked_group_count', 'n/a')}`",
                f"- experimental_skipped_group_count: `{dispatch.get('experimental_skipped_group_count', 'n/a')}`",
                f"- experimental_skipped_group_counts_by_provider: `{dispatch.get('experimental_skipped_group_counts_by_provider', 'n/a')}`",
                f"- experimental_skipped_group_counts_by_title_subreason: `{dispatch.get('experimental_skipped_group_counts_by_title_subreason', 'n/a')}`",
                f"- post_openalex_suppressed_group_count: `{dispatch.get('post_openalex_suppressed_group_count', 'n/a')}`",
                f"- post_openalex_suppressed_group_counts_by_provider: `{dispatch.get('post_openalex_suppressed_group_counts_by_provider', 'n/a')}`",
                f"- post_openalex_suppressed_group_counts_by_title_subreason: `{dispatch.get('post_openalex_suppressed_group_counts_by_title_subreason', 'n/a')}`",
                f"- post_openalex_unsuppressed_targeted_group_count: `{dispatch.get('post_openalex_unsuppressed_targeted_group_count', 'n/a')}`",
                f"- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_reason', 'n/a')}`",
                f"- post_openalex_unsuppressed_targeted_group_counts_by_arxiv_bucket: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_arxiv_bucket', 'n/a')}`",
                f"- post_openalex_unsuppressed_targeted_group_counts_by_reason_arxiv_bucket: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_reason_arxiv_bucket', 'n/a')}`",
                f"- post_openalex_unsuppressed_targeted_group_counts_by_reason_title_subreason: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_reason_title_subreason', 'n/a')}`",
                f"- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_title_subreason', 'n/a')}`",
                f"- title_lane_post_prelink_residual_group_count: `{dispatch.get('title_lane_post_prelink_residual_group_count', 'n/a')}`",
                f"- title_lane_post_prelink_residual_request_count: `{dispatch.get('title_lane_post_prelink_residual_request_count', 'n/a')}`",
                "",
                "## Provider summary",
                *provider_lines,
            ]
        ) + "\n"
    return "\n".join(
        [
            f"# Replay validation report: {summary['policy_profile_name']}",
            "",
            "## Run context",
            f"- source_db: `{summary['source_db']}`",
            f"- output_db: `{summary['output_db']}`",
            f"- policy_profile: `{summary['policy_profile']}`",
            f"- http_fixture_record: `{summary.get('http_fixture_record')}`",
            f"- http_fixture_replay: `{summary.get('http_fixture_replay')}`",
            f"- stages: `{', '.join(summary['stages'])}`",
            "",
            "## Candidate and normalization summary",
            f"- source_candidate_count: `{summary['source_candidate_count']}`",
            f"- replay_candidate_count: `{summary['replay_candidate_count']}`",
            f"- normalized_candidate_count: `{summary['normalized_candidate_count']}`",
            f"- dirty_doi_source_count: `{summary['dirty_doi_source_count']}`",
            f"- dirty_doi_output_count: `{summary['dirty_doi_output_count']}`",
            f"- dirty_doi_repaired_count: `{summary['dirty_doi_repaired_count']}`",
            "",
            "## Replay output summary",
            f"- provider_intent_count: `{summary['provider_intent_count']}`",
            f"- source_record_count: `{summary['source_record_count']}`",
            f"- matched_source_record_count: `{summary['matched_source_record_count']}`",
            f"- merged_metadata_proposal_count: `{summary['merged_metadata_proposal_count']}`",
            f"- normalized_only_fallback_proposal_count: `{summary['normalized_only_fallback_proposal_count']}`",
            f"- canonical_paper_count: `{summary['canonical_paper_count']}`",
            f"- merge_review_queue_count: `{summary['merge_review_queue_count']}`",
            f"- severe_doi_conflict_count: `{summary['severe_doi_conflict_count']}`",
            "",
            "## Runtime and accounting",
            f"- total_batch_duration_ms: `{summary['total_batch_duration_ms']}`",
            f"- total_provider_latency_ms: `{summary['total_provider_latency_ms']}`",
            f"- cost_event_count: `{summary['cost_event_count']}`",
            f"- batch_run_count: `{summary['batch_run_count']}`",
            f"- paid_llm_usage_present: `{llm.get('present', False)}`",
            f"- paid_llm_note: `{llm.get('note', 'n/a')}`",
            f"- dispatch_request_count: `{dispatch.get('dispatch_request_count', 'n/a')}`",
            f"- processed_runnable_intents: `{dispatch.get('processed_runnable_intents', 'n/a')}` / `{dispatch.get('runnable_provider_intents', 'n/a')}`",
            f"- pre_experimental_runnable_provider_intents: `{dispatch.get('pre_experimental_runnable_provider_intents', 'n/a')}`",
            f"- experimental_skipped_provider_intents: `{dispatch.get('experimental_skipped_provider_intents', 'n/a')}`",
            f"- request_savings_vs_processed_intents: `{dispatch.get('request_savings_vs_processed_intents', 'n/a')}`",
            f"- request_savings_vs_total_planned_intents: `{dispatch.get('request_savings_vs_total_planned_intents', dispatch.get('request_savings_vs_runnable_intents', 'n/a'))}`",
            f"- shared_title_reuse_group_count: `{dispatch.get('shared_title_reuse_group_count', 'n/a')}`",
            f"- shared_title_reuse_request_savings: `{dispatch.get('shared_title_reuse_request_savings', 'n/a')}`",
            f"- shared_title_reuse_request_savings_by_provider: `{dispatch.get('shared_title_reuse_request_savings_by_provider', 'n/a')}`",
            f"- title_lane_group_count: `{dispatch.get('title_lane_group_count', 'n/a')}`",
            f"- title_lane_request_count: `{dispatch.get('title_lane_request_count', 'n/a')}`",
            f"- title_lane_group_counts_by_reason: `{dispatch.get('title_lane_group_counts_by_reason', 'n/a')}`",
            f"- title_lane_request_counts_by_reason: `{dispatch.get('title_lane_request_counts_by_reason', 'n/a')}`",
            f"- title_lane_group_counts_by_provider: `{dispatch.get('title_lane_group_counts_by_provider', 'n/a')}`",
            f"- title_lane_request_counts_by_provider: `{dispatch.get('title_lane_request_counts_by_provider', 'n/a')}`",
            f"- title_lane_group_counts_by_provider_reason: `{dispatch.get('title_lane_group_counts_by_provider_reason', 'n/a')}`",
            f"- title_lane_request_counts_by_provider_reason: `{dispatch.get('title_lane_request_counts_by_provider_reason', 'n/a')}`",
            f"- title_lane_identifier_gap_group_counts_by_subreason: `{dispatch.get('title_lane_identifier_gap_group_counts_by_subreason', 'n/a')}`",
            f"- title_lane_identifier_gap_request_counts_by_subreason: `{dispatch.get('title_lane_identifier_gap_request_counts_by_subreason', 'n/a')}`",
            f"- title_lane_identifier_gap_group_counts_by_provider_subreason: `{dispatch.get('title_lane_identifier_gap_group_counts_by_provider_subreason', 'n/a')}`",
            f"- title_lane_identifier_gap_request_counts_by_provider_subreason: `{dispatch.get('title_lane_identifier_gap_request_counts_by_provider_subreason', 'n/a')}`",
            f"- title_lane_cache_hit_group_count: `{dispatch.get('title_lane_cache_hit_group_count', 'n/a')}`",
            f"- experimental_title_skip_subreasons_by_provider: `{dispatch.get('experimental_title_skip_subreasons_by_provider', 'n/a')}`",
            f"- openalex_title_per_page_by_subreason: `{dispatch.get('openalex_title_per_page_by_subreason', 'n/a')}`",
            f"- openalex_title_pick_best_accepted_subreasons: `{dispatch.get('openalex_title_pick_best_accepted_subreasons', 'n/a')}`",
            f"- experimental_skipped_group_count: `{dispatch.get('experimental_skipped_group_count', 'n/a')}`",
            f"- experimental_skipped_group_counts_by_provider: `{dispatch.get('experimental_skipped_group_counts_by_provider', 'n/a')}`",
            f"- experimental_skipped_group_counts_by_title_subreason: `{dispatch.get('experimental_skipped_group_counts_by_title_subreason', 'n/a')}`",
            f"- post_openalex_suppressed_group_count: `{dispatch.get('post_openalex_suppressed_group_count', 'n/a')}`",
            f"- post_openalex_suppressed_group_counts_by_provider: `{dispatch.get('post_openalex_suppressed_group_counts_by_provider', 'n/a')}`",
            f"- post_openalex_suppressed_group_counts_by_title_subreason: `{dispatch.get('post_openalex_suppressed_group_counts_by_title_subreason', 'n/a')}`",
            f"- post_openalex_unsuppressed_targeted_group_count: `{dispatch.get('post_openalex_unsuppressed_targeted_group_count', 'n/a')}`",
            f"- post_openalex_unsuppressed_targeted_group_counts_by_reason: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_reason', 'n/a')}`",
            f"- post_openalex_unsuppressed_targeted_group_counts_by_title_subreason: `{dispatch.get('post_openalex_unsuppressed_targeted_group_counts_by_title_subreason', 'n/a')}`",
            f"- title_lane_post_prelink_residual_group_count: `{dispatch.get('title_lane_post_prelink_residual_group_count', 'n/a')}`",
            f"- title_lane_post_prelink_residual_request_count: `{dispatch.get('title_lane_post_prelink_residual_request_count', 'n/a')}`",
            "",
            "## Provider summary",
            *provider_lines,
        ]
    ) + "\n"


def main() -> None:
    args = parse_args()
    project_root = Path(args.workspace).resolve() if args.workspace else Path(__file__).resolve().parents[1]
    source_db = Path(args.source_db).resolve()
    output_db = Path(args.output_db).resolve()
    policy_profile = Path(args.policy_profile).resolve()
    report_out = Path(args.report_out).resolve()
    markdown_out = report_out.with_suffix('.md')

    if not source_db.exists():
        raise SystemExit(f"source db not found: {source_db}")
    if not policy_profile.exists():
        raise SystemExit(f"policy profile not found: {policy_profile}")

    output_db.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_db, output_db)
    with sqlite3.connect(output_db) as conn:
        create_schema(conn)

    # Determine which stages to actually run; --reuse-source-records-from skips enrich
    stages_to_run = list(args.stages)
    if args.reuse_source_records_from:
        reuse_db = Path(args.reuse_source_records_from).resolve()
        if not reuse_db.exists():
            raise SystemExit(f"reuse source-records DB not found: {reuse_db}")
        # Copy source records before running anything; do not re-run enrich
        stages_to_run = [s for s in stages_to_run if s != "enrich"]
        with sqlite3.connect(output_db) as conn_out:
            reset_tables(conn_out, tables_for_stages(['merge', 'dedup']))
            with sqlite3.connect(reuse_db) as conn_src:
                _copy_source_records(conn_src, conn_out)

    with sqlite3.connect(output_db) as conn:
        source_candidate_count = count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate")
        replay_candidate_count = count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate_normalized")
        dirty_doi_source_count = count_scalar(conn, DIRTY_DOI_SQL)
        if not args.reuse_source_records_from:
            reset_tables(conn, tables_for_stages(args.stages))

    failed_stage = None
    error_message = None
    try:
        if "normalize" in stages_to_run:
            failed_stage = "normalize"
            run_mgap(project_root, args.python, output_db, policy_profile, "normalize-candidates", args.limit, args.stage_timeout_seconds)
        if "enrich" in stages_to_run:
            failed_stage = "enrich"
            run_mgap(
                project_root,
                args.python,
                output_db,
                policy_profile,
                "enrich-candidates",
                args.limit,
                args.stage_timeout_seconds,
                http_fixture_record=Path(args.http_fixture_record).resolve() if args.http_fixture_record else None,
                http_fixture_replay=Path(args.http_fixture_replay).resolve() if args.http_fixture_replay else None,
            )
        if "merge" in stages_to_run:
            failed_stage = "merge"
            run_mgap(project_root, args.python, output_db, policy_profile, "merge-metadata", args.limit, args.stage_timeout_seconds)
        if "dedup" in stages_to_run:
            failed_stage = "dedup"
            run_mgap(project_root, args.python, output_db, policy_profile, "dedup-candidates", args.limit, args.stage_timeout_seconds)
        failed_stage = None
    except subprocess.TimeoutExpired as exc:
        error_message = f"stage timed out after {int(exc.timeout)}s: {' '.join(exc.cmd)}"
    except subprocess.CalledProcessError as exc:
        error_message = f"command failed with exit code {exc.returncode}: {' '.join(exc.cmd)}"
    except Exception as exc:
        error_message = str(exc)

    with sqlite3.connect(output_db) as conn:
        dirty_doi_output_count = count_scalar(conn, DIRTY_DOI_SQL)
        summary = {
            "status": "failed" if error_message else "ok",
            "failed_stage": failed_stage,
            "error_message": error_message,
            "source_db": str(source_db),
            "output_db": str(output_db),
            "policy_profile": str(policy_profile),
            "policy_profile_name": policy_profile.stem,
            "http_fixture_record": str(Path(args.http_fixture_record).resolve()) if args.http_fixture_record else None,
            "http_fixture_replay": str(Path(args.http_fixture_replay).resolve()) if args.http_fixture_replay else None,
            "stages": args.stages,
            "source_candidate_count": source_candidate_count,
            "replay_candidate_count": replay_candidate_count,
            "normalized_candidate_count": count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate_normalized"),
            "dirty_doi_source_count": dirty_doi_source_count,
            "dirty_doi_output_count": dirty_doi_output_count,
            "dirty_doi_repaired_count": max(dirty_doi_source_count - dirty_doi_output_count, 0),
            "provider_intent_count": count_scalar(conn, "SELECT COUNT(*) FROM candidate_enrichment_status"),
            "source_record_count": count_scalar(conn, "SELECT COUNT(*) FROM source_record"),
            "matched_source_record_count": count_scalar(conn, "SELECT COUNT(*) FROM source_record WHERE matched = 1"),
            "merged_metadata_proposal_count": count_scalar(conn, "SELECT COUNT(*) FROM merged_metadata_proposal"),
            "normalized_only_fallback_proposal_count": normalized_only_fallback_count(conn),
            "canonical_paper_count": count_scalar(conn, "SELECT COUNT(*) FROM canonical_paper"),
            "merge_review_queue_count": count_scalar(conn, "SELECT COUNT(*) FROM merge_review_queue"),
            "cost_event_count": count_scalar(conn, "SELECT COUNT(*) FROM cost_event"),
            "batch_run_count": count_scalar(conn, "SELECT COUNT(*) FROM batch_run"),
            "severe_doi_conflict_count": severe_doi_conflict_count(conn),
            "total_batch_duration_ms": count_scalar(conn, "SELECT COALESCE(SUM(duration_ms),0) FROM batch_run"),
            "total_provider_latency_ms": count_scalar(conn, "SELECT COALESCE(SUM(latency_ms),0) FROM cost_event WHERE provider IS NOT NULL"),
            "provider_summary": provider_summary(conn),
            "enrich_dispatch_summary": _normalize_dispatch_summary(enrich_dispatch_summary(conn)),
            "paid_llm_usage": {
                "present": False,
                "note": "No paid LLM call path was exercised in this replay run.",
            },
        }

    report_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_out.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if error_message:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
