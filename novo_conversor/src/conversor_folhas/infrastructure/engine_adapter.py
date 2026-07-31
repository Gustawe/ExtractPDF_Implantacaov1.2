from __future__ import annotations

from pathlib import Path

from folha_pdf_xlsx.batch import process_pdf
from folha_pdf_xlsx.layout_models import PayrollLayoutDocument
from folha_pdf_xlsx.layout_writer import write_layout_workbook
from folha_pdf_xlsx.models import PayrollDocument
from folha_pdf_xlsx.writer import write_workbook


class PayrollEngineAdapter:
    """Expõe uma API pequena e estável para o restante da aplicação."""

    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]:
        document = process_pdf(source_path)
        if isinstance(document, PayrollLayoutDocument) or document.employees:
            write_layout_workbook(document, output_path)
        else:
            write_workbook([document], output_path)

        if isinstance(document, PayrollDocument):
            status = document.status
            message = self._document_message(document)
            return status, message
        return "APROVADO", ""

    @staticmethod
    def _document_message(document: PayrollDocument) -> str:
        if document.status == "APROVADO":
            return ""
        failed_checks = sum(
            1 for check in document.validations if check.status == "FALHA"
        )
        issues = len(document.issues)
        details: list[str] = []
        if failed_checks:
            details.append(f"{failed_checks} validação(ões) com divergência")
        if issues:
            details.append(f"{issues} ocorrência(s) registrada(s)")
        return "; ".join(details) or document.status

