from __future__ import annotations

import logging
from pathlib import Path

from .extractor import PayrollPdfExtractor
from .layout_extractor import SystemPayrollLayoutExtractor
from .layout_models import PayrollLayoutDocument
from .layout_writer import write_layout_workbook
from .models import (
    DocumentMetadata,
    PayrollDocument,
    ProcessingIssue,
)
from .validation import validate_document
from .writer import write_workbook


LOGGER = logging.getLogger(__name__)


def process_pdf(pdf_path: Path) -> PayrollDocument | PayrollLayoutDocument:
    layout_extractor = SystemPayrollLayoutExtractor()
    if layout_extractor.can_parse(pdf_path):
        return layout_extractor.extract(pdf_path)
    document = PayrollPdfExtractor().extract(pdf_path)
    document.validations = validate_document(document)
    return document


def _failed_document(pdf_path: Path, error: Exception) -> PayrollDocument:
    document = PayrollDocument(
        source_path=pdf_path,
        metadata=DocumentMetadata(source_file=pdf_path.name),
    )
    document.issues.append(
        ProcessingIssue(
            source_file=pdf_path.name,
            severity="ERRO",
            code="FALHA_PROCESSAMENTO",
            message=f"{type(error).__name__}: {error}",
        )
    )
    return document


def process_individual(
    pdf_paths: list[Path], output_directory: Path
) -> tuple[list[Path], int]:
    output_directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    failed_count = 0
    for pdf_path in pdf_paths:
        destination = output_directory / f"{pdf_path.stem}.xlsx"
        try:
            document = process_pdf(pdf_path)
        except Exception as error:
            LOGGER.exception("Falha no processamento de %s", pdf_path)
            document = _failed_document(pdf_path, error)
            failed_count += 1
        if isinstance(document, PayrollLayoutDocument) or document.employees:
            outputs.append(write_layout_workbook(document, destination))
        else:
            outputs.append(write_workbook([document], destination))
    return outputs, failed_count


def process_consolidated(
    pdf_paths: list[Path], output_path: Path
) -> tuple[Path, int]:
    documents: list[PayrollDocument] = []
    failed_count = 0
    for pdf_path in pdf_paths:
        try:
            document = process_pdf(pdf_path)
            if isinstance(document, PayrollLayoutDocument):
                raise ValueError(
                    "O perfil visual gera um XLSX por PDF e não aceita consolidação."
                )
            documents.append(document)
        except Exception as error:
            LOGGER.exception("Falha no processamento de %s", pdf_path)
            documents.append(_failed_document(pdf_path, error))
            failed_count += 1
    return write_workbook(documents, output_path), failed_count
