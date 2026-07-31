from __future__ import annotations

from pathlib import Path

import pytest

from conversor_folhas.application.conversion_service import ConversionService


class SuccessfulEngine:
    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]:
        output_path.write_bytes(b"xlsx-gerado")
        return "APROVADO", ""


class FailingEngine:
    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]:
        output_path.write_bytes(b"incompleto")
        raise ValueError("layout não reconhecido")


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

