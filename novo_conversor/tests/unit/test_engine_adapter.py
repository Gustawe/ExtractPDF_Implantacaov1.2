from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from conversor_folhas.infrastructure.engine_adapter import PayrollEngineAdapter
from folha_pdf_xlsx.layout_models import PayrollLayoutDocument


def test_layout_document_uses_approved_visual_writer(tmp_path: Path) -> None:
    source = tmp_path / "folha.pdf"
    output = tmp_path / "folha.xlsx"
    document = PayrollLayoutDocument(source_path=source, page_count=1)
    adapter = PayrollEngineAdapter()

    with (
        patch(
            "conversor_folhas.infrastructure.engine_adapter.process_pdf",
            return_value=document,
        ),
        patch(
            "conversor_folhas.infrastructure.engine_adapter.write_layout_workbook"
        ) as visual_writer,
        patch(
            "conversor_folhas.infrastructure.engine_adapter.write_workbook"
        ) as structured_writer,
    ):
        status, message, details = adapter.convert(source, output)

    visual_writer.assert_called_once_with(document, output)
    structured_writer.assert_not_called()
    assert status == "APROVADO"
    assert message == ""
    assert not details.has_details
