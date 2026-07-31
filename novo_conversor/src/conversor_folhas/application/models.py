from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4


class QueueStatus(str, Enum):
    WAITING = "Aguardando"
    PROCESSING = "Convertendo"
    SUCCEEDED = "Concluído"
    WARNING = "Concluído com alertas"
    FAILED = "Erro"


@dataclass(slots=True)
class QueueItem:
    source_path: Path
    identifier: str = field(default_factory=lambda: uuid4().hex)
    status: QueueStatus = QueueStatus.WAITING
    output_path: Path | None = None
    message: str = ""


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

    @property
    def has_warning(self) -> bool:
        return self.engine_status not in {"", "APROVADO"}


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    source_path: Path
    output_path: Path | None
    status: str
    message: str
    completed_at: datetime


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    identifier: int
    source_path: Path
    output_path: Path | None
    status: str
    message: str
    completed_at: datetime
