from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import pdfplumber

from .extractor import UnsupportedLayoutError
from .layout_models import (
    LayoutLine,
    LayoutWord,
    PayrollLayoutDocument,
    PayrollLayoutSection,
)


LINE_TOLERANCE = 2.1
TITLE_PREFIXES = (
    "Folha de Pagamento",
    "Folha de Pró-Labore",
    "Folha de Pro-Labore",
)


class SystemPayrollLayoutExtractor:
    """Extract the fixed payroll report used by the supplied 2023 PDF."""

    def can_parse(self, pdf_path: str | Path) -> bool:
        with pdfplumber.open(pdf_path) as pdf:
            sample = "\n".join((page.extract_text() or "") for page in pdf.pages[:2])
        return (
            "Apelido:" in sample
            and "Razão Social:" in sample
            and "CNPJ/CEI:" in sample
            and any(title in sample for title in TITLE_PREFIXES)
        )

    def extract(self, pdf_path: str | Path) -> PayrollLayoutDocument:
        path = Path(pdf_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"PDF não encontrado: {path}")
        if not self.can_parse(path):
            raise UnsupportedLayoutError("Layout de folha do sistema não reconhecido.")

        with pdfplumber.open(path) as pdf:
            document = PayrollLayoutDocument(source_path=path, page_count=len(pdf.pages))
            sections: dict[tuple[str, str, str], PayrollLayoutSection] = {}
            order: list[tuple[str, str, str]] = []

            for page_number, page in enumerate(pdf.pages, start=1):
                lines = self._group_lines(
                    page.extract_words(
                        x_tolerance=1,
                        y_tolerance=2,
                        keep_blank_chars=False,
                    ),
                    page_number,
                )
                header = self._parse_header(lines)
                key = (header.title, header.period_start, header.period_end)
                if key not in sections:
                    sections[key] = header
                    order.append(key)
                section = sections[key]
                section.source_pages.append(page_number)
                self._append_content(section, [line for line in lines if line.top >= 80])

            document.sections = [sections[key] for key in order]
            for section in document.sections:
                self._split_blocks(section)
            return document

    @staticmethod
    def _group_lines(
        words: Iterable[dict[str, Any]], page_number: int
    ) -> list[LayoutLine]:
        clusters: list[list[dict[str, Any]]] = []
        for word in sorted(words, key=lambda item: (float(item["top"]), float(item["x0"]))):
            top = float(word["top"])
            if not clusters:
                clusters.append([word])
                continue
            cluster_top = sum(float(item["top"]) for item in clusters[-1]) / len(
                clusters[-1]
            )
            if abs(top - cluster_top) <= LINE_TOLERANCE:
                clusters[-1].append(word)
            else:
                clusters.append([word])
        return [
            LayoutLine(
                page=page_number,
                top=sum(float(item["top"]) for item in cluster) / len(cluster),
                words=tuple(
                    LayoutWord(str(item["text"]), float(item["x0"]))
                    for item in sorted(cluster, key=lambda item: float(item["x0"]))
                ),
            )
            for cluster in clusters
        ]

    @staticmethod
    def _line(lines: list[LayoutLine], prefix: str) -> str:
        return next((line.text for line in lines if line.text.startswith(prefix)), "")

    def _parse_header(self, lines: list[LayoutLine]) -> PayrollLayoutSection:
        title = next(
            (line.text for line in lines if line.text.startswith(TITLE_PREFIXES)),
            "",
        )
        identity = self._line(lines, "Apelido:")
        tax = self._line(lines, "CNPJ/CEI:")
        address_line = self._line(lines, "Endereço:")

        nickname = self._capture(identity, r"Apelido:\s*(.*?)\s+Razão Social:")
        company = self._capture(identity, r"Razão Social:\s*(.*?)(?:\s+Pág:\d+)?$")
        cnpj = self._capture(tax, r"CNPJ/CEI:\s*(.*?)\s+Inscrição:")
        registration = self._capture(tax, r"Inscrição:\s*(.*?)\s+Período de:")
        period_start = self._capture(tax, r"Período de:\s*(\d{2}/\d{2}/\d{4})")
        period_end = self._capture(tax, r"\s+a\s+(\d{2}/\d{2}/\d{4})")
        address = self._capture(address_line, r"Endereço:\s*(.*?)\s+Bairro:")
        district = self._capture(address_line, r"Bairro:\s*(.*?)\s+Cidade:")
        city = self._capture(address_line, r"Cidade:\s*(.*?)\s+UF:")
        state = self._capture(address_line, r"UF:\s*(\S+)")
        return PayrollLayoutSection(
            title=title,
            nickname=nickname,
            company_name=company,
            cnpj=cnpj,
            registration=registration,
            period_start=period_start,
            period_end=period_end,
            address=address,
            district=district,
            city=city,
            state=state,
        )

    @staticmethod
    def _capture(text: str, pattern: str) -> str:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _append_content(
        section: PayrollLayoutSection, content: list[LayoutLine]
    ) -> None:
        # Temporarily use summary_lines as the ordered content buffer.
        section.summary_lines.extend(content)

    @staticmethod
    def _split_blocks(section: PayrollLayoutSection) -> None:
        content = section.summary_lines
        section.summary_lines = []
        current: list[LayoutLine] = []
        in_summary = False
        for line in content:
            if line.text.startswith("R E S U M O"):
                if current:
                    section.employee_blocks.append(current)
                    current = []
                in_summary = True
                section.summary_lines.append(line)
                continue
            if in_summary:
                section.summary_lines.append(line)
                continue
            if line.text.startswith("Cód:"):
                if current:
                    section.employee_blocks.append(current)
                current = [line]
            elif current:
                current.append(line)
            else:
                # A page may begin with the continuation of the last employee.
                if section.employee_blocks:
                    section.employee_blocks[-1].append(line)
        if current:
            section.employee_blocks.append(current)

