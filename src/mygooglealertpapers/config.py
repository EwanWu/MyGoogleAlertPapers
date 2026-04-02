from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


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
    config_source: str


def _load_external_imap_skill_env() -> dict[str, str]:
    path = Path.home() / ".config" / "imap-smtp-email" / ".env"
    if not path.exists():
        return {}
    raw = dotenv_values(path)
    result: dict[str, str] = {}
    if raw.get("IMAP_HOST"):
        result["IMAP_HOST"] = str(raw["IMAP_HOST"])
    if raw.get("IMAP_PORT"):
        result["IMAP_PORT"] = str(raw["IMAP_PORT"])
    if raw.get("IMAP_USER"):
        result["IMAP_USERNAME"] = str(raw["IMAP_USER"])
    if raw.get("IMAP_PASS"):
        result["IMAP_PASSWORD"] = str(raw["IMAP_PASS"])
    if raw.get("IMAP_MAILBOX"):
        result["IMAP_MAILBOX"] = str(raw["IMAP_MAILBOX"])
    return result


def load_settings() -> Settings:
    load_dotenv()
    workspace_root = Path(__file__).resolve().parents[2]
    external_imap_env = _load_external_imap_skill_env()

    imap_host = os.getenv("IMAP_HOST") or external_imap_env.get("IMAP_HOST")
    imap_port = int(os.getenv("IMAP_PORT") or external_imap_env.get("IMAP_PORT") or "993")
    imap_username = os.getenv("IMAP_USERNAME") or external_imap_env.get("IMAP_USERNAME")
    imap_password = os.getenv("IMAP_PASSWORD") or external_imap_env.get("IMAP_PASSWORD")
    imap_mailbox = os.getenv("IMAP_MAILBOX") or external_imap_env.get("IMAP_MAILBOX") or "INBOX"

    if os.getenv("IMAP_HOST") or os.getenv("IMAP_USERNAME") or os.getenv("IMAP_PASSWORD"):
        config_source = "project_env"
    elif external_imap_env:
        config_source = "imap_skill_env"
    else:
        config_source = "defaults_only"

    sqlite_path = Path(os.getenv("SQLITE_PATH", workspace_root / "data" / "mgap.db"))
    return Settings(
        imap_host=imap_host,
        imap_port=imap_port,
        imap_username=imap_username,
        imap_password=imap_password,
        imap_mailbox=imap_mailbox,
        sqlite_path=sqlite_path,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        workspace_root=workspace_root,
        config_source=config_source,
    )
