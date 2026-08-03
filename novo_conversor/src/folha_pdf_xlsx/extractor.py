from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import pdfplumber

from .models import (
    DepartmentSummary,
    DocumentMetadata,
    EmployeeRecord,
    FiscalRecord,
    PayrollDocument,
    PayrollEvent,
    ProcessingIssue,
    RubricSummary,
    ZERO,
)
from .parsing import (
    clean_label_artifacts,
    parse_br_date,
    parse_br_decimal,
    parse_br_number,
    words_text,
)


LOGGER = logging.getLogger(__name__)
LAYOUT_PROFILE = "extrato_mensal_v1"
LINE_TOLERANCE = 2.1


def _normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )


@dataclass(slots=True)
class PdfLine:
    top: float
    words: list[dict[str, Any]]

    @property
    def text(self) -> str:
        return words_text(self.words)

    def between(self, start: float, end: float) -> list[dict[str, Any]]:
        return [word for word in self.words if start <= float(word["x0"]) < end]

    def after(self, start: float) -> list[dict[str, Any]]:
        return [word for word in self.words if float(word["x0"]) >= start]


class UnsupportedLayoutError(ValueError):
    """Raised when no known PDF profile can process a document."""


class PayrollPdfExtractor:
    """Extracts the coordinate-based EXTRATO MENSAL payroll layout."""

    def can_parse(self, pdf_path: str | Path) -> bool:
        path = Path(pdf_path)
        with pdfplumber.open(path) as pdf:
            sample = "\n".join((page.extract_text() or "") for page in pdf.pages[:2])
        return "EXTRATO MENSAL" in sample and ("Empr.:" in sample or "Contr:" in sample)

    def extract(self, pdf_path: str | Path) -> PayrollDocument:
        path = Path(pdf_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"PDF não encontrado: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Arquivo não é PDF: {path}")
        if not self.can_parse(path):
            raise UnsupportedLayoutError(
                "Layout não reconhecido. Esperado relatório 'EXTRATO MENSAL'."
            )

        LOGGER.info("Iniciando extração: %s", path.name)
        with pdfplumber.open(path) as pdf:
            lines_by_page = [
                self._group_lines(
                    page.extract_words(
                        x_tolerance=1,
                        y_tolerance=2,
                        keep_blank_chars=False,
                    )
                )
                for page in pdf.pages
            ]
            metadata = self._parse_metadata(path, lines_by_page[0], len(pdf.pages))
            document = PayrollDocument(source_path=path, metadata=metadata)

            for page_number, lines in enumerate(lines_by_page, start=1):
                document.employees.extend(
                    self._parse_employee_blocks(path.name, page_number, lines)
                )

            page_11_index = self._find_page_with(lines_by_page, "Resumo por Rubrica")
            if page_11_index is not None:
                summary_lines = lines_by_page[page_11_index]
                document.departments.extend(
                    self._parse_departments(path.name, page_11_index + 1, summary_lines)
                )
                document.rubrics.extend(
                    self._parse_rubrics(path.name, page_11_index + 1, summary_lines)
                )

            fiscal_page_index = self._find_fiscal_page(lines_by_page)
            if fiscal_page_index is not None:
                document.fiscal_records.extend(
                    self._parse_fiscal_records(
                        path.name,
                        fiscal_page_index + 1,
                        lines_by_page[fiscal_page_index],
                    )
                )
            else:
                document.issues.append(
                    ProcessingIssue(
                        source_file=path.name,
                        severity="AVISO",
                        code="RESUMO_FISCAL_AUSENTE",
                        message="Página de resumo fiscal não encontrada.",
                    )
                )

        if not document.employees:
            document.issues.append(
                ProcessingIssue(
                    source_file=path.name,
                    severity="ERRO",
                    code="SEM_FUNCIONARIOS",
                    message="Nenhum bloco de empregado ou contribuinte foi reconhecido.",
                )
            )
        LOGGER.info(
            "Extração concluída: %s registros, %s verbas",
            len(document.employees),
            len(document.events),
        )
        return document

    @staticmethod
    def _group_lines(words: Iterable[dict[str, Any]]) -> list[PdfLine]:
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
            PdfLine(
                top=sum(float(item["top"]) for item in cluster) / len(cluster),
                words=sorted(cluster, key=lambda item: float(item["x0"])),
            )
            for cluster in clusters
        ]

    @staticmethod
    def _find_page_with(
        lines_by_page: list[list[PdfLine]], search_text: str
    ) -> int | None:
        normalized = search_text.casefold()
        for index, lines in enumerate(lines_by_page):
            if any(normalized in line.text.casefold() for line in lines):
                return index
        return None

    @staticmethod
    def _find_fiscal_page(lines_by_page: list[list[PdfLine]]) -> int | None:
        """Localiza resumos fiscais completos, mesmo sem a seção de apuração."""

        required_markers = (
            "inss",
            "fgts, pis e iss",
            "irrf conforme competencia do calculo",
            "situacoes",
        )
        for index, lines in enumerate(lines_by_page):
            page_text = _normalized_text("\n".join(line.text for line in lines))
            if "apuracao tributos federais" in page_text:
                return index
            if sum(marker in page_text for marker in required_markers) >= 3:
                return index
        return None

    def _parse_metadata(
        self, path: Path, lines: list[PdfLine], page_count: int
    ) -> DocumentMetadata:
        company_line = self._line_starting(lines, "Empresa:")
        company_parts = words_text(company_line.between(110, 495)).split()
        company_code = company_parts[0] if company_parts else ""
        company_name = " ".join(
            part for part in company_parts[1:] if part != "-"
        ).strip()

        cnpj_line = self._line_starting(lines, "CNPJ:")
        calculation_line = self._line_starting(lines, "Cálculo:")
        competence_line = self._line_starting(lines, "Competência:")
        complement_line = next(
            (line for line in lines if line.text.startswith("Complemento de cálculo:")),
            None,
        )
        issue_line = self._line_containing(lines, "Emissão:")

        return DocumentMetadata(
            source_file=path.name,
            company_code=company_code,
            company_name=company_name,
            cnpj=words_text(cnpj_line.between(110, 495)),
            calculation=words_text(calculation_line.between(110, 495)),
            competence=words_text(competence_line.between(110, 495)),
            calculation_complement=(
                words_text(complement_line.between(110, 495)) if complement_line else ""
            ),
            issued_at=parse_br_date(words_text(issue_line.after(525))),
            page_count=page_count,
            layout_profile=LAYOUT_PROFILE,
        )

    @staticmethod
    def _line_starting(lines: list[PdfLine], prefix: str) -> PdfLine:
        for line in lines:
            if line.text.startswith(prefix):
                return line
        return PdfLine(0.0, [])

    @staticmethod
    def _line_containing(lines: list[PdfLine], text: str) -> PdfLine:
        for line in lines:
            if text in line.text:
                return line
        return PdfLine(0.0, [])

    def _parse_employee_blocks(
        self, source_file: str, page_number: int, lines: list[PdfLine]
    ) -> list[EmployeeRecord]:
        starts = [
            index
            for index, line in enumerate(lines)
            if line.text.startswith("Empr.:") or line.text.startswith("Contr:")
        ]
        employees: list[EmployeeRecord] = []
        for position, start_index in enumerate(starts):
            next_index = starts[position + 1] if position + 1 < len(starts) else len(lines)
            end_index = self._employee_section_end(lines, start_index, next_index)
            block = lines[start_index:end_index]
            if len(block) < 3:
                continue
            employees.append(
                self._parse_employee(source_file, page_number, position + 1, block)
            )
        return employees

    @staticmethod
    def _employee_section_end(
        lines: list[PdfLine], start_index: int, default_end: int
    ) -> int:
        stop_markers = (
            "Totais por Departamento",
            "Resumo por Rubrica",
            "INSS FGTS, PIS e ISS",
        )
        for index in range(start_index + 1, default_end):
            if any(marker in lines[index].text for marker in stop_markers):
                return index
        return default_end

    def _parse_employee(
        self,
        source_file: str,
        page_number: int,
        block_sequence: int,
        block: list[PdfLine],
    ) -> EmployeeRecord:
        header, employment, job = block[0:3]
        record_type = "CONTRIBUINTE" if header.text.startswith("Contr:") else "EMPREGADO"

        identity_words = header.between(60, 250)
        identity_text = clean_label_artifacts(words_text(identity_words))
        identity_parts = identity_text.split()
        registration = identity_parts[0] if identity_parts else ""
        name = " ".join(identity_parts[1:]).strip()

        employee_key = (
            f"{source_file}|{page_number}|{record_type}|{registration}|{block_sequence}"
        )
        employee = EmployeeRecord(
            source_file=source_file,
            page=page_number,
            employee_key=employee_key,
            record_type=record_type,
            registration=registration,
            name=name,
            status=clean_label_artifacts(words_text(header.between(250, 365))),
            cpf=clean_label_artifacts(words_text(header.between(380, 478))),
            admission_date=parse_br_date(words_text(header.after(520))),
            employment_type=words_text(employment.between(60, 230)),
            cost_center=words_text(employment.between(250, 350)),
            department=words_text(employment.between(380, 455)),
            monthly_hours=words_text(employment.after(520)),
            job_code=words_text(job.between(60, 78)),
            job_title=clean_label_artifacts(words_text(job.between(78, 229))),
            cbo=clean_label_artifacts(words_text(job.between(250, 350))),
            branch=clean_label_artifacts(words_text(job.between(380, 460))),
            salary=parse_br_decimal(words_text(job.after(520))) or ZERO,
            raw_text="\n".join(line.text for line in block),
        )

        summary_index = next(
            (index for index, line in enumerate(block) if line.text.startswith("ND:")),
            len(block),
        )
        for line in block[3:summary_index]:
            left_event = self._parse_event_half(
                source_file,
                page_number,
                employee_key,
                registration,
                line,
                kind="P",
            )
            right_event = self._parse_event_half(
                source_file,
                page_number,
                employee_key,
                registration,
                line,
                kind="D",
            )
            if left_event:
                employee.events.append(left_event)
            if right_event:
                employee.events.append(right_event)

        if summary_index < len(block):
            self._parse_employee_totals(employee, block[summary_index])
        nf_index = next(
            (
                index
                for index, line in enumerate(block[summary_index + 1 :], summary_index + 1)
                if line.text.startswith("NF:")
            ),
            None,
        )
        if nf_index is not None:
            self._parse_employee_bases(employee, block[nf_index])
            observations = [
                line.text
                for line in block[nf_index + 1 :]
                if line.top < 800
                and not line.text.startswith(("Empresa:", "CNPJ:", "Cálculo:"))
            ]
            employee.observations = " | ".join(observations)
        return employee

    @staticmethod
    def _parse_event_half(
        source_file: str,
        page_number: int,
        employee_key: str,
        registration: str,
        line: PdfLine,
        kind: str,
    ) -> PayrollEvent | None:
        if kind == "P":
            code_words = line.between(25, 50)
            description_words = line.between(50, 190)
            reference_words = line.between(190, 250)
            value_words = line.between(245, 275)
            type_words = line.between(275, 300)
        else:
            code_words = line.between(300, 329)
            description_words = line.between(329, 470)
            reference_words = line.between(470, 529)
            value_words = line.between(529, 562)
            type_words = line.after(562)

        type_text = words_text(type_words).strip()
        if type_text != kind:
            return None
        code = words_text(code_words).strip()
        value = parse_br_decimal(words_text(value_words))
        if not code or value is None:
            return None
        return PayrollEvent(
            source_file=source_file,
            page=page_number,
            employee_key=employee_key,
            registration=registration,
            code=code,
            description=words_text(description_words).strip(),
            reference=words_text(reference_words).strip(),
            value=value,
            kind=kind,
            raw_text=line.text,
        )

    @staticmethod
    def _number_at(line: PdfLine, start: float, end: float) -> Decimal:
        return parse_br_decimal(words_text(line.between(start, end))) or ZERO

    def _parse_employee_totals(
        self, employee: EmployeeRecord, line: PdfLine
    ) -> None:
        employee.dependents = self._integer_at(line, 35, 50)
        employee.total_earnings = self._number_at(line, 105, 160)
        employee.total_discounts = self._number_at(line, 215, 250)
        employee.informational = self._number_at(line, 315, 365)
        employee.informational_deduction = self._number_at(line, 450, 485)
        employee.net_amount = self._number_at(line, 525, 590)

    def _parse_employee_bases(
        self, employee: EmployeeRecord, line: PdfLine
    ) -> None:
        employee.family_dependents = self._integer_at(line, 35, 48)
        employee.inss_base = self._number_at(line, 105, 145)
        employee.inss_excess = self._number_at(line, 220, 255)
        employee.fgts_base = self._number_at(line, 310, 365)
        employee.fgts_value = self._number_at(line, 435, 485)
        employee.irrf_base = self._number_at(line, 535, 590)

    @staticmethod
    def _integer_at(line: PdfLine, start: float, end: float) -> int | None:
        value = words_text(line.between(start, end)).strip()
        return int(value) if value.isdigit() else None

    def _parse_departments(
        self, source_file: str, page_number: int, lines: list[PdfLine]
    ) -> list[DepartmentSummary]:
        heading_index = next(
            (i for i, line in enumerate(lines) if "Totais por Departamento" in line.text),
            None,
        )
        if heading_index is None:
            return []
        results: list[DepartmentSummary] = []
        for line in lines[heading_index + 1 :]:
            if "Total Geral Proventos" in line.text or "Resumo por Rubrica" in line.text:
                break
            earnings = self._number_at(line, 210, 330)
            discounts = self._number_at(line, 330, 455)
            net_amount = self._number_at(line, 455, 590)
            left = words_text(line.between(15, 210)).strip()
            if not left or (earnings == ZERO and discounts == ZERO and net_amount == ZERO):
                continue
            if left.startswith("Total:"):
                continue
            parts = left.split(maxsplit=1)
            results.append(
                DepartmentSummary(
                    source_file=source_file,
                    page=page_number,
                    department=parts[0],
                    description=parts[1] if len(parts) > 1 else "",
                    earnings=earnings,
                    discounts=discounts,
                    net_amount=net_amount,
                    raw_text=line.text,
                )
            )
        return results

    def _parse_rubrics(
        self, source_file: str, page_number: int, lines: list[PdfLine]
    ) -> list[RubricSummary]:
        heading_index = next(
            (i for i, line in enumerate(lines) if "Resumo por Rubrica" in line.text),
            None,
        )
        if heading_index is None:
            return []
        rubrics: list[RubricSummary] = []
        for line in lines[heading_index + 1 :]:
            if "Líquido Geral:" in line.text:
                break
            for kind in ("P", "D"):
                event = self._parse_event_half(
                    source_file,
                    page_number,
                    "RESUMO_RUBRICA",
                    "",
                    line,
                    kind,
                )
                if event:
                    rubrics.append(
                        RubricSummary(
                            source_file=source_file,
                            page=page_number,
                            code=event.code,
                            description=event.description,
                            reference=event.reference,
                            value=event.value,
                            kind=event.kind,
                            raw_text=event.raw_text,
                        )
                    )
        return rubrics

    def _parse_fiscal_records(
        self, source_file: str, page_number: int, lines: list[PdfLine]
    ) -> list[FiscalRecord]:
        records: list[FiscalRecord] = []
        section = ""
        heading_map = {
            "INSS FGTS, PIS e ISS": "INSS / FGTS / PIS / ISS",
            "IRRF conforme competência do cálculo": "IRRF",
            "Situações": "Situações",
            "Apuração Tributos Federais": "Apuração Tributos Federais",
        }
        for line in lines:
            for marker, mapped_section in heading_map.items():
                if marker in line.text:
                    section = mapped_section
                    break
            if not section or line.top >= 800:
                continue
            if section == "INSS / FGTS / PIS / ISS" and 124 <= line.top <= 270:
                records.extend(
                    self._parse_two_column_fiscal_line(
                        source_file, page_number, section, line, 14, 298, 298, 590
                    )
                )
            elif section == "IRRF" and 290 <= line.top <= 425:
                records.extend(
                    self._parse_two_column_fiscal_line(
                        source_file, page_number, section, line, 14, 298, 298, 590
                    )
                )
            elif section == "Situações" and 455 <= line.top <= 570:
                records.extend(
                    self._parse_two_column_fiscal_line(
                        source_file, page_number, section, line, 14, 298, 298, 590
                    )
                )
            elif (
                section == "Apuração Tributos Federais"
                and "Saldo à recolher:" in line.text
            ):
                value = parse_br_decimal(words_text(line.after(520)))
                if value is not None:
                    records.append(
                        FiscalRecord(
                            source_file=source_file,
                            page=page_number,
                            section=section,
                            subgroup="TOTAL",
                            item="Saldo à recolher",
                            value=value,
                            raw_text=line.text,
                        )
                    )
            elif section == "Apuração Tributos Federais" and 640 <= line.top <= 705:
                records.extend(
                    self._parse_apuracao_line(source_file, page_number, section, line)
                )
            elif section == "Apuração Tributos Federais" and 600 <= line.top < 640:
                records.extend(
                    self._parse_two_column_fiscal_line(
                        source_file,
                        page_number,
                        section,
                        line,
                        14,
                        250,
                        250,
                        590,
                        subgroup_names=("Saldo a compensar", "Saldo a compensar"),
                    )
                )
            elif section == "Apuração Tributos Federais" and 710 <= line.top <= 738:
                records.extend(
                    self._parse_two_column_fiscal_line(
                        source_file,
                        page_number,
                        section,
                        line,
                        14,
                        250,
                        250,
                        590,
                        subgroup_names=(
                            "Saldo remanescente a restituir",
                            "Saldo remanescente a restituir",
                        ),
                    )
                )
            elif section == "Apuração Tributos Federais" and 740 <= line.top < 800:
                records.append(
                    FiscalRecord(
                        source_file=source_file,
                        page=page_number,
                        section=section,
                        subgroup="OBSERVAÇÃO",
                        item="Aviso",
                        value=None,
                        raw_text=line.text,
                    )
                )
        return records

    @staticmethod
    def _parse_two_column_fiscal_line(
        source_file: str,
        page_number: int,
        section: str,
        line: PdfLine,
        left_start: float,
        left_end: float,
        right_start: float,
        right_end: float,
        subgroup_names: tuple[str, str] = ("ESQUERDA", "DIREITA"),
    ) -> list[FiscalRecord]:
        results: list[FiscalRecord] = []
        for subgroup, start, end in (
            (subgroup_names[0], left_start, left_end),
            (subgroup_names[1], right_start, right_end),
        ):
            words = line.between(start, end)
            if not words:
                continue
            numeric_words = [
                word for word in words if parse_br_number(str(word["text"])) is not None
            ]
            if not numeric_words:
                continue
            value_word = numeric_words[-1]
            label_words = [
                word for word in words if float(word["x0"]) < float(value_word["x0"])
            ]
            label = words_text(label_words).strip()
            value = parse_br_number(str(value_word["text"]))
            if label and value is not None:
                results.append(
                    FiscalRecord(
                        source_file=source_file,
                        page=page_number,
                        section=section,
                        subgroup=subgroup,
                        item=label,
                        value=value,
                        raw_text=line.text,
                    )
                )
        return results

    @staticmethod
    def _parse_apuracao_line(
        source_file: str, page_number: int, section: str, line: PdfLine
    ) -> list[FiscalRecord]:
        label = words_text(line.between(14, 150)).strip()
        if not label:
            return []
        columns = (
            ("Valor", 150, 190),
            ("Compensação DCOMP", 250, 285),
            ("Salário Família", 325, 355),
            ("Salário Maternidade", 410, 440),
            ("Retenções", 470, 495),
            ("Saldo a recolher", 535, 590),
        )
        results: list[FiscalRecord] = []
        for subgroup, start, end in columns:
            value = parse_br_decimal(words_text(line.between(start, end)))
            if value is None:
                continue
            results.append(
                FiscalRecord(
                    source_file=source_file,
                    page=page_number,
                    section=section,
                    subgroup=subgroup,
                    item=label,
                    value=value,
                    raw_text=line.text,
                )
            )
        return results
