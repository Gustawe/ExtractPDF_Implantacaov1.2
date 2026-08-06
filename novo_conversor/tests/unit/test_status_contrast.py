from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from conversor_folhas.application.models import HistoryRecord, QueueStatus
from conversor_folhas.application.queue_manager import QueueManager
from conversor_folhas.ui.history_dialog import HistoryTableModel
from conversor_folhas.ui.queue_table_model import QueueTableModel
from conversor_folhas.ui.result_details_dialog import ResultDetailsDialog
from conversor_folhas.ui.theme import apply_theme
from folha_pdf_xlsx.models import ConversionDetails, ProcessingIssue, ValidationCheck


MINIMUM_CONTRAST = 4.5


def test_queue_status_cells_keep_contrast_in_both_themes(qapp, tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    manager = QueueManager()
    item = manager.add_paths([pdf]).added[0]
    model = QueueTableModel(manager)
    index = model.index(0, 2)

    try:
        for dark_mode in (False, True):
            apply_theme(qapp, dark_mode)
            for status in (
                QueueStatus.SUCCEEDED,
                QueueStatus.WARNING,
                QueueStatus.DIVERGENCE,
                QueueStatus.FAILED,
            ):
                item.status = status
                background = model.data(index, Qt.BackgroundRole)
                foreground = model.data(index, Qt.ForegroundRole)
                assert isinstance(background, QColor)
                assert isinstance(foreground, QColor)
                assert _contrast_ratio(foreground, background) >= MINIMUM_CONTRAST
    finally:
        apply_theme(qapp, False)


def test_history_status_cells_keep_contrast_in_both_themes(qapp, tmp_path: Path) -> None:
    statuses = (
        "APROVADO",
        "APROVADO COM AVISOS",
        "APROVADO COM DIVERGÊNCIAS",
        "REPROVADO",
        "ERRO",
    )
    records = tuple(
        HistoryRecord(
            identifier=index,
            source_path=tmp_path / f"folha-{index}.pdf",
            output_path=tmp_path / f"folha-{index}.xlsx",
            status=status,
            message="",
            completed_at=datetime.now(timezone.utc),
        )
        for index, status in enumerate(statuses, start=1)
    )
    model = HistoryTableModel()
    model.replace(records)

    try:
        for dark_mode in (False, True):
            apply_theme(qapp, dark_mode)
            for row in range(model.rowCount()):
                index = model.index(row, 2)
                background = model.data(index, Qt.BackgroundRole)
                foreground = model.data(index, Qt.ForegroundRole)
                assert isinstance(background, QColor)
                assert isinstance(foreground, QColor)
                assert _contrast_ratio(foreground, background) >= MINIMUM_CONTRAST
    finally:
        apply_theme(qapp, False)


def test_details_dialog_colored_rows_keep_contrast_in_both_themes(
    qapp,
    qtbot,
) -> None:
    validation_statuses = ("DIVERGÊNCIA", "FALHA", "AVISO", "NÃO APLICÁVEL")
    details = ConversionDetails(
        validations=[
            ValidationCheck(
                source_file="folha.pdf",
                page=index,
                scope="FUNCIONÁRIO",
                record_key=str(index),
                employee_id=str(index),
                employee_name=f"Pessoa {index}",
                check="Soma de descontos",
                expected=Decimal("100.00"),
                actual=Decimal("0.00"),
                difference=Decimal("-100.00"),
                status=status,
            )
            for index, status in enumerate(validation_statuses, start=1)
        ],
        issues=[
            ProcessingIssue(
                source_file="folha.pdf",
                severity=severity,
                code=f"TESTE_{severity}",
                message="Ocorrência de teste",
            )
            for severity in ("ERRO", "AVISO")
        ],
    )

    try:
        for dark_mode in (False, True):
            apply_theme(qapp, dark_mode)
            dialog = ResultDetailsDialog("folha.pdf", details)
            qtbot.addWidget(dialog)
            for table in (dialog._validations_table, dialog._issues_table):
                for row in range(table.rowCount()):
                    for column in range(table.columnCount()):
                        item = table.item(row, column)
                        foreground_brush = item.foreground()
                        background_brush = item.background()
                        assert foreground_brush.style() != Qt.NoBrush
                        assert background_brush.style() != Qt.NoBrush
                        foreground = foreground_brush.color()
                        background = background_brush.color()
                        assert foreground.isValid()
                        assert background.isValid()
                        assert (
                            _contrast_ratio(foreground, background)
                            >= MINIMUM_CONTRAST
                        )
            dialog.close()
    finally:
        apply_theme(qapp, False)


def _contrast_ratio(first: QColor, second: QColor) -> float:
    lighter = max(_relative_luminance(first), _relative_luminance(second))
    darker = min(_relative_luminance(first), _relative_luminance(second))
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: QColor) -> float:
    channels = (color.redF(), color.greenF(), color.blueF())
    linear = tuple(
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    )
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
