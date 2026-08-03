from __future__ import annotations

from pathlib import Path

from folha_pdf_xlsx.batch import process_pdf
from folha_pdf_xlsx.layout_models import PayrollLayoutDocument
from folha_pdf_xlsx.layout_writer import write_layout_workbook
from folha_pdf_xlsx.models import ConversionDetails, PayrollDocument
from folha_pdf_xlsx.writer import write_workbook


class PayrollEngineAdapter:
    """Expõe uma API pequena e estável para o restante da aplicação."""

    def convert(
        self, source_path: Path, output_path: Path
    ) -> tuple[str, str, ConversionDetails]:
        document = process_pdf(source_path)
        if isinstance(document, PayrollDocument):
            status = document.status
        else:
            status = self._details_status(document.details)
        message = self._details_message(status, document.details)
        if status == "ERRO":
            return status, message, document.details

        if isinstance(document, PayrollLayoutDocument) or document.employees:
            write_layout_workbook(document, output_path)
        else:
            write_workbook([document], output_path)
        return status, message, document.details

    @staticmethod
    def _details_message(status: str, details: ConversionDetails) -> str:
        if status == "APROVADO":
            return ""
        parts: list[str] = []
        if details.divergence_count:
            parts.append(f"{details.divergence_count} divergência(s)")
        if details.warning_count:
            parts.append(f"{details.warning_count} aviso(s)")
        if details.error_count:
            parts.append(f"{details.error_count} erro(s)")
        return "; ".join(parts) or status

    @staticmethod
    def _details_status(details: ConversionDetails) -> str:
        if details.error_count:
            return "ERRO"
        if details.divergence_count:
            return "APROVADO COM DIVERGÊNCIAS"
        if details.warning_count:
            return "APROVADO COM AVISOS"
        return "APROVADO"
