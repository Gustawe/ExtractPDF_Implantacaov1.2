from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LayoutWord:
    text: str
    x0: float


@dataclass(frozen=True, slots=True)
class LayoutLine:
    page: int
    top: float
    words: tuple[LayoutWord, ...]

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words).strip()

    def between(self, start: float, end: float) -> tuple[LayoutWord, ...]:
        return tuple(word for word in self.words if start <= word.x0 < end)


@dataclass(slots=True)
class PayrollLayoutSection:
    title: str
    nickname: str
    company_name: str
    cnpj: str
    registration: str
    period_start: str
    period_end: str
    address: str
    district: str
    city: str
    state: str
    source_pages: list[int] = field(default_factory=list)
    employee_blocks: list[list[LayoutLine]] = field(default_factory=list)
    summary_lines: list[LayoutLine] = field(default_factory=list)


@dataclass(slots=True)
class PayrollLayoutDocument:
    source_path: Path
    page_count: int
    sections: list[PayrollLayoutSection] = field(default_factory=list)

    @property
    def employee_count(self) -> int:
        return sum(len(section.employee_blocks) for section in self.sections)

