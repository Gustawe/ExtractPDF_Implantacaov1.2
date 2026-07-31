from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot

from conversor_folhas.application.conversion_service import ConversionService
from conversor_folhas.application.models import ConversionRequest


LOGGER = logging.getLogger(__name__)


class BatchConversionWorker(QObject):
    item_started = Signal(str)
    item_succeeded = Signal(str, str, bool, str)
    item_failed = Signal(str, str)
    progress_changed = Signal(int, int)
    finished = Signal()

    def __init__(
        self,
        service: ConversionService,
        requests: tuple[ConversionRequest, ...],
    ) -> None:
        super().__init__()
        self._service = service
        self._requests = requests

    @Slot()
    def run(self) -> None:
        completed = 0
        total = len(self._requests)
        for request in self._requests:
            self.item_started.emit(request.identifier)
            try:
                result = self._service.convert(request.source_path)
                self.item_succeeded.emit(
                    request.identifier,
                    str(result.output_path),
                    result.has_warning,
                    result.message,
                )
            except Exception as error:
                LOGGER.exception("Falha no worker para %s", request.source_path)
                message = f"{type(error).__name__}: {error}"
                self.item_failed.emit(request.identifier, message)
            completed += 1
            self.progress_changed.emit(completed, total)
        self.finished.emit()

