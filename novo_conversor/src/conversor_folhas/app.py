from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from folha_pdf_xlsx.logging_config import configure_logging

from . import __version__
from .infrastructure.local_paths import log_directory
from .ui.main_window import MainWindow


LOGGER = logging.getLogger(__name__)


def main() -> int:
    QCoreApplication.setOrganizationName("ConversorFolhas")
    QCoreApplication.setApplicationName("Conversor de Folhas")
    QCoreApplication.setApplicationVersion(__version__)

    configure_logging(log_directory(), diagnostic=False)
    application = QApplication(sys.argv)
    application.setApplicationDisplayName("Conversor de Folhas — Implantação")

    try:
        window = MainWindow()
        window.show()
        return application.exec()
    except Exception as error:
        LOGGER.exception("Falha ao iniciar o aplicativo")
        QMessageBox.critical(
            None,
            "Falha ao iniciar",
            f"O aplicativo não pôde ser iniciado.\n\n{type(error).__name__}: {error}",
        )
        return 1

