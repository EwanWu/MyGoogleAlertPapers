from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    imap_host: str | None
    imap_port: int
    imap_username: str | None
    imap_password: str | None
    imap_mailbox: str
    sqlite_path: Path
    log_level: str
    workspace_root: Path


def load_settings() -> Settings:
    load_dotenv()
    workspace_root = Path(__file__).resolve().parents[3]
    sqlite_path = Path(os.getenv("SQLITE_PATH", workspace_root / "data" / "mgap.db"))
    return Settings(
        imap_host=os.getenv("IMAP_HOST"),
        imap_port=int(os.getenv("IMAP_PORT", "993")),
        imap_username=os.getenv("IMAP_USERNAME"),
        imap_password=os.getenv("IMAP_PASSWORD"),
        imap_mailbox=os.getenv("IMAP_MAILBOX", "INBOX"),
        sqlite_path=sqlite_path,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        workspace_root=workspace_root,
    )
