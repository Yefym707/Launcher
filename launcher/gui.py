"""Graphical user interface for the launcher."""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Any

from PySide6 import QtWidgets, QtGui, QtCore

# Application-wide style sheet for a clean minimalistic look with rounded
# corners. The palette uses light grays and subtle hover effects.
APP_STYLE = """
QWidget {
    background-color: #f5f5f5;
    font-family: Arial, sans-serif;
    font-size: 14px;
}
QToolBox::tab {
    background: #ffffff;
    border: 1px solid #cccccc;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-top: 2px;
    padding: 4px 8px;
}
QToolBox::tab:selected {
    background: #e6e6e6;
}
QToolButton {
    background: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 12px;
    padding: 6px;
}
QToolButton:hover {
    background: #f0f0f0;
}
QToolButton:pressed {
    background: #e0e0e0;
}
"""

from .config import load_config, save_config, CONFIG_PATH
from .dialogs import ItemDialog, ItemData, SectionDialog


class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Launcher")
        # Apply the global style sheet for a consistent minimalistic look
        self.setStyleSheet(APP_STYLE)
        # Make the window frameless and stay on top so it behaves more like a
        # popup launcher rather than a traditional application window.
        flags = (
            self.windowFlags()
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowFlags(flags)
        self.sections: List[Dict[str, Any]] = []
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.layout = QtWidgets.QVBoxLayout(self.central)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.tool_box = QtWidgets.QToolBox()
        self.tool_box.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.layout.addWidget(self.tool_box)

        self._create_menu()
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
        while self.tool_box.count():
            self.tool_box.removeItem(0)


        for section in self.sections:
            widget = QtWidgets.QWidget()
            grid = QtWidgets.QGridLayout(widget)
            grid.setSpacing(10)
            grid.setContentsMargins(0, 0, 0, 0)

            columns = 4
            row = col = 0
            for item in section.get("items", []):
                button = QtWidgets.QToolButton()
                button.setText(item.get("name", ""))
                button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
                icon_path = item.get("icon")
                if icon_path and Path(icon_path).exists():
                    button.setIcon(QtGui.QIcon(icon_path))
                button.setIconSize(QtCore.QSize(64, 64))
                button.clicked.connect(lambda _, it=item: self.launch_item(it))
                grid.addWidget(button, row, col)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1

            self.tool_box.addItem(widget, section.get("name", ""))

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
