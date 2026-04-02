from __future__ import annotations

import argparse

from mygooglealertpapers.config import load_settings
from mygooglealertpapers.db.schema import create_schema_at_default_path
from mygooglealertpapers.logging_utils import configure_logging
from mygooglealertpapers.pipeline.ingest import parse_and_extract_candidates, scan_and_store_messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mgap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Initialize SQLite schema")

    scan_parser = subparsers.add_parser("scan-mailbox", help="Scan mailbox in read-only mode")
    scan_parser.add_argument("--limit", type=int, default=10)
    scan_parser.add_argument("--unseen-only", action="store_true")

    parse_parser = subparsers.add_parser("parse-mails", help="Parse stored raw snapshots and extract candidates")
    parse_parser.add_argument("--limit", type=int, default=50)

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
    else:
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
