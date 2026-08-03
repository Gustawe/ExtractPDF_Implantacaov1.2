from __future__ import annotations

from folha_pdf_xlsx.extractor import PdfLine, PayrollPdfExtractor


def _line(text: str) -> PdfLine:
    return PdfLine(
        top=0.0,
        words=[
            {"text": token, "x0": float(index)}
            for index, token in enumerate(text.split())
        ],
    )


def test_fiscal_page_without_federal_assessment_section_is_detected() -> None:
    pages = [
        [_line("EXTRATO MENSAL")],
        [
            _line("INSS FGTS, PIS e ISS"),
            _line("IRRF conforme competência do cálculo"),
            _line("Situações"),
        ],
    ]

    assert PayrollPdfExtractor._find_fiscal_page(pages) == 1


def test_unrelated_page_is_not_treated_as_fiscal_summary() -> None:
    pages = [[_line("EXTRATO MENSAL"), _line("Resumo por Rubrica")]]

    assert PayrollPdfExtractor._find_fiscal_page(pages) is None
