from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from conversor_folhas.application.conversion_service import ConversionService
from conversor_folhas.application.models import QueueStatus
from conversor_folhas.ui.main_window import MainWindow


class FakeEngine:
    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]:
        output_path.write_bytes(b"xlsx-de-teste")
        return "APROVADO", ""


def test_minimum_ui_flow_runs_outside_main_thread(qtbot, tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    window = MainWindow()
    window._conversion_service = ConversionService(FakeEngine())
    qtbot.addWidget(window)

    window._add_paths([pdf])

    assert window._queue_model.rowCount() == 1
    assert window._convert_button.isEnabled()
    assert window._progress_label.text() == "1 arquivo(s) aguardando conversão"

    qtbot.mouseClick(window._convert_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: not window._conversion_running, timeout=5_000)

    item = window._queue_model.item_at(0)
    assert item is not None
    assert item.status == QueueStatus.SUCCEEDED
    assert item.output_path == tmp_path / "folha.xlsx"
    assert window._progress_bar.value() == 100
