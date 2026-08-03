from __future__ import annotations

from pathlib import Path

import pytest

from conversor_folhas.application.conversion_service import ConversionService
from conversor_folhas.application.models import HistoryEntry
from conversor_folhas.application.conversion_service import ConversionFailedError
from folha_pdf_xlsx.models import ConversionDetails, ProcessingIssue


class SuccessfulEngine:
    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]:
        output_path.write_bytes(b"xlsx-gerado")
        return "APROVADO", ""


class FailingEngine:
    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]:
        output_path.write_bytes(b"incompleto")
        raise ValueError("layout não reconhecido")


class InvalidResultEngine:
    def convert(self, source_path: Path, output_path: Path):
        output_path.write_bytes(b"xlsx-invalido")
        details = ConversionDetails(
            issues=[
                ProcessingIssue(
                    source_file=source_path.name,
                    severity="ERRO",
                    code="SEM_FUNCIONARIOS",
                    message="Nenhum funcionário reconhecido.",
                )
            ]
        )
        return "ERRO", "1 erro(s)", details


class CollectingHistory:
    def __init__(self) -> None:
        self.entries: list[HistoryEntry] = []

    def record(self, entry: HistoryEntry) -> None:
        self.entries.append(entry)


class BrokenHistory:
    def record(self, entry: HistoryEntry) -> None:
        raise OSError("banco indisponível")


def test_conversion_is_saved_beside_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    service = ConversionService(SuccessfulEngine())

    result = service.convert(pdf)

    assert result.output_path == tmp_path / "folha.xlsx"
    assert result.output_path.read_bytes() == b"xlsx-gerado"
    assert not list(tmp_path.glob(".*.temporario.xlsx"))


def test_existing_outputs_receive_sequential_names(tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    (tmp_path / "folha.xlsx").write_bytes(b"existente")
    (tmp_path / "folha (1).xlsx").write_bytes(b"existente")
    service = ConversionService(SuccessfulEngine())

    result = service.convert(pdf)

    assert result.output_path == tmp_path / "folha (2).xlsx"
    assert (tmp_path / "folha.xlsx").read_bytes() == b"existente"
    assert (tmp_path / "folha (1).xlsx").read_bytes() == b"existente"


def test_temporary_file_is_removed_after_engine_failure(tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    service = ConversionService(FailingEngine())

    with pytest.raises(ValueError, match="layout não reconhecido"):
        service.convert(pdf)

    assert not list(tmp_path.glob(".*.temporario.xlsx"))
    assert not (tmp_path / "folha.xlsx").exists()


def test_non_pdf_is_rejected(tmp_path: Path) -> None:
    text_file = tmp_path / "folha.txt"
    text_file.write_text("não é pdf", encoding="utf-8")
    service = ConversionService(SuccessfulEngine())

    with pytest.raises(ValueError, match="não é um PDF"):
        service.convert(text_file)


def test_success_and_failure_are_recorded_in_history(tmp_path: Path) -> None:
    successful_pdf = tmp_path / "sucesso.pdf"
    failed_pdf = tmp_path / "falha.pdf"
    successful_pdf.write_bytes(b"%PDF-1.4")
    failed_pdf.write_bytes(b"%PDF-1.4")
    history = CollectingHistory()

    ConversionService(SuccessfulEngine(), history).convert(successful_pdf)
    with pytest.raises(ValueError):
        ConversionService(FailingEngine(), history).convert(failed_pdf)

    assert len(history.entries) == 2
    assert history.entries[0].status == "APROVADO"
    assert history.entries[0].output_path == tmp_path / "sucesso.xlsx"
    assert history.entries[1].status == "ERRO"
    assert history.entries[1].output_path is None
    assert "layout não reconhecido" in history.entries[1].message


def test_history_failure_does_not_invalidate_conversion(tmp_path: Path) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    result = ConversionService(SuccessfulEngine(), BrokenHistory()).convert(pdf)

    assert result.output_path.is_file()


def test_engine_error_is_not_published_and_keeps_structured_history(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "folha.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    history = CollectingHistory()

    with pytest.raises(ConversionFailedError, match="1 erro"):
        ConversionService(InvalidResultEngine(), history).convert(pdf)

    assert not (tmp_path / "folha.xlsx").exists()
    assert not list(tmp_path.glob(".*.temporario.xlsx"))
    assert history.entries[0].status == "ERRO"
    assert history.entries[0].details.error_count == 1
