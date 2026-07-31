from __future__ import annotations

import os
from pathlib import Path


def open_file(path: str | Path) -> None:
    target = Path(path).resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {target}")
    os.startfile(target)  # type: ignore[attr-defined]


def open_folder(path: str | Path) -> None:
    target = Path(path).resolve()
    directory = target if target.is_dir() else target.parent
    if not directory.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {directory}")
    os.startfile(directory)  # type: ignore[attr-defined]

