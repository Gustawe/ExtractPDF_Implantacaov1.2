from __future__ import annotations

from decimal import Decimal

from conversor_folhas.ui.result_details_dialog import ResultDetailsDialog
from folha_pdf_xlsx.models import (
    ConversionDetails,
    ProcessingIssue,
    ValidationCheck,
)


def test_details_dialog_shows_summary_and_filters(qtbot) -> None:
    details = ConversionDetails(
        validations=[
            ValidationCheck(
                source_file="folha.pdf",
                page=2,
                scope="FUNCIONÁRIO",
                record_key="71",
                employee_id="71",
                employee_name="Ana Teste",
                check="Soma de proventos",
                expected=Decimal("100.00"),
                actual=Decimal("90.00"),
                difference=Decimal("-10.00"),
                status="DIVERGÊNCIA",
                message="Conferir total",
            ),
            ValidationCheck(
                source_file="folha.pdf",
                page=3,
                scope="FUNCIONÁRIO",
                record_key="72",
                employee_id="72",
                employee_name="Bruno Teste",
                check="Soma de descontos",
                expected=Decimal("0.00"),
                actual=Decimal("0.00"),
                difference=Decimal("0.00"),
                status="OK",
            ),
        ],
        issues=[
            ProcessingIssue(
                source_file="folha.pdf",
                severity="AVISO",
                code="RESUMO_FISCAL_AUSENTE",
                message="Resumo fiscal ausente",
            )
        ],
    )
    dialog = ResultDetailsDialog("folha.pdf", details)
    qtbot.addWidget(dialog)

    assert "1 divergência(s)" in dialog._summary_label.text()
    assert dialog._validations_table.item(0, 3).text() == "R$ 100,00"

    dialog._search.setText("Ana")
    assert not dialog._validations_table.isRowHidden(0)
    assert dialog._validations_table.isRowHidden(1)
    assert dialog._issues_table.isRowHidden(0)

    dialog._search.clear()
    dialog._severity_filter.setCurrentText("AVISO")
    assert not dialog._issues_table.isRowHidden(0)


def test_legacy_details_dialog_accepts_summary_only(qtbot) -> None:
    dialog = ResultDetailsDialog(
        "antiga.pdf",
        ConversionDetails(),
        "21 validações com divergência",
    )
    qtbot.addWidget(dialog)

    assert dialog._validations_table.rowCount() == 0
    assert dialog._issues_table.rowCount() == 0
