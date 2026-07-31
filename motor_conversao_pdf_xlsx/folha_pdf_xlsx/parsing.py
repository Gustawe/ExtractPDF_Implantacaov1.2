from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")
NUMBER_PATTERN = re.compile(r"^-?[\d.]+,\d{2}$")
INTEGER_PATTERN = re.compile(r"^-?\d+$")


def parse_br_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    normalized = value.strip().replace("R$", "").replace(" ", "")
    if not normalized or not NUMBER_PATTERN.match(normalized):
        return None
    try:
        return Decimal(normalized.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def parse_br_number(value: str | None) -> Decimal | None:
    decimal_value = parse_br_decimal(value)
    if decimal_value is not None:
        return decimal_value
    if value is None:
        return None
    normalized = value.strip().replace(" ", "")
    if not INTEGER_PATTERN.match(normalized):
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def parse_br_date(value: str | None):
    if not value:
        return None
    normalized = value.strip()
    if not DATE_PATTERN.match(normalized):
        return None
    try:
        return datetime.strptime(normalized, "%d/%m/%Y").date()
    except ValueError:
        return None


def words_text(words: Iterable[dict[str, Any]]) -> str:
    return " ".join(str(word["text"]) for word in sorted(words, key=lambda item: item["x0"]))


def clean_label_artifacts(value: str) -> str:
    labels = (
        "Situação:",
        "CPF:",
        "Adm:",
        "C.B.O:",
        "Filial:",
        "Salário:",
        "Depto:",
        "Horas Mês:",
    )
    cleaned = value
    for label in labels:
        cleaned = cleaned.replace(label, "")
    return " ".join(cleaned.split()).strip()
