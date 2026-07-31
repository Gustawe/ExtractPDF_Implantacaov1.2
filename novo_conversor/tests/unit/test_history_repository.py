from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from conversor_folhas.application.models import HistoryEntry
from conversor_folhas.infrastructure.history_repository import (
    SQLiteHistoryRepository,
)


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
