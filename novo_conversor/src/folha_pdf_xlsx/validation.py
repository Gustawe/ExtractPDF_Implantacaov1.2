from __future__ import annotations

from decimal import Decimal

from .models import PayrollDocument, ValidationCheck, ZERO


DEFAULT_TOLERANCE = Decimal("0.01")


def _status(difference: Decimal, tolerance: Decimal) -> str:
    return "OK" if abs(difference) <= tolerance else "FALHA"


def validate_document(
    document: PayrollDocument,
    tolerance: Decimal = DEFAULT_TOLERANCE,
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    for employee in document.employees:
        event_earnings = sum(
            (event.value for event in employee.events if event.kind == "P"), ZERO
        )
        event_discounts = sum(
            (event.value for event in employee.events if event.kind == "D"), ZERO
        )
        for check_name, expected, actual in (
            ("Soma de proventos", employee.total_earnings, event_earnings),
            ("Soma de descontos", employee.total_discounts, event_discounts),
            (
                "Cálculo do líquido",
                employee.net_amount,
                employee.total_earnings - employee.total_discounts,
            ),
        ):
            difference = actual - expected
            checks.append(
                ValidationCheck(
                    source_file=employee.source_file,
                    scope="FUNCIONARIO",
                    record_key=employee.employee_key,
                    check=check_name,
                    expected=expected,
                    actual=actual,
                    difference=difference,
                    status=_status(difference, tolerance),
                )
            )

    if document.departments:
        employee_earnings = sum(
            (employee.total_earnings for employee in document.employees), ZERO
        )
        employee_discounts = sum(
            (employee.total_discounts for employee in document.employees), ZERO
        )
        employee_net = sum(
            (employee.net_amount for employee in document.employees), ZERO
        )
        department_earnings = sum(
            (item.earnings for item in document.departments), ZERO
        )
        department_discounts = sum(
            (item.discounts for item in document.departments), ZERO
        )
        department_net = sum(
            (item.net_amount for item in document.departments), ZERO
        )
        for check_name, expected, actual in (
            ("Total geral de proventos", department_earnings, employee_earnings),
            ("Total geral de descontos", department_discounts, employee_discounts),
            ("Total geral líquido", department_net, employee_net),
        ):
            difference = actual - expected
            checks.append(
                ValidationCheck(
                    source_file=document.metadata.source_file,
                    scope="DOCUMENTO",
                    record_key=document.metadata.source_file,
                    check=check_name,
                    expected=expected,
                    actual=actual,
                    difference=difference,
                    status=_status(difference, tolerance),
                )
            )
    return checks

