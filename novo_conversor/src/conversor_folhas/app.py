from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from folha_pdf_xlsx.logging_config import configure_logging

from . import __version__
from .infrastructure.history_repository import SQLiteHistoryRepository
from .infrastructure.local_paths import history_database_path, log_directory
from .ui.main_window import MainWindow


LOGGER = logging.getLogger(__name__)


def _application_icon_path() -> Path:
    return Path(__file__).resolve().parent / "resources" / "app.ico"


def main() -> int:
    QCoreApplication.setOrganizationName("ConversorFolhas")
    QCoreApplication.setApplicationName("Conversor de Folhas")
    QCoreApplication.setApplicationVersion(__version__)

    configure_logging(log_directory(), diagnostic=False)
    application = QApplication(sys.argv)
    application.setApplicationDisplayName(
        f"Conversor de Folhas — Implantação {__version__}"
    )
    icon_path = _application_icon_path()
    if icon_path.is_file():
        application.setWindowIcon(QIcon(str(icon_path)))

    try:
        history_repository: SQLiteHistoryRepository | None = None
        history_error = ""
        try:
            history_repository = SQLiteHistoryRepository(history_database_path())
            history_repository.initialize()
        except Exception as error:
            LOGGER.exception("Histórico local indisponível")
            history_repository = None
            history_error = f"Histórico local indisponível: {error}"

        window = MainWindow(history_repository)
        if history_error:
            window.set_startup_message(history_error)
        window.show()
        if "--smoke-test" in sys.argv:
            application.processEvents()
            window.close()
            return 0
        return application.exec()
    except Exception as error:
        LOGGER.exception("Falha ao iniciar o aplicativo")
        QMessageBox.critical(
            None,
            "Falha ao iniciar",
            f"O aplicativo não pôde ser iniciado.\n\n{type(error).__name__}: {error}",
        )
        return 1
