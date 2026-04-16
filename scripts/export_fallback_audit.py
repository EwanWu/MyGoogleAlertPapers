#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re


def norm_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.casefold()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sim(a: str | None, b: str | None) -> float:
    aa = norm_text(a)
    bb = norm_text(b)
    if not aa or not bb:
        return 0.0
    return SequenceMatcher(None, aa, bb).ratio()


@dataclass
class AuditRow:
    candidate_id: str
    paper_id: str
    norm_title: str
    authors_short: str
    venue_guess: str | None
    year_guess: str | None
    doi_extracted: str | None
    pmid_extracted: str | None
    pmcid_extracted: str | None
    arxiv_id_extracted: str | None
    url_canonical: str | None
    preferred_title: str | None
    preferred_venue: str | None
    preferred_year: str | None
    preferred_doi: str | None
    preferred_pmid: str | None
    merge_confidence: float | None
    relation_type: str | None
    link_confidence: float | None
    evidence_rule: str | None
    fallback_mode: str | None
    matched_source_count: int
    unmatched_source_count: int
    provider_list: str
    source_title_summary: str
    max_source_title_similarity: float
    suspicion_score: int
    duplicate_group_size: int
    unique_new_canonical: int


def load_baseline_candidate_ids(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("select candidate_id from merged_metadata_proposal").fetchall()
    return {r[0] for r in rows}


def load_fallback_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        select m.candidate_id,
               m.preferred_title,
               m.preferred_venue,
               m.preferred_year,
               m.preferred_doi,
               m.preferred_pmid,
               m.merge_confidence,
               m.source_priority_trace,
               m.conflict_flags_json,
               p.norm_title,
               p.norm_authors_json,
               p.venue_guess,
               p.year_guess,
               p.doi_extracted,
               p.pmid_extracted,
               p.pmcid_extracted,
               p.arxiv_id_extracted,
               p.url_canonical,
               l.paper_id,
               l.relation_type,
               l.confidence,
               l.evidence_json
        from merged_metadata_proposal m
        join paper_candidate_normalized p on p.candidate_id = m.candidate_id
        left join candidate_paper_link l on l.candidate_id = m.candidate_id
        where json_extract(m.source_priority_trace, '$.fallback_mode') = 'normalized_only'
        order by m.candidate_id
        """
    ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "candidate_id": r[0],
                "preferred_title": r[1],
                "preferred_venue": r[2],
                "preferred_year": r[3],
                "preferred_doi": r[4],
                "preferred_pmid": r[5],
                "merge_confidence": r[6],
                "source_priority_trace": json.loads(r[7]) if r[7] else {},
                "conflict_flags": json.loads(r[8]) if r[8] else {},
                "norm_title": r[9],
                "norm_authors_json": r[10],
                "venue_guess": r[11],
                "year_guess": r[12],
                "doi_extracted": r[13],
                "pmid_extracted": r[14],
                "pmcid_extracted": r[15],
                "arxiv_id_extracted": r[16],
                "url_canonical": r[17],
                "paper_id": r[18],
                "relation_type": r[19],
                "link_confidence": r[20],
                "evidence_json": json.loads(r[21]) if r[21] else {},
            }
        )
    return out


def source_stats(conn: sqlite3.Connection, candidate_id: str, norm_title_value: str | None) -> dict:
    rows = conn.execute(
        """
        select source_name, matched, title, doi, pmid, year, venue
        from source_record
        where candidate_id = ?
        order by source_name, id
        """,
        (candidate_id,),
    ).fetchall()
    matched = 0
    unmatched = 0
    providers = []
    title_bits = []
    max_title_sim = 0.0
    for source_name, is_matched, title, doi, pmid, year, venue in rows:
        providers.append(source_name)
        if is_matched:
            matched += 1
        else:
            unmatched += 1
        if title:
            max_title_sim = max(max_title_sim, sim(norm_title_value, title))
        title_short = (title or "[no title]").replace("\n", " ").strip()
        if len(title_short) > 70:
            title_short = title_short[:67] + "..."
        detail = f"{source_name}:{title_short}"
        if doi:
            detail += f" | doi={doi}"
        elif pmid:
            detail += f" | pmid={pmid}"
        title_bits.append(detail)
    return {
        "matched_source_count": matched,
        "unmatched_source_count": unmatched,
        "provider_list": ", ".join(sorted(dict.fromkeys(providers))),
        "source_title_summary": " || ".join(title_bits),
        "max_source_title_similarity": round(max_title_sim, 3),
    }


def suspicion_score(row: dict, stats: dict) -> int:
    score = 0
    if not row.get("doi_extracted") and not row.get("pmid_extracted") and not row.get("pmcid_extracted"):
        score += 2
    if stats["max_source_title_similarity"] < 0.45:
        score += 2
    elif stats["max_source_title_similarity"] < 0.7:
        score += 1
    if stats["unmatched_source_count"] <= 2:
        score += 1
    if not row.get("venue_guess"):
        score += 1
    if row.get("year_guess") in {None, ""}:
        score += 1
    return score


def authors_short(authors_json: str | None) -> str:
    if not authors_json:
        return ""
    try:
        arr = json.loads(authors_json)
    except Exception:
        return authors_json[:120]
    if not isinstance(arr, list):
        return str(arr)[:120]
    joined = "; ".join(str(x) for x in arr[:4])
    if len(arr) > 4:
        joined += "; …"
    return joined


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-db", required=True)
    ap.add_argument("--treatment-db", required=True)
    ap.add_argument("--out-prefix", required=True, help="prefix without extension")
    args = ap.parse_args()

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = out_prefix.with_suffix(".csv")
    md_path = out_prefix.with_suffix(".md")
    json_path = out_prefix.with_suffix(".json")

    base = sqlite3.connect(args.baseline_db)
    trt = sqlite3.connect(args.treatment_db)

    baseline_candidate_ids = load_baseline_candidate_ids(base)
    fallback_rows = load_fallback_rows(trt)

    by_paper = Counter(r["paper_id"] for r in fallback_rows)

    audit_rows: list[AuditRow] = []
    for row in fallback_rows:
        stats = source_stats(trt, row["candidate_id"], row["norm_title"])
        score = suspicion_score(row, stats)
        audit_rows.append(
            AuditRow(
                candidate_id=row["candidate_id"],
                paper_id=row["paper_id"],
                norm_title=row["norm_title"] or "",
                authors_short=authors_short(row["norm_authors_json"]),
                venue_guess=row["venue_guess"],
                year_guess=row["year_guess"],
                doi_extracted=row["doi_extracted"],
                pmid_extracted=row["pmid_extracted"],
                pmcid_extracted=row["pmcid_extracted"],
                arxiv_id_extracted=row["arxiv_id_extracted"],
                url_canonical=row["url_canonical"],
                preferred_title=row["preferred_title"],
                preferred_venue=row["preferred_venue"],
                preferred_year=row["preferred_year"],
                preferred_doi=row["preferred_doi"],
                preferred_pmid=row["preferred_pmid"],
                merge_confidence=row["merge_confidence"],
                relation_type=row["relation_type"],
                link_confidence=row["link_confidence"],
                evidence_rule=(row.get("evidence_json") or {}).get("rule"),
                fallback_mode=(row.get("source_priority_trace") or {}).get("fallback_mode"),
                matched_source_count=stats["matched_source_count"],
                unmatched_source_count=stats["unmatched_source_count"],
                provider_list=stats["provider_list"],
                source_title_summary=stats["source_title_summary"],
                max_source_title_similarity=stats["max_source_title_similarity"],
                suspicion_score=score,
                duplicate_group_size=by_paper[row["paper_id"]],
                unique_new_canonical=1 if by_paper[row["paper_id"]] == 1 else 0,
            )
        )

    audit_rows.sort(key=lambda r: (-r.suspicion_score, r.max_source_title_similarity, r.candidate_id))

    fields = [f.name for f in AuditRow.__dataclass_fields__.values()]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in audit_rows:
            writer.writerow(r.__dict__)

    summary = {
        "baseline_db": args.baseline_db,
        "treatment_db": args.treatment_db,
        "fallback_row_count": len(audit_rows),
        "unique_new_canonical_count": len({r.paper_id for r in audit_rows}),
        "duplicate_paper_groups": {pid: count for pid, count in by_paper.items() if count > 1},
        "baseline_candidate_count": len(baseline_candidate_ids),
        "top_suspicious_candidate_ids": [r.candidate_id for r in audit_rows[:10]],
    }
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    top10 = audit_rows[:10]
    lines = []
    lines.append("# Package B 前半段：normalized-only fallback 审计摘要\n")
    lines.append(f"- baseline DB: `{args.baseline_db}`")
    lines.append(f"- treatment DB: `{args.treatment_db}`")
    lines.append(f"- fallback proposals: **{len(audit_rows)}**")
    lines.append(f"- unique new canonicals: **{len({r.paper_id for r in audit_rows})}**")
    dup_groups = {pid: count for pid, count in by_paper.items() if count > 1}
    lines.append(f"- duplicate paper groups among fallback rows: **{len(dup_groups)}**")
    lines.append("")
    if dup_groups:
        lines.append("## Duplicate groups")
        for pid, count in dup_groups.items():
            members = [r.candidate_id for r in audit_rows if r.paper_id == pid]
            title = next(r.norm_title for r in audit_rows if r.paper_id == pid)
            lines.append(f"- `{pid}` ({count} rows): {title}")
            for cid in members:
                lines.append(f"  - `{cid}`")
        lines.append("")
    lines.append("## Recommended first-pass audit set (top 10 by suspicion heuristic)")
    lines.append("")
    lines.append("| candidate_id | suspicion | max_title_sim | doi | year | venue | providers | title |")
    lines.append("|---|---:|---:|---|---|---|---|---|")
    for r in top10:
        title = (r.norm_title or "").replace("|", "\\|")[:90]
        doi = (r.doi_extracted or "").replace("|", "\\|")[:36]
        venue = (r.venue_guess or "").replace("|", "\\|")[:28]
        providers = (r.provider_list or "").replace("|", "\\|")[:40]
        lines.append(f"| {r.candidate_id} | {r.suspicion_score} | {r.max_source_title_similarity:.3f} | {doi} | {r.year_guess or ''} | {venue} | {providers} | {title} |")
    lines.append("")
    lines.append("## LLM 审核建议字段")
    lines.append("建议将 CSV 中以下列喂给 LLM 做逐条判断：")
    lines.append("- norm_title, authors_short, venue_guess, year_guess")
    lines.append("- doi_extracted / pmid_extracted / pmcid_extracted / arxiv_id_extracted")
    lines.append("- source_title_summary")
    lines.append("- max_source_title_similarity, suspicion_score")
    lines.append("- duplicate_group_size")
    lines.append("")
    lines.append(f"CSV: `{csv_path}`")
    lines.append(f"JSON summary: `{json_path}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"csv": str(csv_path), "md": str(md_path), "json": str(json_path), **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
