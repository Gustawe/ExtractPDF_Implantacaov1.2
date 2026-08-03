from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping


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
    employee_name: str = ""
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "page": self.page,
            "employee_key": self.employee_key,
            "employee_name": self.employee_name,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessingIssue:
        page = data.get("page")
        return cls(
            source_file=str(data.get("source_file", "")),
            severity=str(data.get("severity", "INFORMAÇÃO")),
            code=str(data.get("code", "")),
            message=str(data.get("message", "")),
            page=int(page) if page not in (None, "") else None,
            employee_key=str(data.get("employee_key", "")),
            employee_name=str(data.get("employee_name", "")),
        )


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
    page: int | None = None
    employee_id: str = ""
    employee_name: str = ""
    target_cell: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "page": self.page,
            "scope": self.scope,
            "record_key": self.record_key,
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "check": self.check,
            "expected": _json_value(self.expected),
            "actual": _json_value(self.actual),
            "difference": _json_value(self.difference),
            "status": self.status,
            "message": self.message,
            "target_cell": self.target_cell,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ValidationCheck:
        page = data.get("page")
        return cls(
            source_file=str(data.get("source_file", "")),
            page=int(page) if page not in (None, "") else None,
            scope=str(data.get("scope", "DOCUMENTO")),
            record_key=str(data.get("record_key", "")),
            employee_id=str(data.get("employee_id", "")),
            employee_name=str(data.get("employee_name", "")),
            check=str(data.get("check", "")),
            expected=_restore_value(data.get("expected")),
            actual=_restore_value(data.get("actual")),
            difference=_restore_decimal(data.get("difference")),
            status=str(data.get("status", "OK")),
            message=str(data.get("message", "")),
            target_cell=str(data.get("target_cell", "")),
        )


@dataclass(slots=True)
class ConversionDetails:
    """Resultado auditável compartilhado pelo motor, aplicação e interface."""

    validations: list[ValidationCheck] = field(default_factory=list)
    issues: list[ProcessingIssue] = field(default_factory=list)
    schema_version: int = 1

    @property
    def has_details(self) -> bool:
        return bool(self.validations or self.issues)

    @property
    def divergence_count(self) -> int:
        return sum(
            check.status in {"DIVERGÊNCIA", "FALHA"}
            for check in self.validations
        )

    @property
    def warning_count(self) -> int:
        return sum(check.status == "AVISO" for check in self.validations) + sum(
            issue.severity in {"AVISO", "INFORMAÇÃO"} for issue in self.issues
        )

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "ERRO" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "validations": [check.to_dict() for check in self.validations],
            "issues": [issue.to_dict() for issue in self.issues],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> ConversionDetails:
        if not data:
            return cls()
        validations = data.get("validations", [])
        issues = data.get("issues", [])
        return cls(
            validations=[
                ValidationCheck.from_dict(item)
                for item in validations
                if isinstance(item, Mapping)
            ],
            issues=[
                ProcessingIssue.from_dict(item)
                for item in issues
                if isinstance(item, Mapping)
            ],
            schema_version=int(data.get("schema_version", 1)),
        )


def _json_value(value: Decimal | int | str | None) -> int | str | None:
    return str(value) if isinstance(value, Decimal) else value


def _restore_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError):
        return None


def _restore_value(value: Any) -> Decimal | int | str | None:
    if value is None or isinstance(value, int):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except ArithmeticError:
            return value
    return str(value)


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
    def details(self) -> ConversionDetails:
        return ConversionDetails(self.validations, self.issues)

    @property
    def status(self) -> str:
        if any(issue.severity == "ERRO" for issue in self.issues):
            return "ERRO"
        if any(
            check.status in {"DIVERGÊNCIA", "FALHA"}
            for check in self.validations
        ):
            return "APROVADO COM DIVERGÊNCIAS"
        if any(
            issue.severity in {"AVISO", "INFORMAÇÃO"} for issue in self.issues
        ) or any(check.status == "AVISO" for check in self.validations):
            return "APROVADO COM AVISOS"
        return "APROVADO"

