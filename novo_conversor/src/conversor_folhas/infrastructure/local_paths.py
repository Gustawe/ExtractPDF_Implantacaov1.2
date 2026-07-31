from __future__ import annotations

import os
from pathlib import Path


APPLICATION_DIRECTORY_NAME = "ConversorFolhas"


def application_data_directory() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    base_directory = Path(local_app_data) if local_app_data else Path.home()
    directory = base_directory / APPLICATION_DIRECTORY_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def log_directory() -> Path:
    directory = application_data_directory() / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def history_database_path() -> Path:
    return application_data_directory() / "history.sqlite3"
