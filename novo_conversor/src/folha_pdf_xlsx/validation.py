from __future__ import annotations

import unicodedata
from decimal import Decimal

from .models import (
    PayrollDocument,
    ProcessingIssue,
    ValidationCheck,
    ZERO,
)


DEFAULT_TOLERANCE = Decimal("0.01")
NOT_APPLICABLE_MESSAGE = (
    "Validação não aplicável: este modelo de 13º não apresenta eventos detalhados."
)
MISSING_EVENTS_MESSAGE = (
    "Nenhum evento detalhado foi lido para este funcionário em um layout que "
    "normalmente apresenta eventos. Confira a extração."
)


def _status(difference: Decimal, tolerance: Decimal) -> str:
    return "OK" if abs(difference) <= tolerance else "DIVERGÊNCIA"


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def is_thirteenth_without_detailed_events(document: PayrollDocument) -> bool:
    """Reconhece somente o perfil conhecido de 13º sem linhas de eventos."""

    if document.metadata.layout_profile != "extrato_mensal_v1":
        return False
    if not document.employees or any(employee.events for employee in document.employees):
        return False

    evidence = _normalized(
        " ".join(
            (
                document.metadata.calculation,
                document.metadata.calculation_complement,
                document.metadata.competence,
            )
        )
    )
    thirteenth_markers = (
        "13º",
        "13°",
        "13o",
        "13 salario",
        "decimo terceiro",
    )
    installment_markers = (
        "1ª parcela",
        "1a parcela",
        "primeira parcela",
        "2ª parcela",
        "2a parcela",
        "segunda parcela",
        "parcela",
        "adiantamento",
    )
    return any(marker in evidence for marker in thirteenth_markers) and any(
        marker in evidence for marker in installment_markers
    )


def validate_document(
    document: PayrollDocument,
    tolerance: Decimal = DEFAULT_TOLERANCE,
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    thirteenth_without_events = is_thirteenth_without_detailed_events(document)

    for employee in document.employees:
        event_earnings = sum(
            (event.value for event in employee.events if event.kind == "P"), ZERO
        )
        event_discounts = sum(
            (event.value for event in employee.events if event.kind == "D"), ZERO
        )

        if not employee.events and thirteenth_without_events:
            checks.extend(
                _employee_event_checks(
                    employee,
                    event_earnings,
                    event_discounts,
                    status="NÃO APLICÁVEL",
                    message=NOT_APPLICABLE_MESSAGE,
                )
            )
        elif not employee.events:
            checks.extend(
                _employee_event_checks(
                    employee,
                    event_earnings,
                    event_discounts,
                    status="AVISO",
                    message=MISSING_EVENTS_MESSAGE,
                )
            )
            _append_missing_events_issue(document, employee)
        else:
            checks.extend(
                _employee_event_checks(
                    employee,
                    event_earnings,
                    event_discounts,
                    tolerance=tolerance,
                )
            )

        liquid_actual = employee.total_earnings - employee.total_discounts
        liquid_difference = liquid_actual - employee.net_amount
        checks.append(
            ValidationCheck(
                source_file=employee.source_file,
                page=employee.page,
                scope="FUNCIONÁRIO",
                record_key=employee.employee_key,
                employee_id=employee.registration,
                employee_name=employee.name,
                check="Cálculo do líquido",
                expected=employee.net_amount,
                actual=liquid_actual,
                difference=liquid_difference,
                status=_status(liquid_difference, tolerance),
            )
        )

    if document.departments:
        _append_document_total_checks(document, checks, tolerance)
    return checks


def _employee_event_checks(
    employee,
    event_earnings: Decimal,
    event_discounts: Decimal,
    *,
    status: str | None = None,
    message: str = "",
    tolerance: Decimal = DEFAULT_TOLERANCE,
) -> list[ValidationCheck]:
    results: list[ValidationCheck] = []
    for check_name, expected, actual in (
        ("Soma de proventos", employee.total_earnings, event_earnings),
        ("Soma de descontos", employee.total_discounts, event_discounts),
    ):
        difference = actual - expected
        results.append(
            ValidationCheck(
                source_file=employee.source_file,
                page=employee.page,
                scope="FUNCIONÁRIO",
                record_key=employee.employee_key,
                employee_id=employee.registration,
                employee_name=employee.name,
                check=check_name,
                expected=expected,
                actual=actual,
                difference=difference,
                status=status or _status(difference, tolerance),
                message=message,
            )
        )
    return results


def _append_missing_events_issue(document: PayrollDocument, employee) -> None:
    code = "EVENTOS_DETALHADOS_NAO_LIDOS"
    if any(
        issue.code == code and issue.employee_key == employee.employee_key
        for issue in document.issues
    ):
        return
    document.issues.append(
        ProcessingIssue(
            source_file=employee.source_file,
            page=employee.page,
            severity="AVISO",
            code=code,
            message=MISSING_EVENTS_MESSAGE,
            employee_key=employee.employee_key,
            employee_name=employee.name,
        )
    )


def _append_document_total_checks(
    document: PayrollDocument,
    checks: list[ValidationCheck],
    tolerance: Decimal,
) -> None:
    employee_earnings = sum(
        (employee.total_earnings for employee in document.employees), ZERO
    )
    employee_discounts = sum(
        (employee.total_discounts for employee in document.employees), ZERO
    )
    employee_net = sum((employee.net_amount for employee in document.employees), ZERO)
    department_earnings = sum((item.earnings for item in document.departments), ZERO)
    department_discounts = sum((item.discounts for item in document.departments), ZERO)
    department_net = sum((item.net_amount for item in document.departments), ZERO)
    page = document.departments[0].page if document.departments else None

    for check_name, expected, actual in (
        ("Total geral de proventos", department_earnings, employee_earnings),
        ("Total geral de descontos", department_discounts, employee_discounts),
        ("Total geral líquido", department_net, employee_net),
    ):
        difference = actual - expected
        checks.append(
            ValidationCheck(
                source_file=document.metadata.source_file,
                page=page,
                scope="DOCUMENTO",
                record_key=document.metadata.source_file,
                check=check_name,
                expected=expected,
                actual=actual,
                difference=difference,
                status=_status(difference, tolerance),
            )
        )
