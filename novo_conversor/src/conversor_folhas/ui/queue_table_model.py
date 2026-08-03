from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from conversor_folhas.application.models import (
    QueueAddResult,
    QueueItem,
    QueueStatus,
    queue_status_from_engine,
)
from folha_pdf_xlsx.models import ConversionDetails
from conversor_folhas.application.queue_manager import QueueManager


class QueueTableModel(QAbstractTableModel):
    HEADERS = ("Arquivo", "Pasta", "Estado", "Resultado")

    def __init__(self, manager: QueueManager) -> None:
        super().__init__()
        self._manager = manager

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._manager.items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._manager.items):
            return None
        item = self._manager.items[index.row()]

        if role == Qt.DisplayRole:
            return self._display_value(item, index.column())
        if role == Qt.ToolTipRole:
            return self._tooltip(item, index.column())
        if role == Qt.TextAlignmentRole and index.column() == 2:
            return int(Qt.AlignCenter)
        if role == Qt.BackgroundRole and index.column() == 2:
            return self._status_color(item.status)
        if role == Qt.ForegroundRole and index.column() == 2:
            return self._status_text_color(item.status)
        return None

    def add_paths(self, paths: Iterable[str | Path]) -> QueueAddResult:
        prepared, duplicate_count, invalid_count = self._manager.prepare_paths(paths)
        if not prepared:
            return QueueAddResult((), duplicate_count, invalid_count)

        first_row = len(self._manager.items)
        last_row = first_row + len(prepared) - 1
        self.beginInsertRows(QModelIndex(), first_row, last_row)
        added = self._manager.append_prepared(prepared)
        self.endInsertRows()
        return QueueAddResult(added, duplicate_count, invalid_count)

    def remove_rows(self, rows: Iterable[int]) -> int:
        removed = 0
        for row in sorted(set(rows), reverse=True):
            if not 0 <= row < len(self._manager.items):
                continue
            if self._manager.items[row].status == QueueStatus.PROCESSING:
                continue
            self.beginRemoveRows(QModelIndex(), row, row)
            removed += self._manager.remove_rows([row])
            self.endRemoveRows()
        return removed

    def remove_completed(self) -> int:
        removable = {
            QueueStatus.SUCCEEDED,
            QueueStatus.WARNING,
            QueueStatus.DIVERGENCE,
            QueueStatus.FAILED,
        }
        rows = [
            row
            for row, item in enumerate(self._manager.items)
            if item.status in removable
        ]
        return self.remove_rows(rows)

    def item_at(self, row: int) -> QueueItem | None:
        items = self._manager.items
        return items[row] if 0 <= row < len(items) else None

    def set_processing(self, identifier: str) -> None:
        self._update_item(
            identifier, QueueStatus.PROCESSING, None, "", ConversionDetails()
        )

    def set_succeeded(
        self,
        identifier: str,
        output_path: str | Path,
        engine_status: str | bool,
        message: str,
        details: ConversionDetails | None = None,
    ) -> None:
        if isinstance(engine_status, bool):
            status = QueueStatus.WARNING if engine_status else QueueStatus.SUCCEEDED
        else:
            status = queue_status_from_engine(engine_status)
        self._update_item(
            identifier,
            status,
            Path(output_path),
            message,
            details or ConversionDetails(),
        )

    def set_failed(
        self,
        identifier: str,
        message: str,
        details: ConversionDetails | None = None,
    ) -> None:
        self._update_item(
            identifier,
            QueueStatus.FAILED,
            None,
            message,
            details or ConversionDetails(),
        )

    def _update_item(
        self,
        identifier: str,
        status: QueueStatus,
        output_path: Path | None,
        message: str,
        details: ConversionDetails,
    ) -> None:
        item = self._manager.find(identifier)
        if item is None:
            return
        item.status = status
        item.output_path = output_path
        item.message = message
        item.details = details
        row = self._manager.items.index(item)
        self.dataChanged.emit(self.index(row, 0), self.index(row, 3))

    @staticmethod
    def _display_value(item: QueueItem, column: int) -> str:
        if column == 0:
            return item.source_path.name
        if column == 1:
            return str(item.source_path.parent)
        if column == 2:
            return item.status.value
        if column == 3:
            return item.output_path.name if item.output_path else "—"
        return ""

    @staticmethod
    def _tooltip(item: QueueItem, column: int) -> str:
        if column == 0:
            return str(item.source_path)
        if column == 3 and item.output_path:
            return str(item.output_path)
        if column == 2 and item.message:
            return f"{QueueTableModel._status_description(item.status)}\n{item.message}"
        if column == 2:
            return QueueTableModel._status_description(item.status)
        return ""

    @staticmethod
    def _status_description(status: QueueStatus) -> str:
        descriptions = {
            QueueStatus.WAITING: "Arquivo aguardando o início da conversão.",
            QueueStatus.PROCESSING: "Conversão em andamento.",
            QueueStatus.SUCCEEDED: "XLSX gerado sem pendências.",
            QueueStatus.WARNING: "XLSX gerado com avisos que podem exigir revisão.",
            QueueStatus.DIVERGENCE: "XLSX gerado com divergências de valor para conferência.",
            QueueStatus.FAILED: "Não foi possível concluir uma conversão válida.",
        }
        return descriptions[status]

    @staticmethod
    def _status_color(status: QueueStatus) -> QColor | None:
        colors = {
            QueueStatus.SUCCEEDED: QColor("#e2f0d9"),
            QueueStatus.WARNING: QColor("#fff2cc"),
            QueueStatus.DIVERGENCE: QColor("#fce4d6"),
            QueueStatus.FAILED: QColor("#f4cccc"),
        }
        return colors.get(status)

    @staticmethod
    def _status_text_color(status: QueueStatus) -> QColor | None:
        if status in {
            QueueStatus.SUCCEEDED,
            QueueStatus.WARNING,
            QueueStatus.DIVERGENCE,
            QueueStatus.FAILED,
        }:
            return QColor("#202124")
        return None
