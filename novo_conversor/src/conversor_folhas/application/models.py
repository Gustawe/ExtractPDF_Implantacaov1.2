from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4

from folha_pdf_xlsx.models import ConversionDetails


class QueueStatus(str, Enum):
    WAITING = "Aguardando"
    PROCESSING = "Convertendo"
    SUCCEEDED = "Concluído"
    WARNING = "Concluído com avisos"
    DIVERGENCE = "Concluído com divergências"
    FAILED = "Erro"


@dataclass(slots=True)
class QueueItem:
    source_path: Path
    identifier: str = field(default_factory=lambda: uuid4().hex)
    status: QueueStatus = QueueStatus.WAITING
    output_path: Path | None = None
    message: str = ""
    details: ConversionDetails = field(default_factory=ConversionDetails)


@dataclass(frozen=True, slots=True)
class QueueAddResult:
    added: tuple[QueueItem, ...]
    duplicate_count: int = 0
    invalid_count: int = 0


@dataclass(frozen=True, slots=True)
class ConversionRequest:
    identifier: str
    source_path: Path


@dataclass(frozen=True, slots=True)
class ConversionResult:
    source_path: Path
    output_path: Path
    engine_status: str
    message: str = ""
    details: ConversionDetails = field(default_factory=ConversionDetails)

    @property
    def has_warning(self) -> bool:
        return self.engine_status == "APROVADO COM AVISOS"

    @property
    def queue_status(self) -> QueueStatus:
        return queue_status_from_engine(self.engine_status)


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    source_path: Path
    output_path: Path | None
    status: str
    message: str
    completed_at: datetime
    details: ConversionDetails = field(default_factory=ConversionDetails)


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    identifier: int
    source_path: Path
    output_path: Path | None
    status: str
    message: str
    completed_at: datetime
    details: ConversionDetails = field(default_factory=ConversionDetails)


def queue_status_from_engine(status: str) -> QueueStatus:
    if status in {"ERRO", "REPROVADO"}:
        return QueueStatus.FAILED
    if status in {"APROVADO COM DIVERGÊNCIAS", "COM_DIVERGENCIAS"}:
        return QueueStatus.DIVERGENCE
    if status in {"APROVADO COM AVISOS", "COM_AVISOS"}:
        return QueueStatus.WARNING
    return QueueStatus.SUCCEEDED
