from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from conversor_folhas.application.models import HistoryEntry
from conversor_folhas.infrastructure.history_repository import (
    SQLiteHistoryRepository,
)
from conversor_folhas.ui.history_dialog import HistoryDialog


def test_history_dialog_loads_only_when_created(qtbot, tmp_path: Path) -> None:
    repository = SQLiteHistoryRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    repository.record(
        HistoryEntry(
            source_path=tmp_path / "folha.pdf",
            output_path=tmp_path / "folha.xlsx",
            status="APROVADO",
            message="",
            completed_at=datetime.now(timezone.utc),
        )
    )

    dialog = HistoryDialog(repository)
    qtbot.addWidget(dialog)

    assert dialog._model.rowCount() == 1
    assert "1 registro(s)" in dialog._summary_label.text()
