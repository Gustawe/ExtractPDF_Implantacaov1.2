from __future__ import annotations

from pathlib import Path

from conversor_folhas.application.models import QueueStatus
from conversor_folhas.application.queue_manager import QueueManager


def test_add_paths_filters_invalid_and_duplicate_files(tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    invalid = tmp_path / "texto.txt"
    invalid.write_text("conteúdo", encoding="utf-8")
    manager = QueueManager()

    result = manager.add_paths([pdf, pdf, invalid, tmp_path / "ausente.pdf"])

    assert len(result.added) == 1
    assert result.duplicate_count == 1
    assert result.invalid_count == 2
    assert manager.items[0].source_path == pdf.resolve()


def test_processing_item_cannot_be_removed(tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    manager = QueueManager()
    item = manager.add_paths([pdf]).added[0]
    item.status = QueueStatus.PROCESSING

    assert manager.remove_rows([0]) == 0
    assert len(manager.items) == 1


def test_pending_requests_include_only_waiting_items(tmp_path: Path) -> None:
    first = tmp_path / "primeira.pdf"
    second = tmp_path / "segunda.pdf"
    first.write_bytes(b"%PDF-1.4")
    second.write_bytes(b"%PDF-1.4")
    manager = QueueManager()
    items = manager.add_paths([first, second]).added
    items[0].status = QueueStatus.SUCCEEDED

    requests = manager.pending_requests()

    assert len(requests) == 1
    assert requests[0].source_path == second.resolve()

