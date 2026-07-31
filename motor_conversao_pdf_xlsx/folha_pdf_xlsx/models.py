from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


ZERO = Decimal("0.00")


@dataclass(slots=True)
class DocumentMetadata:
    source_file: str
    company_code: str = ""
    company_name: str = ""
    cnpj: str = ""
    calculation: str = ""
    competence: str = ""
    calculation_complement: str = ""
    issued_at: date | None = None
    page_count: int = 0
    layout_profile: str = "extrato_mensal_v1"


@dataclass(slots=True)
class PayrollEvent:
    source_file: str
    page: int
    employee_key: str
    registration: str
    code: str
    description: str
    reference: str
    value: Decimal
    kind: str
    raw_text: str = ""


@dataclass(slots=True)
class EmployeeRecord:
    source_file: str
    page: int
    employee_key: str
    record_type: str
    registration: str
    name: str
    status: str = ""
    cpf: str = ""
    admission_date: date | None = None
    employment_type: str = ""
    cost_center: str = ""
    department: str = ""
    monthly_hours: str = ""
    job_code: str = ""
    job_title: str = ""
    cbo: str = ""
    branch: str = ""
    salary: Decimal = ZERO
    dependents: int | None = None
    family_dependents: int | None = None
    total_earnings: Decimal = ZERO
    total_discounts: Decimal = ZERO
    informational: Decimal = ZERO
    informational_deduction: Decimal = ZERO
    net_amount: Decimal = ZERO
    inss_base: Decimal = ZERO
    inss_excess: Decimal = ZERO
    fgts_base: Decimal = ZERO
    fgts_value: Decimal = ZERO
    irrf_base: Decimal = ZERO
    observations: str = ""
    raw_text: str = ""
    events: list[PayrollEvent] = field(default_factory=list)


@dataclass(slots=True)
class DepartmentSummary:
    source_file: str
    page: int
    department: str
    description: str
    earnings: Decimal
    discounts: Decimal
    net_amount: Decimal
    raw_text: str = ""


@dataclass(slots=True)
class RubricSummary:
    source_file: str
    page: int
    code: str
    description: str
    reference: str
    value: Decimal
    kind: str
    raw_text: str = ""


@dataclass(slots=True)
class FiscalRecord:
    source_file: str
    page: int
    section: str
    subgroup: str
    item: str
    value: Decimal | None
    raw_text: str = ""


@dataclass(slots=True)
class ProcessingIssue:
    source_file: str
    severity: str
    code: str
    message: str
    page: int | None = None
    employee_key: str = ""
    raw_text: str = ""


@dataclass(slots=True)
class ValidationCheck:
    source_file: str
    scope: str
    record_key: str
    check: str
    expected: Decimal | int | str | None
    actual: Decimal | int | str | None
    difference: Decimal | None
    status: str
    message: str = ""


@dataclass(slots=True)
class PayrollDocument:
    source_path: Path
    metadata: DocumentMetadata
    employees: list[EmployeeRecord] = field(default_factory=list)
    departments: list[DepartmentSummary] = field(default_factory=list)
    rubrics: list[RubricSummary] = field(default_factory=list)
    fiscal_records: list[FiscalRecord] = field(default_factory=list)
    issues: list[ProcessingIssue] = field(default_factory=list)
    validations: list[ValidationCheck] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.now)

    @property
    def events(self) -> list[PayrollEvent]:
        return [event for employee in self.employees for event in employee.events]

    @property
    def status(self) -> str:
        if any(issue.severity == "ERRO" for issue in self.issues):
            return "REPROVADO"
        if any(check.status == "FALHA" for check in self.validations):
            return "REPROVADO"
        if self.issues or any(check.status == "AVISO" for check in self.validations):
            return "APROVADO COM AVISOS"
        return "APROVADO"

