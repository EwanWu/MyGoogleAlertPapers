from __future__ import annotations

import argparse

from mygooglealertpapers.config import load_settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.logging_utils import configure_logging
from mygooglealertpapers.pipeline.ingest import parse_and_extract_candidates, scan_and_store_messages
from mygooglealertpapers.pipeline.normalize import normalize_candidates
from mygooglealertpapers.pipeline.enrich import enrich_candidates
from mygooglealertpapers.pipeline.enrich_stats import build_enrichment_stats
from mygooglealertpapers.pipeline.merge import build_merged_metadata
from mygooglealertpapers.pipeline.merge_stats import build_merge_stats
from mygooglealertpapers.pipeline.dedup import deduplicate_candidates
from mygooglealertpapers.pipeline.dedup_stats import build_dedup_stats
from mygooglealertpapers.pipeline.report import build_batch_report
from mygooglealertpapers.pipeline.stats import build_normalization_stats
from pathlib import Path

from mygooglealertpapers.pipeline.cost_stats import build_cost_stats
from mygooglealertpapers.pipeline.review_queue import build_review_queue_report, export_review_queue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mgap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize SQLite schema")

    scan_parser = subparsers.add_parser("scan-mailbox", help="Scan mailbox in read-only mode")
    scan_parser.add_argument("--limit", type=int, default=10)
    scan_parser.add_argument("--unseen-only", action="store_true")

    parse_parser = subparsers.add_parser("parse-mails", help="Parse stored raw snapshots and extract candidates")
    parse_parser.add_argument("--limit", type=int, default=50)

    normalize_parser = subparsers.add_parser("normalize-candidates", help="Normalize extracted candidates")
    normalize_parser.add_argument("--limit", type=int, default=100)

    subparsers.add_parser("report-batch", help="Show a lightweight batch report")
    enrich_parser = subparsers.add_parser("enrich-candidates", help="Enrich normalized candidates")
    enrich_parser.add_argument("--limit", type=int, default=100)

    subparsers.add_parser("report-normalization", help="Show normalization statistics")
    merge_parser = subparsers.add_parser("merge-metadata", help="Build merged metadata proposals")
    merge_parser.add_argument("--limit", type=int, default=100)

    subparsers.add_parser("report-enrichment", help="Show enrichment statistics")
    dedup_parser = subparsers.add_parser("dedup-candidates", help="Deduplicate candidates into canonical papers")
    dedup_parser.add_argument("--limit", type=int, default=100)

    subparsers.add_parser("report-merge", help="Show merged proposal statistics")
    subparsers.add_parser("report-dedup", help="Show dedup statistics")
    subparsers.add_parser("report-cost", help="Show cost/timing statistics")
    subparsers.add_parser("report-review-queue", help="Show blocked merge/canonical review queue")
    export_review_parser = subparsers.add_parser("export-review-queue", help="Export blocked merge/canonical review queue as JSONL")
    export_review_parser.add_argument("--output", type=str, default="data/exports/merge_review_queue.jsonl")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings()
    configure_logging(settings.log_level)

    if args.command == "init-db":
        create_schema_at_default_path(settings.sqlite_path)
    elif args.command == "scan-mailbox":
        scan_and_store_messages(settings, limit=args.limit, unseen_only=args.unseen_only)
    elif args.command == "parse-mails":
        parse_and_extract_candidates(settings, limit=args.limit)
    elif args.command == "normalize-candidates":
        normalize_candidates(settings, limit=args.limit)
    elif args.command == "report-batch":
        print(build_batch_report(settings.sqlite_path))
    elif args.command == "enrich-candidates":
        enrich_candidates(settings, limit=args.limit)
    elif args.command == "report-normalization":
        print(build_normalization_stats(settings.sqlite_path))
    elif args.command == "merge-metadata":
        build_merged_metadata(settings, limit=args.limit)
    elif args.command == "report-enrichment":
        print(build_enrichment_stats(settings.sqlite_path))
    elif args.command == "dedup-candidates":
        deduplicate_candidates(settings, limit=args.limit)
    elif args.command == "report-merge":
        print(build_merge_stats(settings.sqlite_path))
    elif args.command == "report-dedup":
        print(build_dedup_stats(settings.sqlite_path))
    elif args.command == "report-cost":
        print(build_cost_stats(settings.sqlite_path))
    elif args.command == "report-review-queue":
        print(build_review_queue_report(settings.sqlite_path))
    elif args.command == "export-review-queue":
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = settings.workspace_root / output_path
        print(export_review_queue(settings.sqlite_path, output_path))
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
