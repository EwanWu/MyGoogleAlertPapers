from __future__ import annotations

import imaplib
import logging
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MessageStub:
    uid: str
    flags: tuple[str, ...]
    internal_date: str | None
    raw_message: bytes


class ImapMailboxClient:
    def __init__(self, host: str, port: int, username: str, password: str, mailbox: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.mailbox = mailbox
        self._conn: imaplib.IMAP4_SSL | None = None

    def connect(self) -> None:
        self._conn = imaplib.IMAP4_SSL(self.host, self.port)
        self._conn.login(self.username, self.password)
        typ, _ = self._conn.select(self.mailbox, readonly=True)
        if typ != "OK":
            raise RuntimeError(f"Failed to select mailbox in readonly mode: {self.mailbox}")
        logger.info("Selected mailbox in readonly mode: %s", self.mailbox)

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn.logout()
            self._conn = None

    def fetch_message_metadata(self, limit: int, unseen_only: bool) -> list[MessageStub]:
        if self._conn is None:
            raise RuntimeError("IMAP client is not connected")
        criteria = "UNSEEN" if unseen_only else "ALL"
        typ, data = self._conn.uid("search", None, criteria)
        if typ != "OK" or not data or not data[0]:
            return []
        uids = data[0].decode().split()
        selected_uids = uids[-limit:]
        results: list[MessageStub] = []
        for uid in selected_uids:
            typ, msg_data = self._conn.uid("fetch", uid, "(FLAGS INTERNALDATE BODY.PEEK[])")
            if typ != "OK" or not msg_data:
                continue
            flags: tuple[str, ...] = tuple()
            internal_date: str | None = None
            raw_message = b""
            for item in msg_data:
                if not isinstance(item, tuple):
                    continue
                meta = item[0].decode(errors="ignore") if isinstance(item[0], bytes) else str(item[0])
                raw_message = item[1] if isinstance(item[1], bytes) else raw_message
                if "FLAGS" in meta:
                    try:
                        flags_str = meta.split("FLAGS ", 1)[1].split(" INTERNALDATE", 1)[0].strip()
                        flags = tuple(flags_str.strip("() ").split()) if flags_str else tuple()
                    except Exception:
                        flags = tuple()
                if "INTERNALDATE" in meta:
                    try:
                        internal_date = meta.split('INTERNALDATE "', 1)[1].split('"', 1)[0]
                    except Exception:
                        internal_date = None
            results.append(MessageStub(uid=uid, flags=flags, internal_date=internal_date, raw_message=raw_message))
        return results
