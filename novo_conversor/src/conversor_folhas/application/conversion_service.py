from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .models import ConversionResult


LOGGER = logging.getLogger(__name__)


class EnginePort(Protocol):
    def convert(self, source_path: Path, output_path: Path) -> tuple[str, str]: ...


class ConversionService:
    """Converte um PDF e publica o XLSX sem sobrescrever arquivos existentes."""

    def __init__(self, engine: EnginePort) -> None:
        self._engine = engine

    def convert(self, source_path: str | Path) -> ConversionResult:
        source = Path(source_path).expanduser().resolve()
        self._validate_source(source)

        temporary_output = source.parent / (
            f".{source.stem}.{uuid4().hex}.temporario.xlsx"
        )
        try:
            engine_status, message = self._engine.convert(source, temporary_output)
            if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
                raise RuntimeError("O motor não gerou um XLSX válido.")
            final_output = self._publish_without_overwrite(source, temporary_output)
            return ConversionResult(
                source_path=source,
                output_path=final_output,
                engine_status=engine_status,
                message=message,
            )
        except Exception:
            LOGGER.exception("Falha ao converter %s", source)
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

