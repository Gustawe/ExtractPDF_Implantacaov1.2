from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from conversor_folhas.application.models import HistoryEntry
from conversor_folhas.infrastructure.history_repository import (
    SQLiteHistoryRepository,
)
from folha_pdf_xlsx.models import ConversionDetails, ValidationCheck


def test_history_is_persisted_ordered_and_cleared(tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    first_time = datetime(2026, 7, 31, 10, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(minutes=5)

    repository.record(
        HistoryEntry(
            source_path=tmp_path / "primeira.pdf",
            output_path=tmp_path / "primeira.xlsx",
            status="APROVADO",
            message="",
            completed_at=first_time,
        )
    )
    repository.record(
        HistoryEntry(
            source_path=tmp_path / "segunda.pdf",
            output_path=None,
            status="ERRO",
            message="layout não reconhecido",
            completed_at=second_time,
        )
    )

    records = repository.list_recent()

    assert [record.source_path.name for record in records] == [
        "segunda.pdf",
        "primeira.pdf",
    ]
    assert records[0].status == "ERRO"
    assert records[1].output_path == tmp_path / "primeira.xlsx"

    repository.clear()
    assert repository.list_recent() == ()


def test_history_limit_is_applied(tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    completed_at = datetime.now(timezone.utc)
    for index in range(3):
        repository.record(
            HistoryEntry(
                source_path=tmp_path / f"folha-{index}.pdf",
                output_path=None,
                status="ERRO",
                message="erro",
                completed_at=completed_at,
            )
        )

    assert len(repository.list_recent(limit=2)) == 2


def test_structured_details_are_persisted(tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    details = ConversionDetails(
        validations=[
            ValidationCheck(
                source_file="folha.pdf",
                page=3,
                scope="FUNCIONÁRIO",
                record_key="71",
                employee_id="71",
                employee_name="Pessoa",
                check="Soma de proventos",
                expected=Decimal("100.00"),
                actual=Decimal("90.00"),
                difference=Decimal("-10.00"),
                status="DIVERGÊNCIA",
                target_cell="Folha!E12",
            )
        ]
    )
    repository.record(
        HistoryEntry(
            source_path=tmp_path / "folha.pdf",
            output_path=tmp_path / "folha.xlsx",
            status="APROVADO COM DIVERGÊNCIAS",
            message="1 divergência(s)",
            completed_at=datetime.now(timezone.utc),
            details=details,
        )
    )

    record = repository.list_recent()[0]

    assert record.details.divergence_count == 1
    assert record.details.validations[0].difference == Decimal("-10.00")
    assert record.details.validations[0].target_cell == "Folha!E12"


def test_initialize_migrates_legacy_database_without_losing_records(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE conversion_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                output_path TEXT,
                status TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                completed_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO conversion_history (
                source_path, output_path, status, message, completed_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(tmp_path / "antiga.pdf"),
                None,
                "REPROVADO",
                "resumo legado",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    repository = SQLiteHistoryRepository(database_path)
    repository.initialize()
    record = repository.list_recent()[0]

    assert record.message == "resumo legado"
    assert not record.details.has_details
    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(conversion_history)")
        }
    assert "details_json" in columns
