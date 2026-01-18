from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Submission:
    id: int
    created_at: str
    from_user_id: int
    from_username: Optional[str]
    from_full_name: str
    file_id: str
    file_unique_id: str
    file_kind: str
    nickname: str
    genre: str
    comment: str


class SubmissionsDb:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    from_user_id INTEGER NOT NULL,
                    from_username TEXT NULL,
                    from_full_name TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    file_unique_id TEXT NOT NULL,
                    file_kind TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    comment TEXT NOT NULL
                )
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at DESC)"
            )

    def add(
        self,
        *,
        from_user_id: int,
        from_username: Optional[str],
        from_full_name: str,
        file_id: str,
        file_unique_id: str,
        file_kind: str,
        nickname: str,
        genre: str,
        comment: str,
    ) -> int:
        created_at = datetime.now(tz=timezone.utc).isoformat()
        with self._connect() as con:
            cur = con.execute(
                """
                INSERT INTO submissions (
                    created_at,
                    from_user_id,
                    from_username,
                    from_full_name,
                    file_id,
                    file_unique_id,
                    file_kind,
                    nickname,
                    genre,
                    comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    from_user_id,
                    from_username,
                    from_full_name,
                    file_id,
                    file_unique_id,
                    file_kind,
                    nickname,
                    genre,
                    comment,
                ),
            )
            return int(cur.lastrowid)

    def get(self, submission_id: int) -> Optional[Submission]:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM submissions WHERE id = ?", (submission_id,)
            ).fetchone()
            if row is None:
                return None
            return Submission(**dict(row))

    def list_latest(self, limit: int) -> list[Submission]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT * FROM submissions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [Submission(**dict(r)) for r in rows]
