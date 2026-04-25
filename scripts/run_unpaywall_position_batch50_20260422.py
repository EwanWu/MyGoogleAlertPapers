#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_TAG = "20260422_batch50"
SOURCE_SEED = PROJECT_ROOT / "data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
SEED_DB = PROJECT_ROOT / f"data/mgap_unpaywall_position_seed_{RUN_TAG}.db"
BASE_DB = PROJECT_ROOT / f"data/mgap_unpaywall_position_baseline_v2_{RUN_TAG}.db"
TREAT_DB = PROJECT_ROOT / f"data/mgap_unpaywall_position_candidate_unpaywall_{RUN_TAG}.db"
BASE_REPORT = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-baseline-{RUN_TAG}.json"
SUMMARY_JSON = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-summary-{RUN_TAG}.json"
SUMMARY_MD = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-summary-{RUN_TAG}.md"
SELECTION_JSON = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-selection-{RUN_TAG}.json"
LOG_PATH = PROJECT_ROOT / f"data/logs/unpaywall_position_batch50_{RUN_TAG}.log"
STATE_PATH = PROJECT_ROOT / f"data/task_state/unpaywall_position_batch50_{RUN_TAG}.json"
LIMIT = 1_000_000
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "ewan.wu7@gmail.com")


def log(message: str) -> None:
    line = message.rstrip()
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def update_state(**patch: Any) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    current: dict[str, Any] = {}
    if STATE_PATH.exists():
        current = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    current.update(patch)
    current["updated_at"] = subprocess.check_output(["date", "-Iseconds"], text=True).strip()
    STATE_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    if not text:
        return None
    prefix = "https://doi.org/"
    if text.startswith(prefix):
        text = text[len(prefix):]
    return text or None


def count_scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0) if row else 0


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
        for payload in [source_priority_trace, conflict_flags_json]:
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


def provider_cost_breakdown(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT COALESCE(provider, 'none') AS provider,
               COUNT(*) AS events,
               SUM(CASE WHEN status != 'cache_hit' THEN 1 ELSE 0 END) AS remote_events,
               SUM(CASE WHEN status = 'cache_hit' THEN 1 ELSE 0 END) AS cache_hits,
               COALESCE(SUM(latency_ms),0) AS total_latency_ms
        FROM cost_event
        GROUP BY COALESCE(provider, 'none')
        ORDER BY total_latency_ms DESC, provider
        """
    ).fetchall()
    return [
        {
            "provider": row[0],
            "events": int(row[1] or 0),
            "remote_events": int(row[2] or 0),
            "cache_hits": int(row[3] or 0),
            "total_latency_ms": int(row[4] or 0),
        }
        for row in rows
    ]


def db_summary(path: Path, policy_profile_name: str, stages: list[str]) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        return {
            "status": "ok",
            "policy_profile_name": policy_profile_name,
            "stages": stages,
            "source_candidate_count": count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate"),
            "normalized_candidate_count": count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate_normalized"),
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
            "provider_breakdown": provider_cost_breakdown(conn),
        }


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    log("$ " + " ".join(cmd))
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    merged_env.setdefault("PYTHONPATH", str(PROJECT_ROOT / "src"))
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, env=merged_env, text=True, capture_output=True)
    if proc.stdout:
        for line in proc.stdout.splitlines():
            log(line)
    if proc.stderr:
        for line in proc.stderr.splitlines():
            log(line)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")


def select_oldest_scholar_uids(limit: int = 50) -> list[str]:
    with sqlite3.connect(SOURCE_SEED) as conn:
        rows = conn.execute(
            """
            SELECT mail_uid
            FROM mail_ingestion_record
            WHERE is_google_scholar_alert = 1
            ORDER BY CASE WHEN mail_uid GLOB '[0-9]*' THEN CAST(mail_uid AS INT) ELSE 0 END ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row[0] for row in rows]


def build_subset_seed(selected_uids: list[str]) -> dict[str, Any]:
    if SEED_DB.exists():
        SEED_DB.unlink()
    shutil.copy2(SOURCE_SEED, SEED_DB)
    q = ",".join("?" for _ in selected_uids)
    with sqlite3.connect(SEED_DB) as conn:
        candidate_ids = [
            row[0]
            for row in conn.execute(
                f"SELECT candidate_id FROM paper_candidate WHERE mail_uid IN ({q}) ORDER BY id ASC",
                tuple(selected_uids),
            ).fetchall()
        ]
        q_cand = ",".join("?" for _ in candidate_ids) if candidate_ids else "''"
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(f"DELETE FROM raw_mail_snapshot WHERE mail_uid NOT IN ({q})", tuple(selected_uids))
        conn.execute(f"DELETE FROM mail_ingestion_record WHERE mail_uid NOT IN ({q})", tuple(selected_uids))
        if candidate_ids:
            conn.execute(f"DELETE FROM paper_candidate_normalized WHERE candidate_id NOT IN ({q_cand})", tuple(candidate_ids))
            conn.execute(f"DELETE FROM paper_candidate WHERE candidate_id NOT IN ({q_cand})", tuple(candidate_ids))
        else:
            conn.execute("DELETE FROM paper_candidate_normalized")
            conn.execute("DELETE FROM paper_candidate")
        for table in [
            "source_record",
            "candidate_enrichment_status",
            "merged_metadata_proposal",
            "merge_review_queue",
            "canonical_paper",
            "candidate_paper_link",
            "query_cache",
            "cost_event",
            "batch_run",
        ]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        rows = conn.execute(
            f"""
            SELECT mail_uid, internal_date, subject, num_candidates_extracted
            FROM mail_ingestion_record
            ORDER BY CASE WHEN mail_uid GLOB '[0-9]*' THEN CAST(mail_uid AS INT) ELSE 0 END ASC
            """
        ).fetchall()
        selection = {
            "selection_basis": "oldest locally cached Google Scholar alert mails from the large-slice150 seed",
            "source_seed": str(SOURCE_SEED),
            "reason_two_month_mail_unavailable": "Live IMAP mailbox access currently fails with EXAMINE Unsafe Login, so this run uses the oldest reproducible locally cached Scholar mails instead.",
            "selected_mail_count": len(rows),
            "selected_uids": [row[0] for row in rows],
            "date_range": {
                "start": rows[0][1] if rows else None,
                "end": rows[-1][1] if rows else None,
            },
            "candidate_count": count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate"),
            "normalized_candidate_count": count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate_normalized"),
            "doi_positive_candidate_count": count_scalar(conn, "SELECT COUNT(*) FROM paper_candidate_normalized WHERE doi_extracted IS NOT NULL AND trim(doi_extracted) != ''"),
            "mail_rows": [
                {
                    "mail_uid": row[0],
                    "internal_date": row[1],
                    "subject": row[2],
                    "num_candidates_extracted": row[3],
                }
                for row in rows
            ],
        }
    SELECTION_JSON.write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    return selection


def prepare_candidate_position_treatment() -> None:
    if TREAT_DB.exists():
        TREAT_DB.unlink()
    shutil.copy2(BASE_DB, TREAT_DB)
    with sqlite3.connect(TREAT_DB) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in [
            "merged_metadata_proposal",
            "merge_review_queue",
            "canonical_paper",
            "candidate_paper_link",
            "cost_event",
            "batch_run",
        ]:
            conn.execute(f"DELETE FROM {table}")
        conn.execute("DELETE FROM source_record WHERE source_name='unpaywall'")
        conn.execute("DELETE FROM candidate_enrichment_status WHERE provider='unpaywall'")
        conn.execute("DELETE FROM query_cache WHERE provider='unpaywall'")
        conn.commit()


def load_unpaywall_cache(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        "SELECT query_key, response_json FROM query_cache WHERE provider='unpaywall' AND query_type='doi'"
    ).fetchall()
    result: dict[str, dict[str, Any]] = {}
    for query_key, response_json in rows:
        doi = normalize_doi(query_key)
        if not doi:
            continue
        try:
            payload = json.loads(response_json) if response_json else {}
        except Exception:
            payload = {}
        result[doi] = {
            "matched": bool(payload.get("matched")),
            "url_present": bool(payload.get("url")),
            "latency_ms": int(payload.get("latency_ms") or 0),
            "external_id": payload.get("external_id"),
        }
    return result


def unique_doi_set(conn: sqlite3.Connection, sql: str) -> set[str]:
    rows = conn.execute(sql).fetchall()
    result: set[str] = set()
    for (value,) in rows:
        doi = normalize_doi(value)
        if doi:
            result.add(doi)
    return result


def placement_stats(name: str, doi_set: set[str], cache: dict[str, dict[str, Any]], current_size: int) -> dict[str, Any]:
    matched = 0
    with_url = 0
    total_latency = 0
    missing = 0
    for doi in doi_set:
        payload = cache.get(doi)
        if not payload:
            missing += 1
            continue
        total_latency += int(payload.get("latency_ms") or 0)
        if payload.get("matched"):
            matched += 1
        if payload.get("url_present"):
            with_url += 1
    reduction = None
    if current_size:
        reduction = round((current_size - len(doi_set)) / current_size, 4)
    return {
        "placement": name,
        "unique_doi_count": len(doi_set),
        "matched_unique_doi_count": matched,
        "oa_url_unique_doi_count": with_url,
        "matched_fill_rate": round(with_url / matched, 4) if matched else None,
        "estimated_remote_latency_ms": total_latency,
        "missing_from_current_unpaywall_cache": missing,
        "request_reduction_vs_candidate_level": reduction,
    }


def build_summary(selection: dict[str, Any]) -> dict[str, Any]:
    baseline = json.loads(BASE_REPORT.read_text(encoding="utf-8"))
    treatment = db_summary(TREAT_DB, "unpaywall_only_incremental", ["enrich", "merge", "dedup"])
    with sqlite3.connect(TREAT_DB) as conn:
        unpaywall_cache = load_unpaywall_cache(conn)
        current_unpaywall_source_records = count_scalar(conn, "SELECT COUNT(*) FROM source_record WHERE source_name='unpaywall'")
        current_unpaywall_statuses = count_scalar(conn, "SELECT COUNT(*) FROM candidate_enrichment_status WHERE provider='unpaywall'")
        current_unpaywall_cost_events = conn.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN status != 'cache_hit' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN status = 'cache_hit' THEN 1 ELSE 0 END),
                   COALESCE(SUM(latency_ms),0)
            FROM cost_event
            WHERE provider='unpaywall'
            """
        ).fetchone()
        candidate_dois = unique_doi_set(conn, "SELECT doi_extracted FROM paper_candidate_normalized WHERE doi_extracted IS NOT NULL AND trim(doi_extracted) != ''")
        proposal_dois = unique_doi_set(conn, "SELECT preferred_doi FROM merged_metadata_proposal WHERE preferred_doi IS NOT NULL AND trim(preferred_doi) != ''")
        canonical_dois = unique_doi_set(conn, "SELECT canonical_doi FROM canonical_paper WHERE canonical_doi IS NOT NULL AND trim(canonical_doi) != ''")

    current_placement = placement_stats("candidate_level_current", candidate_dois, unpaywall_cache, len(candidate_dois))
    proposal_placement = placement_stats("post_merge_proposal_level", proposal_dois, unpaywall_cache, len(candidate_dois))
    canonical_placement = placement_stats("post_dedup_canonical_level", canonical_dois, unpaywall_cache, len(candidate_dois))

    current_placement["source_record_count"] = current_unpaywall_source_records
    current_placement["candidate_status_count"] = current_unpaywall_statuses
    current_placement["cost_event_count"] = int(current_unpaywall_cost_events[0] or 0)
    current_placement["remote_event_count"] = int(current_unpaywall_cost_events[1] or 0)
    current_placement["cache_hit_count"] = int(current_unpaywall_cost_events[2] or 0)
    current_placement["actual_total_latency_ms"] = int(current_unpaywall_cost_events[3] or 0)

    baseline_provider_latency_ms = int(baseline.get("total_provider_latency_ms") or 0)
    added_unpaywall_latency_ms = current_placement["actual_total_latency_ms"]

    recommendation = {
        "best_position": "post_dedup_canonical_level",
        "why": [],
    }

    if treatment["canonical_paper_count"] != baseline["canonical_paper_count"] or treatment["merge_review_queue_count"] != baseline["merge_review_queue_count"]:
        recommendation["why"].append("在这批 50 封邮件上，candidate-level 插入已经改变了下游输出，因此不应前置到 merge 之前。")
    else:
        recommendation["why"].append("在这批 50 封邮件上，candidate-level 增量插入没有改变 canonical / review 结果，说明 Unpaywall 的 bibliographic 扰动可控。")

    if canonical_placement["oa_url_unique_doi_count"] == proposal_placement["oa_url_unique_doi_count"]:
        recommendation["why"].append("post-dedup 与 post-merge 的 OA URL 覆盖相同，因此应优先选择调用数更少的 post-dedup。")
    else:
        recommendation["best_position"] = "post_merge_proposal_level"
        recommendation["why"].append("post-merge 比 post-dedup 多保留了一部分 OA URL 覆盖，值得承担这部分额外调用。")

    recommendation["why"].append(
        f"相对 current candidate-level，post-dedup 预计把 Unpaywall 唯一 DOI 请求从 {current_placement['unique_doi_count']} 降到 {canonical_placement['unique_doi_count']}，减少比例约 {canonical_placement['request_reduction_vs_candidate_level']}。"
    )

    summary = {
        "run_tag": RUN_TAG,
        "selection": selection,
        "baseline_v2": baseline,
        "candidate_level_incremental_unpaywall": treatment,
        "candidate_level_delta_vs_baseline": {
            "canonical_paper_count": treatment["canonical_paper_count"] - baseline["canonical_paper_count"],
            "merge_review_queue_count": treatment["merge_review_queue_count"] - baseline["merge_review_queue_count"],
            "normalized_only_fallback_proposal_count": treatment["normalized_only_fallback_proposal_count"] - baseline["normalized_only_fallback_proposal_count"],
            "matched_source_record_count": treatment["matched_source_record_count"] - baseline["matched_source_record_count"],
            "provider_intent_count": treatment["provider_intent_count"] - baseline["provider_intent_count"],
        },
        "baseline_enrich_cost": {
            "total_provider_latency_ms": baseline_provider_latency_ms,
            "provider_breakdown": baseline.get("provider_summary", []),
            "paid_llm_usage": baseline.get("paid_llm_usage"),
        },
        "unpaywall_overhead_vs_baseline": {
            "added_latency_ms": added_unpaywall_latency_ms,
            "added_latency_ratio_vs_baseline": round(added_unpaywall_latency_ms / baseline_provider_latency_ms, 4) if baseline_provider_latency_ms else None,
            "added_remote_events": current_placement["remote_event_count"],
            "added_cache_hits": current_placement["cache_hit_count"],
            "added_provider_intents": treatment["provider_intent_count"] - baseline["provider_intent_count"],
            "added_source_records": current_placement["source_record_count"],
        },
        "placement_analysis": [current_placement, proposal_placement, canonical_placement],
        "recommendation": recommendation,
        "notes": [
            "两个月前的新邮件现抓失败，原因是当前 IMAP EXAMINE 返回 Unsafe Login，因此本轮采用本地最老可重放的缓存 Scholar 邮件。",
            "baseline 使用 conditional_sources_v2 全量 enrich -> merge -> dedup。",
            "treatment 不是重跑全链路，而是在 baseline DB 上只增量跑 unpaywall_only，再重新 merge -> dedup，用来隔离 Unpaywall 开销和影响。",
            "post-merge / post-dedup 位置成本是根据 candidate-level 当前 run 的真实 Unpaywall query_cache 与对应 DOI 子集估算的，不再重复打远端接口。",
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    selection = summary["selection"]
    baseline = summary["baseline_v2"]
    delta = summary["candidate_level_delta_vs_baseline"]
    overhead = summary["unpaywall_overhead_vs_baseline"]
    placements = {item["placement"]: item for item in summary["placement_analysis"]}
    rec = summary["recommendation"]

    lines = [
        f"# Unpaywall position experiment, oldest cached 50-mail batch ({RUN_TAG})",
        "",
        "## What I ran",
        f"- Seed source: `{selection['source_seed']}`",
        "- Batch choice: oldest 50 locally cached Google Scholar alert mails",
        f"- Mail date range: `{selection['date_range']['start']}` -> `{selection['date_range']['end']}`",
        f"- Mail count: `{selection['selected_mail_count']}`",
        f"- Candidate count: `{selection['candidate_count']}`",
        f"- DOI-positive normalized candidates: `{selection['doi_positive_candidate_count']}`",
        "",
        "## Constraint",
        f"- {selection['reason_two_month_mail_unavailable']}",
        "",
        "## Baseline current enrich cost (conditional_sources_v2)",
        f"- total_provider_latency_ms: `{baseline['total_provider_latency_ms']}`",
        f"- canonical_paper_count: `{baseline['canonical_paper_count']}`",
        f"- merge_review_queue_count: `{baseline['merge_review_queue_count']}`",
        f"- paid_llm_usage_present: `{baseline['paid_llm_usage']['present']}`",
        "",
        "### Provider breakdown",
    ]
    for row in baseline.get("provider_summary", []):
        lines.append(
            f"- {row['provider']}: events={row['events']}, total_latency_ms={row['total_latency_ms']}, estimated_cost_usd={row['estimated_cost_usd']}"
        )

    lines += [
        "",
        "## Incremental Unpaywall overhead on top of baseline",
        f"- added_latency_ms: `{overhead['added_latency_ms']}`",
        f"- added_latency_ratio_vs_baseline: `{overhead['added_latency_ratio_vs_baseline']}`",
        f"- added_remote_events: `{overhead['added_remote_events']}`",
        f"- added_cache_hits: `{overhead['added_cache_hits']}`",
        f"- added_provider_intents: `{overhead['added_provider_intents']}`",
        f"- added_source_records: `{overhead['added_source_records']}`",
        "",
        "## Candidate-level output delta vs baseline",
        f"- canonical_paper_count delta: `{delta['canonical_paper_count']}`",
        f"- merge_review_queue_count delta: `{delta['merge_review_queue_count']}`",
        f"- normalized_only_fallback_proposal_count delta: `{delta['normalized_only_fallback_proposal_count']}`",
        f"- matched_source_record_count delta: `{delta['matched_source_record_count']}`",
        "",
        "## Placement comparison",
        "| Placement | unique DOI | matched | OA url | fill rate | latency ms | request reduction vs current |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key in ["candidate_level_current", "post_merge_proposal_level", "post_dedup_canonical_level"]:
        item = placements[key]
        lines.append(
            f"| {item['placement']} | {item['unique_doi_count']} | {item['matched_unique_doi_count']} | {item['oa_url_unique_doi_count']} | {item['matched_fill_rate']} | {item.get('actual_total_latency_ms', item['estimated_remote_latency_ms'])} | {item['request_reduction_vs_candidate_level']} |"
        )

    lines += [
        "",
        "## Recommendation",
        f"- best_position: `{rec['best_position']}`",
    ]
    for item in rec["why"]:
        lines.append(f"- {item}")

    lines += [
        "",
        "## Artifacts",
        f"- selection: `{SELECTION_JSON}`",
        f"- baseline report: `{BASE_REPORT}`",
        f"- summary json: `{SUMMARY_JSON}`",
        f"- log: `{LOG_PATH}`",
        f"- state: `{STATE_PATH}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    update_state(
        schema_version="2026-04-21-long-run-handoff-v2",
        flow_id=f"unpaywall-position-batch50-{RUN_TAG}",
        owner_session_key="agent:deepblue:main",
        status="running",
        goal="Use an approximately 50-mail older cached Scholar batch to quantify baseline enrich cost, measure incremental Unpaywall overhead, and decide the best insertion position.",
        current_step="Selecting batch and building reproducible subset seed DB.",
        next_step="Run baseline v2 replay, then add Unpaywall incrementally and summarize placement tradeoffs.",
        expected_artifacts=[str(SELECTION_JSON), str(BASE_REPORT), str(SUMMARY_JSON), str(LOG_PATH)],
        notes=[
            "Using oldest locally cached Scholar mails because live IMAP mailbox selection is currently blocked by Unsafe Login.",
            f"UNPAYWALL_EMAIL set to {UNPAYWALL_EMAIL} for this run.",
        ],
    )

    selected_uids = select_oldest_scholar_uids(limit=50)
    selection = build_subset_seed(selected_uids)
    log(f"Selected {len(selected_uids)} oldest cached Scholar mails, date range {selection['date_range']['start']} -> {selection['date_range']['end']}")

    update_state(current_step="Running baseline conditional_sources_v2 replay on the 50-mail subset seed.")
    run([
        sys.executable,
        "scripts/replay_validation.py",
        "--source-db", str(SEED_DB),
        "--output-db", str(BASE_DB),
        "--policy-profile", "config/policy_profiles/conditional_sources_v2.yaml",
        "--report-out", str(BASE_REPORT),
        "--stages", "enrich", "merge", "dedup",
        "--limit", str(LIMIT),
        "--stage-timeout-seconds", "5400",
    ])

    update_state(current_step="Applying incremental Unpaywall-only enrich on top of the stable baseline source-record set.")
    prepare_candidate_position_treatment()
    common_env = {
        "SQLITE_PATH": str(TREAT_DB),
        "MGAP_POLICY_PROFILE": str(PROJECT_ROOT / "config/policy_profiles/unpaywall_only.yaml"),
        "UNPAYWALL_EMAIL": UNPAYWALL_EMAIL,
        "https_proxy": os.environ.get("https_proxy", "http://172.18.240.1:62049"),
        "http_proxy": os.environ.get("http_proxy", "http://172.18.240.1:62049"),
        "all_proxy": os.environ.get("all_proxy", "socks5://172.18.240.1:62049"),
    }
    run([sys.executable, "-m", "mygooglealertpapers.cli", "enrich-candidates", "--limit", str(LIMIT)], env=common_env)
    run([sys.executable, "-m", "mygooglealertpapers.cli", "merge-metadata", "--limit", str(LIMIT)], env=common_env)
    run([sys.executable, "-m", "mygooglealertpapers.cli", "dedup-candidates", "--limit", str(LIMIT)], env=common_env)

    update_state(current_step="Summarizing baseline cost, incremental Unpaywall overhead, and placement tradeoffs.")
    summary = build_summary(selection)
    SUMMARY_MD.write_text(render_markdown(summary), encoding="utf-8")

    update_state(
        status="completed",
        current_step="Experiment completed.",
        next_step="Read the summary and decide whether to promote Unpaywall as a post-merge or post-dedup OA enhancement step.",
        artifacts=[str(SELECTION_JSON), str(BASE_REPORT), str(SUMMARY_JSON), str(SUMMARY_MD), str(LOG_PATH)],
    )
    log(f"Done. Summary: {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
