"""Graphical user interface for the launcher."""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Any

from PySide6 import QtWidgets, QtGui, QtCore

# Dark professional style sheet for the panel-like launcher
APP_STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: Arial, sans-serif;
    font-size: 14px;
}
QTabWidget::pane {
    border: none;
}
QTabBar::tab {
    background: #3c3c3c;
    color: #dddddd;
    padding: 4px 8px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #555555;
}
QToolButton {
    background: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 10px;
    padding: 6px;
}
QToolButton:hover {
    background: #4c4c4c;
}
QToolButton:pressed {
    background: #626262;
}
"""

from .config import load_config, save_config, CONFIG_PATH
from .dialogs import ItemDialog, ItemData, SectionDialog


class ConfigEditor(QtWidgets.QWidget):
    """Simple text editor for editing ``config.yaml`` within the UI."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.editor = QtWidgets.QPlainTextEdit()
        layout.addWidget(self.editor)

        buttons = QtWidgets.QHBoxLayout()
        self.reload_button = QtWidgets.QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload)
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)
        buttons.addStretch()
        buttons.addWidget(self.reload_button)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

        self.reload()

    def reload(self) -> None:
        if CONFIG_PATH.exists():
            text = CONFIG_PATH.read_text(encoding="utf-8")
            self.editor.setPlainText(text)

    def save(self) -> None:
        CONFIG_PATH.write_text(self.editor.toPlainText(), encoding="utf-8")


class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Launcher")
        # Apply the global style sheet for a consistent minimalistic look
        self.setStyleSheet(APP_STYLE)
        # Make the window a frameless panel that spans the top of the screen
        flags = (
            self.windowFlags()
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowFlags(flags)
        screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width(), 80)
        self.setFixedHeight(80)
        self.sections: List[Dict[str, Any]] = []
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.layout = QtWidgets.QVBoxLayout(self.central)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.layout.addWidget(self.tabs)
        self.config_editor = ConfigEditor()

        self._create_menu()
        self.menuBar().hide()
        self.reload_items()

        # Create tray icon used to show or hide the launcher on demand and
        # start hidden to minimise screen usage.
        self._create_tray()
        self.hide()

    def _create_menu(self) -> None:
        menubar = self.menuBar()
        config_menu = menubar.addMenu("Config")

        add_section = QtGui.QAction("Add Section", self)
        add_section.triggered.connect(self.add_section)
        config_menu.addAction(add_section)

        edit_section = QtGui.QAction("Edit Section", self)
        edit_section.triggered.connect(self.edit_section)
        config_menu.addAction(edit_section)

        remove_section = QtGui.QAction("Remove Section", self)
        remove_section.triggered.connect(self.remove_section)
        config_menu.addAction(remove_section)

        add_action = QtGui.QAction("Add Item", self)
        add_action.triggered.connect(self.add_item)
        config_menu.addAction(add_action)

        edit_action = QtGui.QAction("Edit Item", self)
        edit_action.triggered.connect(self.edit_item)
        config_menu.addAction(edit_action)

        remove_action = QtGui.QAction("Remove Item", self)
        remove_action.triggered.connect(self.remove_item)
        config_menu.addAction(remove_action)

        open_config_action = QtGui.QAction("Open config.yaml", self)
        open_config_action.triggered.connect(lambda: subprocess.Popen(["xdg-open", str(CONFIG_PATH)]))
        config_menu.addAction(open_config_action)

        reload_action = QtGui.QAction("Reload", self)
        reload_action.triggered.connect(self.reload_items)
        config_menu.addAction(reload_action)

    def _create_tray(self) -> None:
        """Set up system tray icon used to toggle the launcher window."""
        icon = QtGui.QIcon.fromTheme("system-run")
        if icon.isNull():
            icon = QtGui.QIcon("icon.png")  # your own icon
        self.tray = QtWidgets.QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Launcher")
        menu = QtWidgets.QMenu()
        toggle_action = menu.addAction("Show/Hide")
        toggle_action.triggered.connect(self._toggle_visibility)
        menu.addSeparator()
        menu.addAction("Add Section", self.add_section)
        menu.addAction("Edit Section", self.edit_section)
        menu.addAction("Remove Section", self.remove_section)
        menu.addSeparator()
        menu.addAction("Add Item", self.add_item)
        menu.addAction("Edit Item", self.edit_item)
        menu.addAction("Remove Item", self.remove_item)
        menu.addSeparator()
        menu.addAction("Open config.yaml", lambda: subprocess.Popen(["xdg-open", str(CONFIG_PATH)]))
        menu.addAction("Reload", self.reload_items)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QtWidgets.QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            self.setGeometry(0, 0, screen.width(), self.height())
            self.show()
            self.activateWindow()

    def add_section(self) -> None:
        dlg = SectionDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections.append({"name": dlg.get_name(), "items": []})
            save_config(self.sections)
            self.reload_items()

    def edit_section(self) -> None:
        if not self.sections:
            return
        idx = self._select_section("Edit Section", "Select section")
        if idx is None:
            return
        dlg = SectionDialog(self, self.sections[idx].get("name", ""))
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections[idx]["name"] = dlg.get_name()
            save_config(self.sections)
            self.reload_items()

    def remove_section(self) -> None:
        if not self.sections:
            return
        idx = self._select_section("Remove Section", "Select section")
        if idx is not None:
            del self.sections[idx]
            save_config(self.sections)
            self.reload_items()

    def reload_items(self) -> None:
        """Reload items from configuration and rebuild UI."""
        self.sections = load_config()
        while self.tabs.count():
            self.tabs.removeTab(0)


        for section in self.sections:
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(widget)
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)

            for item in section.get("items", []):
                button = QtWidgets.QToolButton()
                button.setText(item.get("name", ""))
                button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
                icon_path = item.get("icon")
                if icon_path and Path(icon_path).exists():
                    button.setIcon(QtGui.QIcon(icon_path))
                button.setIconSize(QtCore.QSize(48, 48))
                button.clicked.connect(lambda _, it=item: self.launch_item(it))
                layout.addWidget(button)
            layout.addStretch()

            scroll = QtWidgets.QScrollArea()
            scroll.setWidget(widget)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

            self.tabs.addTab(scroll, section.get("name", ""))

        # Add settings tab with embedded config editor
        self.config_editor.reload()
        self.tabs.addTab(self.config_editor, "Settings")

    # --- actions ---
    def launch_item(self, item: Dict[str, Any]) -> None:
        """Run command or open URL depending on item type."""
        typ = item.get("type")
        cmd = item.get("command")
        if not cmd:
            return
        if typ == "url":
            webbrowser.open(cmd)
        else:
            subprocess.Popen(cmd, shell=True)

    def add_item(self) -> None:
        if not self.sections:
            QtWidgets.QMessageBox.warning(self, "No Sections", "Please add a section first.")
            return
        idx = self._select_section("Add Item", "Select section")
        if idx is None:
            return
        dlg = ItemDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections[idx].setdefault("items", []).append(dlg.get_data().__dict__)
            save_config(self.sections)
            self.reload_items()

    def edit_item(self) -> None:
        if not self.sections:
            return
        sec_idx = self._select_section("Edit Item", "Select section")
        if sec_idx is None or not self.sections[sec_idx].get("items"):
            return
        names = [it.get("name", "") for it in self.sections[sec_idx]["items"]]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Edit Item", "Select item", names, 0, False)
        if ok and item:
            idx = names.index(item)
            current = ItemData(**self.sections[sec_idx]["items"][idx])
            dlg = ItemDialog(self, current)
            if dlg.exec() == QtWidgets.QDialog.Accepted:
                self.sections[sec_idx]["items"][idx] = dlg.get_data().__dict__
                save_config(self.sections)
                self.reload_items()

    def remove_item(self) -> None:
        if not self.sections:
            return
        sec_idx = self._select_section("Remove Item", "Select section")
        if sec_idx is None or not self.sections[sec_idx].get("items"):
            return
        names = [it.get("name", "") for it in self.sections[sec_idx]["items"]]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Remove Item", "Select item", names, 0, False)
        if ok and item:
            idx = names.index(item)
            del self.sections[sec_idx]["items"][idx]
            save_config(self.sections)
            self.reload_items()

    def _select_section(self, title: str, label: str) -> int | None:
        names = [sec.get("name", "") for sec in self.sections]
        section, ok = QtWidgets.QInputDialog.getItem(self, title, label, names, 0, False)
        if ok and section:
            return names.index(section)
        return None
