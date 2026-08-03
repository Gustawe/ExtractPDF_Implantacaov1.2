from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from folha_pdf_xlsx.models import ConversionDetails

from .models import ConversionResult, HistoryEntry


LOGGER = logging.getLogger(__name__)


class ConversionFailedError(RuntimeError):
    def __init__(self, message: str, details: ConversionDetails) -> None:
        super().__init__(message)
        self.details = details


class EnginePort(Protocol):
    def convert(
        self, source_path: Path, output_path: Path
    ) -> tuple[str, str, ConversionDetails] | tuple[str, str]: ...


class HistoryPort(Protocol):
    def record(self, entry: HistoryEntry) -> None: ...


class ConversionService:
    """Converte um PDF e publica o XLSX sem sobrescrever arquivos existentes."""

    def __init__(
        self,
        engine: EnginePort,
        history: HistoryPort | None = None,
    ) -> None:
        self._engine = engine
        self._history = history

    def convert(self, source_path: str | Path) -> ConversionResult:
        source = Path(source_path).expanduser().resolve()
        self._validate_source(source)

        temporary_output = source.parent / (
            f".{source.stem}.{uuid4().hex}.temporario.xlsx"
        )
        details = ConversionDetails()
        try:
            engine_result = self._engine.convert(source, temporary_output)
            if len(engine_result) == 2:
                engine_status, message = engine_result
                details = ConversionDetails()
            else:
                engine_status, message, details = engine_result
            if engine_status in {"ERRO", "REPROVADO"}:
                raise ConversionFailedError(
                    message or "O motor classificou o resultado como inválido.",
                    details,
                )
            if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
                raise RuntimeError("O motor não gerou um XLSX válido.")
            final_output = self._publish_without_overwrite(source, temporary_output)
            result = ConversionResult(
                source_path=source,
                output_path=final_output,
                engine_status=engine_status,
                message=message,
                details=details,
            )
            self._record_history(
                HistoryEntry(
                    source_path=source,
                    output_path=final_output,
                    status=engine_status,
                    message=message,
                    completed_at=datetime.now().astimezone(),
                    details=details,
                )
            )
            return result
        except Exception as error:
            LOGGER.exception("Falha ao converter %s", source)
            self._record_history(
                HistoryEntry(
                    source_path=source,
                    output_path=None,
                    status="ERRO",
                    message=f"{type(error).__name__}: {error}",
                    completed_at=datetime.now().astimezone(),
                    details=details,
                )
            )
            raise
        finally:
            temporary_output.unlink(missing_ok=True)

    @staticmethod
    def _validate_source(source: Path) -> None:
        if not source.is_file():
            raise FileNotFoundError(f"PDF não encontrado: {source}")
        if source.suffix.lower() != ".pdf":
            raise ValueError(f"O arquivo selecionado não é um PDF: {source.name}")

    @classmethod
    def _publish_without_overwrite(
        cls,
        source: Path,
        temporary_output: Path,
    ) -> Path:
        sequence = 0
        while True:
            candidate = cls._output_candidate(source, sequence)
            try:
                # No Windows, os.rename falha se o destino já existir. Isso evita
                # substituir silenciosamente uma planilha criada por outro processo.
                os.rename(temporary_output, candidate)
                return candidate
            except FileExistsError:
                sequence += 1

    @staticmethod
    def _output_candidate(source: Path, sequence: int) -> Path:
        suffix = "" if sequence == 0 else f" ({sequence})"
        return source.with_name(f"{source.stem}{suffix}.xlsx")

    def _record_history(self, entry: HistoryEntry) -> None:
        if self._history is None:
            return
        try:
            self._history.record(entry)
        except Exception:
            # Uma indisponibilidade do histórico nunca deve invalidar um XLSX
            # que já foi convertido corretamente.
            LOGGER.exception("Não foi possível registrar o histórico local")
