from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_directory: Path, diagnostic: bool = False) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if diagnostic else logging.INFO
    handler = RotatingFileHandler(
        log_directory / "folha_pdf_xlsx.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

