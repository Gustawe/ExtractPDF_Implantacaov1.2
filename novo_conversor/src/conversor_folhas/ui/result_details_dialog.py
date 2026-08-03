from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from folha_pdf_xlsx.models import ConversionDetails


class ResultDetailsDialog(QDialog):
    """Exibe detalhes tipados sem permitir alteração do resultado."""

    def __init__(
        self,
        file_name: str,
        details: ConversionDetails,
        legacy_message: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._details = details
        self.setWindowTitle(f"Detalhes — {file_name}")
        self.resize(1120, 680)
        self._build_interface(legacy_message)
        self._populate()

    def _build_interface(self, legacy_message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        self._summary_label = QLabel(
            f"{self._details.divergence_count} divergência(s) • "
            f"{self._details.warning_count} aviso(s) • "
            f"{self._details.error_count} erro(s)"
        )
        self._summary_label.setObjectName("instructionLabel")
        layout.addWidget(self._summary_label)

        if legacy_message:
            message = QLabel(legacy_message)
            message.setWordWrap(True)
            message.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(message)
        if not self._details.has_details:
            legacy_notice = QLabel(
                "Os detalhes estruturados não estão disponíveis para esta execução. "
                "Isso ocorre em registros antigos ou quando a falha acontece antes "
                "da extração; somente o resumo armazenado pode ser exibido."
            )
            legacy_notice.setWordWrap(True)
            layout.addWidget(legacy_notice)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Situação:"))
        self._validation_filter = QComboBox()
        self._validation_filter.addItem("Todas")
        self._validation_filter.currentTextChanged.connect(self._apply_filters)
        filters.addWidget(self._validation_filter)
        filters.addWidget(QLabel("Severidade:"))
        self._severity_filter = QComboBox()
        self._severity_filter.addItem("Todas")
        self._severity_filter.currentTextChanged.connect(self._apply_filters)
        filters.addWidget(self._severity_filter)
        self._search = QLineEdit()
        self._search.setClearButtonEnabled(True)
        self._search.setPlaceholderText("Buscar funcionário, código ou mensagem")
        self._search.textChanged.connect(self._apply_filters)
        filters.addWidget(self._search, 1)
        layout.addLayout(filters)

        tabs = QTabWidget()
        self._validations_table = self._table(
            (
                "Situação",
                "Funcionário",
                "Validação",
                "Esperado",
                "Apurado",
                "Diferença",
                "Página",
                "Mensagem",
            )
        )
        self._issues_table = self._table(
            ("Severidade", "Código", "Funcionário", "Página", "Mensagem")
        )
        tabs.addTab(self._validations_table, "Validações")
        tabs.addTab(self._issues_table, "Ocorrências")
        layout.addWidget(tabs, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _table(headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setWordWrap(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _populate(self) -> None:
        validation_statuses: set[str] = set()
        for check in self._details.validations:
            row = self._validations_table.rowCount()
            self._validations_table.insertRow(row)
            values = (
                check.status,
                check.employee_name or check.employee_id or "—",
                check.check,
                _format_value(check.expected),
                _format_value(check.actual),
                _format_value(check.difference),
                str(check.page) if check.page is not None else "—",
                check.message,
            )
            color = _status_color(check.status)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, check.status)
                item.setData(Qt.UserRole + 1, " ".join(values).casefold())
                if color is not None:
                    item.setBackground(color)
                self._validations_table.setItem(row, column, item)
            validation_statuses.add(check.status)

        severities: set[str] = set()
        for issue in self._details.issues:
            row = self._issues_table.rowCount()
            self._issues_table.insertRow(row)
            values = (
                issue.severity,
                issue.code,
                issue.employee_name or "—",
                str(issue.page) if issue.page is not None else "—",
                issue.message,
            )
            color = QColor("#f4cccc") if issue.severity == "ERRO" else QColor("#fff2cc")
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, issue.severity)
                item.setData(Qt.UserRole + 1, " ".join(values).casefold())
                item.setBackground(color)
                self._issues_table.setItem(row, column, item)
            severities.add(issue.severity)

        self._validation_filter.addItems(sorted(validation_statuses))
        self._severity_filter.addItems(sorted(severities))
        self._validations_table.resizeColumnsToContents()
        self._issues_table.resizeColumnsToContents()

    def _apply_filters(self, *_args: object) -> None:
        search = self._search.text().strip().casefold()
        selected_status = self._validation_filter.currentText()
        selected_severity = self._severity_filter.currentText()
        self._filter_table(
            self._validations_table, selected_status, search
        )
        self._filter_table(self._issues_table, selected_severity, search)

    @staticmethod
    def _filter_table(table: QTableWidget, selected: str, search: str) -> None:
        for row in range(table.rowCount()):
            first = table.item(row, 0)
            category = str(first.data(Qt.UserRole)) if first else ""
            searchable = str(first.data(Qt.UserRole + 1)) if first else ""
            category_matches = selected == "Todas" or category == selected
            table.setRowHidden(row, not (category_matches and search in searchable))


def _format_value(value) -> str:
    if isinstance(value, Decimal):
        formatted = f"{value:,.2f}"
        return f"R$ {formatted.replace(',', 'X').replace('.', ',').replace('X', '.')}"
    if value is None or value == "":
        return "—"
    return str(value)


def _status_color(status: str) -> QColor | None:
    if status in {"DIVERGÊNCIA", "FALHA"}:
        return QColor("#fff2cc")
    if status == "AVISO":
        return QColor("#fce4d6")
    if status == "NÃO APLICÁVEL":
        return QColor("#e7e6e6")
    return None
