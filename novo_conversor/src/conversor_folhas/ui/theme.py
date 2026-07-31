from __future__ import annotations

from PySide6.QtWidgets import QApplication


LIGHT_STYLE = """
QWidget {
    background-color: #ffffff;
    color: #202124;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow { background-color: #ffffff; }
QLabel#appName {
    color: #010042;
    font-size: 17pt;
    font-weight: 600;
}
QLabel#versionLabel { color: #5f6368; }
QLabel#instructionLabel { color: #3c4043; font-size: 11pt; }
QLabel#dropArea {
    background-color: #f7f8fb;
    border: 1px dashed #8b8ba8;
    border-radius: 4px;
    color: #4f4f66;
    padding: 16px;
}
QLabel#messageLabel {
    background-color: #f2f4f8;
    border-left: 3px solid #010042;
    padding: 8px 10px;
}
QPushButton {
    background-color: #f5f6f8;
    border: 1px solid #c7c9d1;
    border-radius: 4px;
    padding: 7px 14px;
}
QPushButton:hover { background-color: #eceef3; }
QPushButton:pressed { background-color: #e1e3e9; }
QPushButton:disabled { color: #9aa0a6; background-color: #f4f4f4; }
QPushButton#primaryButton {
    background-color: #010042;
    border-color: #010042;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 20px;
}
QPushButton#primaryButton:hover { background-color: #17165a; }
QTableView {
    alternate-background-color: #f8f9fb;
    background-color: #ffffff;
    border: 1px solid #d9dbe2;
    gridline-color: #e6e7eb;
    selection-background-color: #dce5f4;
    selection-color: #202124;
}
QHeaderView::section {
    background-color: #eef1f6;
    border: none;
    border-bottom: 1px solid #cdd1d9;
    color: #30313a;
    font-weight: 600;
    padding: 8px;
}
QProgressBar {
    border: 1px solid #c7c9d1;
    border-radius: 3px;
    background-color: #f2f3f5;
    min-height: 16px;
    text-align: center;
}
QProgressBar::chunk { background-color: #010042; }
"""


DARK_STYLE = """
QWidget {
    background-color: #17171c;
    color: #e8e8ed;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow { background-color: #17171c; }
QLabel#appName { color: #ffffff; font-size: 17pt; font-weight: 600; }
QLabel#versionLabel { color: #a9a9b5; }
QLabel#instructionLabel { color: #e0e0e6; font-size: 11pt; }
QLabel#dropArea {
    background-color: #202029;
    border: 1px dashed #77778e;
    border-radius: 4px;
    color: #c5c5d0;
    padding: 16px;
}
QLabel#messageLabel {
    background-color: #22222b;
    border-left: 3px solid #7f8cff;
    padding: 8px 10px;
}
QPushButton {
    background-color: #2a2a33;
    border: 1px solid #4a4a57;
    border-radius: 4px;
    color: #eeeeF2;
    padding: 7px 14px;
}
QPushButton:hover { background-color: #34343f; }
QPushButton:pressed { background-color: #3d3d48; }
QPushButton:disabled { color: #74747f; background-color: #222228; }
QPushButton#primaryButton {
    background-color: #3936a6;
    border-color: #5552c8;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 20px;
}
QPushButton#primaryButton:hover { background-color: #4845b8; }
QTableView {
    alternate-background-color: #202027;
    background-color: #1b1b21;
    border: 1px solid #3f3f49;
    gridline-color: #34343d;
    selection-background-color: #39365f;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #272730;
    border: none;
    border-bottom: 1px solid #484852;
    color: #f0f0f3;
    font-weight: 600;
    padding: 8px;
}
QProgressBar {
    border: 1px solid #4a4a57;
    border-radius: 3px;
    background-color: #24242c;
    min-height: 16px;
    text-align: center;
}
QProgressBar::chunk { background-color: #5a57cc; }
"""


def apply_theme(application: QApplication, dark_mode: bool) -> None:
    application.setStyle("Fusion")
    application.setStyleSheet(DARK_STYLE if dark_mode else LIGHT_STYLE)

