from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class AnalysisRunRecord:
    run_id: str
    created_at: str
    filename: str
    payload: dict[str, Any]


class AnalysisRunStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def save_run(self, filename: str, payload: dict[str, Any]) -> AnalysisRunRecord:
        run_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps(payload)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO analysis_runs (run_id, created_at, filename, payload) VALUES (?, ?, ?, ?)",
                (run_id, created_at, filename, serialized),
            )
        return AnalysisRunRecord(run_id=run_id, created_at=created_at, filename=filename, payload=payload)

    def list_runs(self, limit: int = 20) -> list[AnalysisRunRecord]:
        safe_limit = max(1, min(limit, 200))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT run_id, created_at, filename, payload FROM analysis_runs ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [
            AnalysisRunRecord(
                run_id=row[0],
                created_at=row[1],
                filename=row[2],
                payload=json.loads(row[3]),
            )
            for row in rows
        ]

    def get_run(self, run_id: str) -> AnalysisRunRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT run_id, created_at, filename, payload FROM analysis_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return AnalysisRunRecord(
            run_id=row[0],
            created_at=row[1],
            filename=row[2],
            payload=json.loads(row[3]),
        )