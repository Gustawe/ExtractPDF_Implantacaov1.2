from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from .models import (
    ConversionRequest,
    QueueAddResult,
    QueueItem,
    QueueStatus,
)


class QueueManager:
    """Mantém a fila em memória sem qualquer dependência da interface."""

    def __init__(self) -> None:
        self._items: list[QueueItem] = []
        self._path_keys: set[str] = set()

    @property
    def items(self) -> tuple[QueueItem, ...]:
        return tuple(self._items)

    def add_paths(self, paths: Iterable[str | Path]) -> QueueAddResult:
        prepared, duplicate_count, invalid_count = self.prepare_paths(paths)
        added = self.append_prepared(prepared)
        return QueueAddResult(
            added=added,
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
        )

    def prepare_paths(
        self,
        paths: Iterable[str | Path],
    ) -> tuple[tuple[Path, ...], int, int]:
        prepared: list[Path] = []
        prepared_keys = set(self._path_keys)
        duplicate_count = 0
        invalid_count = 0

        for raw_path in paths:
            path = Path(raw_path).expanduser().resolve()
            if not path.is_file() or path.suffix.lower() != ".pdf":
                invalid_count += 1
                continue
            path_key = self._path_key(path)
            if path_key in prepared_keys:
                duplicate_count += 1
                continue
            prepared.append(path)
            prepared_keys.add(path_key)

        return tuple(prepared), duplicate_count, invalid_count

    def append_prepared(self, paths: Iterable[Path]) -> tuple[QueueItem, ...]:
        added: list[QueueItem] = []
        for path in paths:
            path_key = self._path_key(path)
            if path_key in self._path_keys:
                continue
            item = QueueItem(source_path=path)
            self._items.append(item)
            self._path_keys.add(path_key)
            added.append(item)
        return tuple(added)

    def remove_rows(self, rows: Iterable[int]) -> int:
        removed_count = 0
        for row in sorted(set(rows), reverse=True):
            if not 0 <= row < len(self._items):
                continue
            item = self._items[row]
            if item.status == QueueStatus.PROCESSING:
                continue
            self._items.pop(row)
            self._path_keys.discard(self._path_key(item.source_path))
            removed_count += 1
        return removed_count

    def remove_completed(self) -> int:
        removable = {
            QueueStatus.SUCCEEDED,
            QueueStatus.WARNING,
            QueueStatus.DIVERGENCE,
            QueueStatus.FAILED,
        }
        rows = [
            index
            for index, item in enumerate(self._items)
            if item.status in removable
        ]
        return self.remove_rows(rows)

    def pending_requests(self) -> tuple[ConversionRequest, ...]:
        return tuple(
            ConversionRequest(item.identifier, item.source_path)
            for item in self._items
            if item.status == QueueStatus.WAITING
        )

    def find(self, identifier: str) -> QueueItem | None:
        return next(
            (item for item in self._items if item.identifier == identifier),
            None,
        )

    @staticmethod
    def _path_key(path: Path) -> str:
        return os.path.normcase(str(path.resolve()))
