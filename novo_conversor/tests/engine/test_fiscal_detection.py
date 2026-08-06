from __future__ import annotations

from decimal import Decimal

from folha_pdf_xlsx.extractor import PdfLine, PayrollPdfExtractor


def _line(text: str) -> PdfLine:
    return PdfLine(
        top=0.0,
        words=[
            {"text": token, "x0": float(index)}
            for index, token in enumerate(text.split())
        ],
    )


def _positioned_line(top: float, *words: tuple[str, float]) -> PdfLine:
    return PdfLine(
        top=top,
        words=[{"text": text, "x0": x0} for text, x0 in words],
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


def test_compact_fiscal_page_with_resumo_das_bases_is_detected() -> None:
    pages = [
        [_line("EXTRATO MENSAL")],
        [
            _line("Resumo das Bases"),
            _line("Situações"),
            _line("Base IRRF Mensal"),
            _line("Total INSS"),
            _line("Base do FGTS"),
        ],
    ]

    assert PayrollPdfExtractor._find_fiscal_page(pages) == 1


def test_compact_fiscal_records_are_parsed_by_semantic_column() -> None:
    lines = [
        _positioned_line(110.30, ("Resumo", 14.82), ("das", 42.0), ("Bases", 55.0)),
        _positioned_line(115.04, ("Situações", 57.72)),
        _positioned_line(
            136.08,
            ("Número", 14.82),
            ("de", 40.89),
            ("empregados:", 50.43),
            ("39", 155.88),
            ("Salário", 228.72),
            ("contribuição", 251.22),
            ("empregados:", 290.07),
            ("141.126,02", 375.66),
            ("Base", 416.16),
            ("IRRF", 432.61),
            ("Mensal:", 449.40),
            ("85.150,15", 541.80),
        ),
        _positioned_line(
            301.20,
            ("Total", 228.72),
            ("INSS:", 246.09),
            ("26.021,99", 379.38),
            ("Valor", 416.16),
            ("do", 433.75),
            ("FGTS", 443.40),
            ("Aprendiz:", 461.50),
            ("38,15", 555.06),
        ),
        _positioned_line(
            404.40,
            ("Líquido", 416.16),
            ("Geral:", 445.0),
            ("78.764,67", 541.80),
        ),
    ]

    records = PayrollPdfExtractor()._parse_fiscal_records("folha.pdf", 10, lines)
    index = {(item.section, item.subgroup, item.item): item.value for item in records}

    assert index[("Situações", "CONTAGEM", "Número de empregados:")] == Decimal("39")
    assert index[
        ("INSS / CONTRIBUIÇÕES", "BASES", "Salário contribuição empregados:")
    ] == Decimal("141126.02")
    assert index[("INSS / CONTRIBUIÇÕES", "BASES", "Total INSS:")] == Decimal(
        "26021.99"
    )
    assert index[
        ("IRRF / FGTS / PIS / ISS", "BASES", "Valor do FGTS Aprendiz:")
    ] == Decimal("38.15")
    assert index[("Resumo das Bases", "TOTAL", "Líquido Geral:")] == Decimal(
        "78764.67"
    )


def test_resumo_das_bases_without_financial_markers_is_not_enough() -> None:
    pages = [[_line("Resumo das Bases"), _line("Situações")]]

    assert PayrollPdfExtractor._find_fiscal_page(pages) is None
