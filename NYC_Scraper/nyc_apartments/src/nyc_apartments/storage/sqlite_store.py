from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from ..models import Apartment


_SCHEMA = """
CREATE TABLE IF NOT EXISTS apartments (
    provider TEXT NOT NULL,
    id TEXT NOT NULL,
    first_seen_ts TEXT NOT NULL,
    PRIMARY KEY (provider, id)
);
"""


def _get_connection(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    if p.parent:
        p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    return conn


def upsert_apartments(db_path: str, apartments: Iterable[Apartment]) -> None:
    """Record apartments in the DB if not already present."""

    apartments = list(apartments)
    if not apartments:
        return

    conn = _get_connection(db_path)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO apartments (provider, id, first_seen_ts) VALUES (?, ?, ?)",
            [(apt.provider, apt.id, ts) for apt in apartments],
        )
    conn.close()


def get_new_since_last_run(db_path: str, apartments: Iterable[Apartment]) -> List[Apartment]:
    """Return only apartments that have not been seen before.

    This also records the new apartments in the DB.
    """

    apartments_list = list(apartments)
    if not apartments_list:
        return []

    conn = _get_connection(db_path)
    cur = conn.cursor()

    new_apts: List[Apartment] = []
    try:
        for apt in apartments_list:
            cur.execute(
                "SELECT 1 FROM apartments WHERE provider = ? AND id = ?",
                (apt.provider, apt.id),
            )
            if cur.fetchone() is None:
                new_apts.append(apt)

        # Mark new apartments as seen.
        upsert_apartments(db_path, new_apts)
    finally:
        conn.close()

    return new_apts
