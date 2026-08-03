from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from conversor_folhas.application.models import HistoryEntry, HistoryRecord
from folha_pdf_xlsx.models import ConversionDetails


class SQLiteHistoryRepository:
    """Histórico local pequeno, consultado somente por ação do usuário."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path).expanduser().resolve()

    @property
    def database_path(self) -> Path:
        return self._database_path

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL,
                    output_path TEXT,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT '',
                    details_json TEXT,
                    completed_at TEXT NOT NULL
                )
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute(
                    "PRAGMA table_info(conversion_history)"
                ).fetchall()
            }
            if "details_json" not in columns:
                connection.execute(
                    "ALTER TABLE conversion_history ADD COLUMN details_json TEXT"
                )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversion_history_completed
                ON conversion_history (completed_at DESC)
                """
            )

    def record(self, entry: HistoryEntry) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversion_history (
                    source_path,
                    output_path,
                    status,
                    message,
                    details_json,
                    completed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(entry.source_path),
                    str(entry.output_path) if entry.output_path else None,
                    entry.status,
                    entry.message,
                    json.dumps(
                        entry.details.to_dict(),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    entry.completed_at.isoformat(),
                ),
            )

    def list_recent(self, limit: int = 500) -> tuple[HistoryRecord, ...]:
        bounded_limit = max(1, min(limit, 2_000))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, source_path, output_path, status, message,
                       details_json, completed_at
                FROM conversion_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (bounded_limit,),
            ).fetchall()
        return tuple(self._row_to_record(row) for row in rows)

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM conversion_history")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> HistoryRecord:
        output_value = row["output_path"]
        details = ConversionDetails()
        details_json = row["details_json"]
        if details_json:
            try:
                loaded = json.loads(str(details_json))
                if isinstance(loaded, dict):
                    details = ConversionDetails.from_dict(loaded)
            except (json.JSONDecodeError, TypeError, ValueError):
                details = ConversionDetails()
        return HistoryRecord(
            identifier=int(row["id"]),
            source_path=Path(row["source_path"]),
            output_path=Path(output_value) if output_value else None,
            status=str(row["status"]),
            message=str(row["message"]),
            completed_at=datetime.fromisoformat(row["completed_at"]),
            details=details,
        )
