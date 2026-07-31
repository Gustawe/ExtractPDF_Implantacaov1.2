from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Qt
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from conversor_folhas import __version__
from conversor_folhas.application.conversion_service import ConversionService
from conversor_folhas.application.models import QueueItem, QueueStatus
from conversor_folhas.application.queue_manager import QueueManager
from conversor_folhas.infrastructure.engine_adapter import PayrollEngineAdapter
from conversor_folhas.infrastructure.history_repository import (
    SQLiteHistoryRepository,
)
from conversor_folhas.infrastructure.windows_shell import open_file, open_folder

from .conversion_worker import BatchConversionWorker
from .history_dialog import HistoryDialog
from .queue_table_model import QueueTableModel
from .theme import apply_theme


class MainWindow(QMainWindow):
    def __init__(
        self,
        history_repository: SQLiteHistoryRepository | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle(f"Conversor de Folhas — Implantação {__version__}")
        self.setMinimumSize(980, 640)
        self.setAcceptDrops(True)

        self._settings = QSettings()
        self._dialog_open = False
        self._conversion_running = False
        self._thread: QThread | None = None
        self._worker: BatchConversionWorker | None = None
        self._failure_count = 0
        self._warning_count = 0
        self._history_repository = history_repository

        self._queue_manager = QueueManager()
        self._queue_model = QueueTableModel(self._queue_manager)
        self._conversion_service = ConversionService(
            PayrollEngineAdapter(),
            history_repository,
        )

        self._build_interface()
        self._restore_theme()
        self._refresh_actions()

    def set_startup_message(self, message: str) -> None:
        """Exibe um aviso de inicialização sem expor detalhes da interface."""
        self._set_message(message)

    def _build_interface(self) -> None:
        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(28, 22, 28, 24)
        root_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        app_name = QLabel("Conversor de Folhas — Implantação")
        app_name.setObjectName("appName")
        self._version_label = QLabel(f"Versão {__version__}")
        self._version_label.setObjectName("versionLabel")
        self._theme_button = QPushButton("Modo escuro")
        self._theme_button.setCheckable(True)
        self._theme_button.clicked.connect(self._toggle_theme)
        self._history_button = QPushButton("Histórico")
        self._history_button.clicked.connect(self._open_history)
        if self._history_repository is None:
            self._history_button.setEnabled(False)
            self._history_button.setToolTip("Histórico local indisponível.")
        header_layout.addWidget(app_name)
        header_layout.addStretch()
        header_layout.addWidget(self._version_label)
        header_layout.addSpacing(12)
        header_layout.addWidget(self._history_button)
        header_layout.addWidget(self._theme_button)
        root_layout.addLayout(header_layout)

        instruction = QLabel("Selecione os arquivos que deseja converter.")
        instruction.setObjectName("instructionLabel")
        root_layout.addWidget(instruction)

        input_layout = QHBoxLayout()
        self._add_files_button = QPushButton("Adicionar PDFs")
        self._add_files_button.clicked.connect(self._choose_files)
        self._add_folder_button = QPushButton("Adicionar pasta")
        self._add_folder_button.clicked.connect(self._choose_folder)
        input_layout.addWidget(self._add_files_button)
        input_layout.addWidget(self._add_folder_button)
        input_layout.addStretch()
        root_layout.addLayout(input_layout)

        self._drop_area = QLabel("↓  Arraste arquivos PDF para esta área")
        self._drop_area.setObjectName("dropArea")
        self._drop_area.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(self._drop_area)

        self._table = QTableView()
        self._table.setModel(self._queue_model)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setSortingEnabled(False)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.selectionModel().selectionChanged.connect(self._refresh_actions)
        self._table.doubleClicked.connect(self._activate_selected_item)
        root_layout.addWidget(self._table, 1)

        queue_actions = QHBoxLayout()
        self._remove_button = QPushButton("Remover selecionados")
        self._remove_button.clicked.connect(self._remove_selected)
        self._remove_completed_button = QPushButton("Remover finalizados")
        self._remove_completed_button.clicked.connect(self._remove_completed)
        self._details_button = QPushButton("Ver detalhes")
        self._details_button.clicked.connect(self._show_selected_details)
        self._open_result_button = QPushButton("Abrir XLSX")
        self._open_result_button.clicked.connect(self._open_selected_result)
        self._open_folder_button = QPushButton("Abrir pasta")
        self._open_folder_button.clicked.connect(self._open_selected_folder)
        queue_actions.addWidget(self._remove_button)
        queue_actions.addWidget(self._remove_completed_button)
        queue_actions.addStretch()
        queue_actions.addWidget(self._details_button)
        queue_actions.addWidget(self._open_result_button)
        queue_actions.addWidget(self._open_folder_button)
        root_layout.addLayout(queue_actions)

        progress_layout = QHBoxLayout()
        self._progress_label = QLabel("Nenhum arquivo na fila")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.valueChanged.connect(self._update_progress_text_color)
        self._convert_button = QPushButton("Iniciar conversão")
        self._convert_button.setObjectName("primaryButton")
        self._convert_button.clicked.connect(self._start_conversion)
        progress_layout.addWidget(self._progress_label)
        progress_layout.addWidget(self._progress_bar, 1)
        progress_layout.addWidget(self._convert_button)
        root_layout.addLayout(progress_layout)

        self._message_label = QLabel("Adicione um ou mais PDFs para começar.")
        self._message_label.setObjectName("messageLabel")
        self._message_label.setWordWrap(True)
        root_layout.addWidget(self._message_label)

        self.setCentralWidget(central_widget)

    def _open_history(self) -> None:
        if self._history_repository is None or self._conversion_running:
            return
        HistoryDialog(self._history_repository, self).exec()

    def _choose_files(self) -> None:
        if self._dialog_open or self._conversion_running:
            return
        self._dialog_open = True
        self._set_input_enabled(False)
        try:
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Adicionar folhas de pagamento",
                "",
                "Arquivos PDF (*.pdf)",
            )
            if paths:
                self._add_paths(paths)
        finally:
            self._dialog_open = False
            self._set_input_enabled(not self._conversion_running)

    def _choose_folder(self) -> None:
        if self._dialog_open or self._conversion_running:
            return
        self._dialog_open = True
        self._set_input_enabled(False)
        try:
            selected = QFileDialog.getExistingDirectory(
                self,
                "Selecionar pasta com PDFs",
            )
            if not selected:
                return
            folder = Path(selected)
            try:
                pdfs = sorted(
                    path
                    for path in folder.iterdir()
                    if path.is_file() and path.suffix.lower() == ".pdf"
                )
            except OSError as error:
                self._show_error("Não foi possível ler a pasta", str(error))
                return
            if not pdfs:
                self._set_message("Nenhum PDF foi encontrado na pasta selecionada.")
                return
            self._add_paths(pdfs)
        finally:
            self._dialog_open = False
            self._set_input_enabled(not self._conversion_running)

    def _add_paths(self, paths: list[str] | list[Path]) -> None:
        result = self._queue_model.add_paths(paths)
        messages: list[str] = []
        if result.added:
            messages.append(f"{len(result.added)} arquivo(s) adicionado(s) à fila.")
        if result.duplicate_count:
            messages.append(f"{result.duplicate_count} duplicado(s) ignorado(s).")
        if result.invalid_count:
            messages.append(f"{result.invalid_count} arquivo(s) inválido(s) ignorado(s).")
        if result.added:
            pending_count = len(self._queue_manager.pending_requests())
            self._progress_bar.setValue(0)
            self._progress_label.setText(
                f"{pending_count} arquivo(s) aguardando conversão"
            )
        self._set_message(" ".join(messages) or "Nenhum arquivo foi adicionado.")
        self._refresh_actions()

    def _remove_selected(self) -> None:
        rows = self._selected_rows()
        removed = self._queue_model.remove_rows(rows)
        if removed:
            self._set_message(f"{removed} arquivo(s) removido(s) da fila.")
        self._refresh_actions()

    def _remove_completed(self) -> None:
        removed = self._queue_model.remove_completed()
        if removed:
            self._set_message(f"{removed} arquivo(s) finalizado(s) removido(s).")
        self._refresh_actions()

    def _start_conversion(self) -> None:
        if self._conversion_running:
            return
        requests = self._queue_manager.pending_requests()
        if not requests:
            self._set_message("Não há arquivos aguardando conversão.")
            return

        self._conversion_running = True
        self._failure_count = 0
        self._warning_count = 0
        self._progress_bar.setValue(0)
        self._progress_label.setText(f"0 de {len(requests)} concluídos")
        self._set_message("Conversão iniciada.")
        self._set_input_enabled(False)
        self._refresh_actions()

        thread = QThread(self)
        worker = BatchConversionWorker(self._conversion_service, requests)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.item_started.connect(self._queue_model.set_processing)
        worker.item_succeeded.connect(self._on_item_succeeded)
        worker.item_failed.connect(self._on_item_failed)
        worker.progress_changed.connect(self._on_progress_changed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_conversion_finished)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_item_succeeded(
        self,
        identifier: str,
        output_path: str,
        warning: bool,
        message: str,
    ) -> None:
        self._queue_model.set_succeeded(
            identifier,
            output_path,
            warning,
            message,
        )
        if warning:
            self._warning_count += 1

    def _on_item_failed(self, identifier: str, message: str) -> None:
        self._failure_count += 1
        self._queue_model.set_failed(identifier, message)

    def _on_progress_changed(self, completed: int, total: int) -> None:
        percentage = round((completed / total) * 100) if total else 0
        self._progress_bar.setValue(percentage)
        self._progress_label.setText(f"{completed} de {total} concluídos")

    def _update_progress_text_color(self, value: int) -> None:
        self._progress_bar.setStyleSheet(
            "color: #ffffff;" if value == self._progress_bar.maximum() else ""
        )

    def _on_conversion_finished(self) -> None:
        self._conversion_running = False
        self._thread = None
        self._worker = None
        self._set_input_enabled(True)
        if self._failure_count:
            self._set_message(
                f"Conversão finalizada com {self._failure_count} erro(s). "
                "Selecione o arquivo e clique em Ver detalhes."
            )
        elif self._warning_count:
            self._set_message(
                f"Conversão finalizada com {self._warning_count} alerta(s)."
            )
        else:
            self._set_message("Conversão finalizada com sucesso.")
        self._refresh_actions()

    def _activate_selected_item(self, *_args: object) -> None:
        item = self._selected_item()
        if item is None:
            return
        if item.output_path is not None:
            self._open_selected_result()
        elif item.message:
            self._show_selected_details()

    def _show_selected_details(self) -> None:
        item = self._selected_item()
        if item is None or not item.message:
            return
        QMessageBox.information(
            self,
            f"Detalhes — {item.source_path.name}",
            item.message,
        )

    def _open_selected_result(self) -> None:
        item = self._selected_item()
        if item is None or item.output_path is None:
            return
        try:
            open_file(item.output_path)
        except OSError as error:
            self._show_error("Não foi possível abrir o XLSX", str(error))

    def _open_selected_folder(self) -> None:
        item = self._selected_item()
        if item is None:
            return
        target = item.output_path or item.source_path
        try:
            open_folder(target)
        except OSError as error:
            self._show_error("Não foi possível abrir a pasta", str(error))

    def _selected_rows(self) -> list[int]:
        selection_model = self._table.selectionModel()
        return [index.row() for index in selection_model.selectedRows()]

    def _selected_item(self) -> QueueItem | None:
        rows = self._selected_rows()
        return self._queue_model.item_at(rows[0]) if rows else None

    def _refresh_actions(self, *_args: object) -> None:
        selected = self._selected_item()
        has_items = bool(self._queue_manager.items)
        has_pending = bool(self._queue_manager.pending_requests())
        has_finished = any(
            item.status
            in {QueueStatus.SUCCEEDED, QueueStatus.WARNING, QueueStatus.FAILED}
            for item in self._queue_manager.items
        )

        self._remove_button.setEnabled(
            selected is not None and not self._conversion_running
        )
        self._remove_completed_button.setEnabled(
            has_finished and not self._conversion_running
        )
        self._open_result_button.setEnabled(
            selected is not None and selected.output_path is not None
        )
        self._details_button.setEnabled(
            selected is not None and bool(selected.message)
        )
        self._open_folder_button.setEnabled(selected is not None)
        self._convert_button.setEnabled(has_pending and not self._conversion_running)
        self._history_button.setEnabled(
            self._history_repository is not None and not self._conversion_running
        )
        if not has_items:
            self._progress_label.setText("Nenhum arquivo na fila")
            if not self._conversion_running:
                self._progress_bar.setValue(0)
        elif (
            not self._conversion_running
            and self._progress_bar.value() == 0
            and has_pending
        ):
            pending_count = len(self._queue_manager.pending_requests())
            self._progress_label.setText(
                f"{pending_count} arquivo(s) aguardando conversão"
            )

    def _set_input_enabled(self, enabled: bool) -> None:
        self._add_files_button.setEnabled(enabled)
        self._add_folder_button.setEnabled(enabled)
        self._drop_area.setEnabled(enabled)

    def _set_message(self, message: str) -> None:
        self._message_label.setText(message)

    def _show_error(self, title: str, message: str) -> None:
        self._set_message(message)
        QMessageBox.critical(self, title, message)

    def _restore_theme(self) -> None:
        dark_mode = self._settings.value("interface/dark_mode", False, type=bool)
        self._theme_button.setChecked(dark_mode)
        self._apply_current_theme()

    def _toggle_theme(self) -> None:
        self._settings.setValue("interface/dark_mode", self._theme_button.isChecked())
        self._apply_current_theme()

    def _apply_current_theme(self) -> None:
        dark_mode = self._theme_button.isChecked()
        self._theme_button.setText("Modo claro" if dark_mode else "Modo escuro")
        application = QApplication.instance()
        if isinstance(application, QApplication):
            apply_theme(application, dark_mode)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._conversion_running or not event.mimeData().hasUrls():
            event.ignore()
            return
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        if any(path.is_dir() or path.suffix.lower() == ".pdf" for path in paths):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if self._conversion_running:
            event.ignore()
            return
        paths: list[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                try:
                    paths.extend(
                        child
                        for child in path.iterdir()
                        if child.is_file() and child.suffix.lower() == ".pdf"
                    )
                except OSError as error:
                    self._set_message(f"Não foi possível ler {path}: {error}")
            else:
                paths.append(path)
        self._add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._conversion_running:
            QMessageBox.information(
                self,
                "Conversão em andamento",
                "Aguarde a conversão atual terminar antes de fechar o aplicativo.",
            )
            event.ignore()
            return
        event.accept()
