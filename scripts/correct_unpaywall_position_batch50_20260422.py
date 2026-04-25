#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_TAG = "20260422_batch50"
BASE_DB = PROJECT_ROOT / f"data/mgap_unpaywall_position_baseline_v2_{RUN_TAG}.db"
ORIG_TREAT_DB = PROJECT_ROOT / f"data/mgap_unpaywall_position_candidate_unpaywall_{RUN_TAG}.db"
FIXED_TREAT_DB = PROJECT_ROOT / f"data/mgap_unpaywall_position_candidate_unpaywall_fixed_{RUN_TAG}.db"
BASE_REPORT = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-baseline-{RUN_TAG}.json"
ORIG_SUMMARY = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-summary-{RUN_TAG}.json"
CORRECTED_JSON = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-summary-{RUN_TAG}-corrected.json"
CORRECTED_MD = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-summary-{RUN_TAG}-corrected.md"
CACHE_JSON = PROJECT_ROOT / f"docs/validation/unpaywall-position-batch50-unpaywall-cache-{RUN_TAG}.json"
LOG_PATH = PROJECT_ROOT / f"data/logs/unpaywall_position_batch50_{RUN_TAG}_corrected.log"
STATE_PATH = PROJECT_ROOT / "data/task_state/unpaywall_position_batch50_20260422.json"

os.environ.setdefault("https_proxy", "http://172.18.240.1:62049")
os.environ.setdefault("http_proxy", "http://172.18.240.1:62049")
os.environ.setdefault("all_proxy", "socks5://172.18.240.1:62049")
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "ewan.wu7@gmail.com")

sys.path.insert(0, str(PROJECT_ROOT / "src"))
from mygooglealertpapers.enrich.unpaywall import query_unpaywall  # noqa: E402


def log(msg: str) -> None:
    print(msg, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


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


def q1(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0) if row else 0


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def db_summary(path: Path, policy_profile_name: str) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        return {
            "status": "ok",
            "policy_profile_name": policy_profile_name,
            "source_candidate_count": q1(conn, "SELECT COUNT(*) FROM paper_candidate"),
            "normalized_candidate_count": q1(conn, "SELECT COUNT(*) FROM paper_candidate_normalized"),
            "provider_intent_count": q1(conn, "SELECT COUNT(*) FROM candidate_enrichment_status"),
            "source_record_count": q1(conn, "SELECT COUNT(*) FROM source_record"),
            "matched_source_record_count": q1(conn, "SELECT COUNT(*) FROM source_record WHERE matched = 1"),
            "merged_metadata_proposal_count": q1(conn, "SELECT COUNT(*) FROM merged_metadata_proposal"),
            "normalized_only_fallback_proposal_count": normalized_only_fallback_count(conn),
            "canonical_paper_count": q1(conn, "SELECT COUNT(*) FROM canonical_paper"),
            "merge_review_queue_count": q1(conn, "SELECT COUNT(*) FROM merge_review_queue"),
            "cost_event_count": q1(conn, "SELECT COUNT(*) FROM cost_event"),
            "batch_run_count": q1(conn, "SELECT COUNT(*) FROM batch_run"),
            "severe_doi_conflict_count": severe_doi_conflict_count(conn),
            "total_batch_duration_ms": q1(conn, "SELECT COALESCE(SUM(duration_ms),0) FROM batch_run"),
            "total_provider_latency_ms": q1(conn, "SELECT COALESCE(SUM(latency_ms),0) FROM cost_event WHERE provider IS NOT NULL"),
            "provider_breakdown": provider_cost_breakdown(conn),
        }


def run_cli(db: Path, command: str) -> None:
    env = os.environ.copy()
    env["SQLITE_PATH"] = str(db)
    env["MGAP_POLICY_PROFILE"] = str(PROJECT_ROOT / "config/policy_profiles/conditional_sources_v2_unpaywall.yaml")
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    cmd = [sys.executable, "-m", "mygooglealertpapers.cli", command, "--limit", "1000000"]
    log("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True)
    if proc.stdout:
        log(proc.stdout.rstrip())
    if proc.stderr:
        log(proc.stderr.rstrip())
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}")


def prepare_fixed_treatment() -> None:
    if FIXED_TREAT_DB.exists():
        FIXED_TREAT_DB.unlink()
    shutil.copy2(BASE_DB, FIXED_TREAT_DB)
    with sqlite3.connect(FIXED_TREAT_DB) as dst, sqlite3.connect(ORIG_TREAT_DB) as src:
        dst.execute("PRAGMA foreign_keys = OFF")
        for table in ["source_record", "candidate_enrichment_status", "query_cache"]:
            if table == "source_record":
                rows = src.execute("SELECT * FROM source_record WHERE source_name='unpaywall'").fetchall()
            elif table == "candidate_enrichment_status":
                rows = src.execute("SELECT * FROM candidate_enrichment_status WHERE provider='unpaywall'").fetchall()
            else:
                rows = src.execute("SELECT * FROM query_cache WHERE provider='unpaywall'").fetchall()
            if rows:
                placeholders = ",".join(["?"] * len(rows[0]))
                if table == "source_record":
                    dst.executemany(f"INSERT INTO source_record VALUES ({placeholders})", rows)
                elif table == "candidate_enrichment_status":
                    dst.executemany(f"INSERT INTO candidate_enrichment_status VALUES ({placeholders})", rows)
                else:
                    dst.executemany(f"INSERT INTO query_cache VALUES ({placeholders})", rows)
        for table in ["merged_metadata_proposal", "merge_review_queue", "canonical_paper", "candidate_paper_link", "cost_event", "batch_run"]:
            dst.execute(f"DELETE FROM {table}")
        dst.commit()


def doi_set(conn: sqlite3.Connection, sql: str) -> set[str]:
    out: set[str] = set()
    for (value,) in conn.execute(sql).fetchall():
        doi = normalize_doi(value)
        if doi:
            out.add(doi)
    return out


def hydrate_unpaywall_cache(all_dois: set[str]) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    if CACHE_JSON.exists():
        cache = load_json(CACHE_JSON)
    with sqlite3.connect(ORIG_TREAT_DB) as conn:
        for query_key, response_json in conn.execute("SELECT query_key, response_json FROM query_cache WHERE provider='unpaywall' AND query_type='doi'"):
            doi = normalize_doi(query_key)
            if not doi:
                continue
            try:
                payload = json.loads(response_json) if response_json else {}
            except Exception:
                payload = {}
            cache[doi] = {
                "matched": bool(payload.get("matched")),
                "url_present": bool(payload.get("url")),
                "latency_ms": int(payload.get("latency_ms") or 0),
                "source": "existing_cache",
            }
    missing = sorted([doi for doi in all_dois if doi not in cache])
    if missing:
        log(f"Querying Unpaywall for {len(missing)} additional DOI(s) needed for post-merge/post-dedup placement analysis")
    for doi in missing:
        rec = query_unpaywall("analysis", doi=doi, email=UNPAYWALL_EMAIL)
        cache[doi] = {
            "matched": bool(rec and rec.matched),
            "url_present": bool(rec and rec.url),
            "latency_ms": int(rec.latency_ms if rec else 0),
            "source": "fresh_query",
        }
        save_json(CACHE_JSON, cache)
    return cache


def placement_stats(name: str, doi_values: set[str], cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    matched = 0
    url_present = 0
    latency_ms = 0
    fresh = 0
    cached = 0
    for doi in sorted(doi_values):
        payload = cache[doi]
        latency_ms += int(payload.get("latency_ms") or 0)
        if payload.get("matched"):
            matched += 1
        if payload.get("url_present"):
            url_present += 1
        if payload.get("source") == "fresh_query":
            fresh += 1
        else:
            cached += 1
    return {
        "placement": name,
        "unique_doi_count": len(doi_values),
        "matched_unique_doi_count": matched,
        "oa_url_unique_doi_count": url_present,
        "matched_fill_rate": round(url_present / matched, 4) if matched else None,
        "estimated_total_latency_ms": latency_ms,
        "fresh_queries_used": fresh,
        "existing_cached_queries_used": cached,
    }


def write_state(summary: dict[str, Any]) -> None:
    state = {
        "schema_version": "2026-04-21-long-run-handoff-v2",
        "flow_id": "unpaywall-position-batch50-20260422_batch50",
        "owner_session_key": "agent:deepblue:main",
        "status": "completed",
        "goal": "Use an approximately 50-mail older cached Scholar batch to quantify baseline enrich cost, measure incremental Unpaywall overhead, and decide the best insertion position.",
        "current_step": "Corrected analysis completed.",
        "next_step": "Review corrected summary and decide whether to place Unpaywall at candidate-level for lower cost or post-dedup for broader OA coverage.",
        "expected_artifacts": [str(CORRECTED_JSON), str(CORRECTED_MD), str(CACHE_JSON), str(LOG_PATH)],
        "notes": [
            "Original summary had a merge-rules confound because unpaywall_only fell back to builtin_default merge_rules; corrected analysis reran merge/dedup with conditional_sources_v2_unpaywall merge rules.",
            "Original placement recommendation math was invalid because post-merge/post-dedup DOI sets can exceed candidate DOI-extracted coverage; corrected analysis queried the additional DOI set directly.",
        ],
        "artifacts": [str(CORRECTED_JSON), str(CORRECTED_MD), str(CACHE_JSON), str(LOG_PATH)],
    }
    save_json(STATE_PATH, state)


def main() -> None:
    LOG_PATH.write_text("", encoding="utf-8")
    base = load_json(BASE_REPORT)
    orig = load_json(ORIG_SUMMARY)

    prepare_fixed_treatment()
    run_cli(FIXED_TREAT_DB, "merge-metadata")
    run_cli(FIXED_TREAT_DB, "dedup-candidates")
    fixed = db_summary(FIXED_TREAT_DB, "conditional_sources_v2_unpaywall")

    with sqlite3.connect(BASE_DB) as conn:
        candidate_dois = doi_set(conn, "SELECT doi_extracted FROM paper_candidate_normalized WHERE doi_extracted IS NOT NULL AND trim(doi_extracted) != ''")
        proposal_dois = doi_set(conn, "SELECT preferred_doi FROM merged_metadata_proposal WHERE preferred_doi IS NOT NULL AND trim(preferred_doi) != ''")
        canonical_dois = doi_set(conn, "SELECT canonical_doi FROM canonical_paper WHERE canonical_doi IS NOT NULL AND trim(canonical_doi) != ''")

    cache = hydrate_unpaywall_cache(candidate_dois | proposal_dois | canonical_dois)
    candidate_stats = placement_stats("candidate_level", candidate_dois, cache)
    proposal_stats = placement_stats("post_merge", proposal_dois, cache)
    canonical_stats = placement_stats("post_dedup", canonical_dois, cache)

    recommendation = {
        "best_position": None,
        "rationale": [],
    }
    if fixed["canonical_paper_count"] == base["canonical_paper_count"] and fixed["merge_review_queue_count"] == base["merge_review_queue_count"]:
        recommendation["rationale"].append("在相同 merge_rules 下，candidate-level 加入 Unpaywall 没有改变 canonical 数或 review queue。")
    else:
        recommendation["rationale"].append("candidate-level 在相同 merge_rules 下仍改变了下游 correctness，因此不宜前置。")

    if canonical_stats["oa_url_unique_doi_count"] > candidate_stats["oa_url_unique_doi_count"]:
        recommendation["best_position"] = "post_dedup"
        recommendation["rationale"].append(
            f"post-dedup 可覆盖 {canonical_stats['oa_url_unique_doi_count']} 个带 OA URL 的 DOI，高于 candidate-level 的 {candidate_stats['oa_url_unique_doi_count']}。"
        )
    else:
        recommendation["best_position"] = "candidate_level"
        recommendation["rationale"].append("candidate-level 的 OA URL 覆盖并不低于后置位置，因此优先保留更低请求数。")

    if proposal_stats["oa_url_unique_doi_count"] == canonical_stats["oa_url_unique_doi_count"]:
        recommendation["rationale"].append("post-merge 与 post-dedup 的 OA URL 覆盖相同，因此两者中应优先选 post-dedup。")

    corrected = {
        "run_tag": RUN_TAG,
        "selection": orig["selection"],
        "baseline_v2": base,
        "original_summary_issue": {
            "merge_rules_confound": True,
            "placement_math_bug": True,
            "note": "unpaywall_only used builtin_default merge_rules, which disabled normalized_only_fallback and invalidated the first candidate-level delta. Placement analysis also compared later DOI sets against an incomplete Unpaywall cache.",
        },
        "candidate_level_corrected": fixed,
        "candidate_level_delta_vs_baseline": {
            "canonical_paper_count": fixed["canonical_paper_count"] - base["canonical_paper_count"],
            "merge_review_queue_count": fixed["merge_review_queue_count"] - base["merge_review_queue_count"],
            "normalized_only_fallback_proposal_count": fixed["normalized_only_fallback_proposal_count"] - base["normalized_only_fallback_proposal_count"],
            "matched_source_record_count": fixed["matched_source_record_count"] - base["matched_source_record_count"],
            "provider_intent_count": fixed["provider_intent_count"] - base["provider_intent_count"],
        },
        "unpaywall_overhead_from_original_incremental_run": orig["unpaywall_overhead_vs_baseline"],
        "placement_analysis_corrected": [candidate_stats, proposal_stats, canonical_stats],
        "recommendation": recommendation,
    }
    save_json(CORRECTED_JSON, corrected)

    md = [
        f"# Corrected Unpaywall position experiment ({RUN_TAG})",
        "",
        "## What was corrected",
        "- The first summary mixed in builtin_default merge rules through `unpaywall_only`, which disabled `normalized_only_fallback` and made the candidate-level downstream delta invalid.",
        "- The first placement comparison undercounted post-merge/post-dedup cost because it only had cache for candidate-level DOI queries.",
        "",
        "## Baseline current enrich cost",
        f"- provider latency total: `{base['total_provider_latency_ms']}` ms",
        f"- canonical papers: `{base['canonical_paper_count']}`",
        f"- review queue: `{base['merge_review_queue_count']}`",
        "",
        "## Candidate-level Unpaywall, corrected downstream check",
        f"- canonical delta: `{corrected['candidate_level_delta_vs_baseline']['canonical_paper_count']}`",
        f"- review delta: `{corrected['candidate_level_delta_vs_baseline']['merge_review_queue_count']}`",
        f"- normalized_only_fallback delta: `{corrected['candidate_level_delta_vs_baseline']['normalized_only_fallback_proposal_count']}`",
        f"- matched_source_record delta: `{corrected['candidate_level_delta_vs_baseline']['matched_source_record_count']}`",
        "",
        "## Placement comparison",
        "| placement | unique DOI | OA URL DOI | matched fill rate | estimated latency ms |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in corrected["placement_analysis_corrected"]:
        md.append(f"| {item['placement']} | {item['unique_doi_count']} | {item['oa_url_unique_doi_count']} | {item['matched_fill_rate']} | {item['estimated_total_latency_ms']} |")
    md += [
        "",
        "## Recommendation",
        f"- best_position: `{recommendation['best_position']}`",
    ]
    for line in recommendation["rationale"]:
        md.append(f"- {line}")
    md += [
        "",
        "## Artifacts",
        f"- corrected json: `{CORRECTED_JSON}`",
        f"- corrected md: `{CORRECTED_MD}`",
        f"- unpaywall cache: `{CACHE_JSON}`",
    ]
    CORRECTED_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    write_state(corrected)
    log(f"Corrected summary written to {CORRECTED_JSON}")


if __name__ == "__main__":
    main()
