from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from conversor_folhas.application.models import HistoryRecord
from conversor_folhas.infrastructure.history_repository import (
    SQLiteHistoryRepository,
)
from conversor_folhas.infrastructure.windows_shell import open_file, open_folder

from .result_details_dialog import ResultDetailsDialog


class HistoryTableModel(QAbstractTableModel):
    HEADERS = ("Data e hora", "Arquivo", "Estado", "Resultado")
    STATUS_LABELS = {
        "APROVADO": "Concluído",
        "APROVADO COM AVISOS": "Concluído com avisos",
        "APROVADO COM DIVERGÊNCIAS": "Concluído com divergências",
        "REPROVADO": "Concluído com divergências",
        "ERRO": "Erro",
    }

    def __init__(self) -> None:
        super().__init__()
        self._records: tuple[HistoryRecord, ...] = ()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

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
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        record = self._records[index.row()]
        if role == Qt.DisplayRole:
            return self._display_value(record, index.column())
        if role == Qt.ToolTipRole:
            return self._tooltip(record, index.column())
        if role == Qt.TextAlignmentRole and index.column() == 2:
            return int(Qt.AlignCenter)
        if role == Qt.BackgroundRole and index.column() == 2:
            return self._status_color(record.status)
        if role == Qt.ForegroundRole and index.column() == 2:
            return self._status_text_color(record.status)
        return None

    def replace(self, records: tuple[HistoryRecord, ...]) -> None:
        self.beginResetModel()
        self._records = records
        self.endResetModel()

    def record_at(self, row: int) -> HistoryRecord | None:
        return self._records[row] if 0 <= row < len(self._records) else None

    def _display_value(self, record: HistoryRecord, column: int) -> str:
        if column == 0:
            return record.completed_at.astimezone().strftime("%d/%m/%Y %H:%M")
        if column == 1:
            return record.source_path.name
        if column == 2:
            return self.STATUS_LABELS.get(record.status, record.status.title())
        if column == 3:
            return record.output_path.name if record.output_path else "—"
        return ""

    @staticmethod
    def _tooltip(record: HistoryRecord, column: int) -> str:
        if column == 1:
            return str(record.source_path)
        if column == 2:
            description = HistoryTableModel._status_description(record.status)
            return f"{description}\n{record.message}" if record.message else description
        if column == 3 and record.output_path:
            return str(record.output_path)
        return ""

    @staticmethod
    def _status_color(status: str) -> QColor | None:
        colors = {
            "APROVADO": QColor("#e2f0d9"),
            "APROVADO COM AVISOS": QColor("#fff2cc"),
            "APROVADO COM DIVERGÊNCIAS": QColor("#fce4d6"),
            "REPROVADO": QColor("#fce4d6"),
            "ERRO": QColor("#f4cccc"),
        }
        return colors.get(status)

    @staticmethod
    def _status_text_color(status: str) -> QColor | None:
        if status in {
            "APROVADO",
            "APROVADO COM AVISOS",
            "APROVADO COM DIVERGÊNCIAS",
            "REPROVADO",
            "ERRO",
        }:
            return QColor("#202124")
        return None

    @staticmethod
    def _status_description(status: str) -> str:
        descriptions = {
            "APROVADO": "XLSX gerado sem pendências.",
            "APROVADO COM AVISOS": "XLSX gerado com avisos que podem exigir revisão.",
            "APROVADO COM DIVERGÊNCIAS": (
                "XLSX gerado com divergências de valor para conferência."
            ),
            "REPROVADO": "Registro legado com pendências de validação.",
            "ERRO": "Não foi possível concluir uma conversão válida.",
        }
        return descriptions.get(status, status)


class HistoryDialog(QDialog):
    def __init__(
        self,
        repository: SQLiteHistoryRepository,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._repository = repository
        self._model = HistoryTableModel()
        self.setWindowTitle("Histórico de conversões")
        self.resize(920, 520)
        self._build_interface()
        self._load_history()

    def _build_interface(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 20, 22, 18)
        root_layout.setSpacing(12)

        title = QLabel("Histórico de conversões desta máquina")
        title.setObjectName("instructionLabel")
        root_layout.addWidget(title)

        self._summary_label = QLabel("Carregando histórico...")
        root_layout.addWidget(self._summary_label)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.selectionModel().selectionChanged.connect(self._refresh_actions)
        self._table.doubleClicked.connect(self._activate_selected)
        root_layout.addWidget(self._table, 1)

        actions = QHBoxLayout()
        self._clear_button = QPushButton("Limpar histórico")
        self._clear_button.clicked.connect(self._clear_history)
        self._details_button = QPushButton("Ver detalhes")
        self._details_button.clicked.connect(self._show_details)
        self._open_result_button = QPushButton("Abrir XLSX")
        self._open_result_button.clicked.connect(self._open_result)
        self._open_folder_button = QPushButton("Abrir pasta")
        self._open_folder_button.clicked.connect(self._open_selected_folder)
        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)
        actions.addWidget(self._clear_button)
        actions.addStretch()
        actions.addWidget(self._details_button)
        actions.addWidget(self._open_result_button)
        actions.addWidget(self._open_folder_button)
        actions.addWidget(close_buttons)
        root_layout.addLayout(actions)

        self._refresh_actions()

    def _load_history(self) -> None:
        try:
            records = self._repository.list_recent(limit=500)
        except Exception as error:
            self._model.replace(())
            self._summary_label.setText(f"Não foi possível carregar o histórico: {error}")
            return
        self._model.replace(records)
        if records:
            self._summary_label.setText(
                f"{len(records)} registro(s) mais recente(s)."
            )
        else:
            self._summary_label.setText("Nenhuma conversão registrada.")
        self._refresh_actions()

    def _clear_history(self) -> None:
        if self._model.rowCount() == 0:
            return
        answer = QMessageBox.question(
            self,
            "Limpar histórico",
            "Deseja remover todo o histórico local de conversões?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self._repository.clear()
            self._load_history()
        except Exception as error:
            QMessageBox.critical(self, "Falha ao limpar histórico", str(error))

    def _selected_record(self) -> HistoryRecord | None:
        selected = self._table.selectionModel().selectedRows()
        return self._model.record_at(selected[0].row()) if selected else None

    def _refresh_actions(self, *_args: object) -> None:
        record = self._selected_record()
        self._details_button.setEnabled(
            record is not None
            and bool(record.message or record.details.has_details)
        )
        self._open_result_button.setEnabled(
            record is not None
            and record.output_path is not None
            and record.output_path.is_file()
        )
        self._open_folder_button.setEnabled(record is not None)
        self._clear_button.setEnabled(self._model.rowCount() > 0)

    def _activate_selected(self, *_args: object) -> None:
        record = self._selected_record()
        if record is None:
            return
        if record.output_path and record.output_path.is_file():
            self._open_result()
        elif record.message or record.details.has_details:
            self._show_details()

    def _show_details(self) -> None:
        record = self._selected_record()
        if record is None or not (record.message or record.details.has_details):
            return
        ResultDetailsDialog(
            record.source_path.name,
            record.details,
            record.message,
            self,
        ).exec()

    def _open_result(self) -> None:
        record = self._selected_record()
        if record is None or record.output_path is None:
            return
        try:
            open_file(record.output_path)
        except OSError as error:
            QMessageBox.critical(self, "Não foi possível abrir o XLSX", str(error))

    def _open_selected_folder(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        target = record.output_path or record.source_path
        try:
            open_folder(target)
        except OSError as error:
            QMessageBox.critical(self, "Não foi possível abrir a pasta", str(error))
