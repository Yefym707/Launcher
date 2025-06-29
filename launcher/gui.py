"""Graphical user interface for the launcher."""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Any

from PySide6 import QtWidgets, QtGui, QtCore

from .config import load_config, save_config, CONFIG_PATH
from .dialogs import ItemDialog, ItemData


class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Launcher")
        self.items: List[Dict[str, Any]] = []
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.grid = QtWidgets.QGridLayout(self.central)
        self.grid.setSpacing(10)

        self._create_menu()
        self.reload_items()

    def _create_menu(self) -> None:
        menubar = self.menuBar()
        config_menu = menubar.addMenu("Config")

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

    def reload_items(self) -> None:
        """Reload items from configuration and rebuild UI."""
        self.items = load_config()
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        columns = 4
        row = col = 0
        for item in self.items:
            button = QtWidgets.QToolButton()
            button.setText(item.get("name", ""))
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            icon_path = item.get("icon")
            if icon_path and Path(icon_path).exists():
                button.setIcon(QtGui.QIcon(icon_path))
            button.setIconSize(QtCore.QSize(64, 64))
            button.clicked.connect(lambda _, it=item: self.launch_item(it))
            self.grid.addWidget(button, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

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
        dlg = ItemDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.items.append(dlg.get_data().__dict__)
            save_config(self.items)
            self.reload_items()

    def edit_item(self) -> None:
        if not self.items:
            return
        names = [it.get("name", "") for it in self.items]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Edit Item", "Select item", names, 0, False)
        if ok and item:
            idx = names.index(item)
            current = ItemData(**self.items[idx])
            dlg = ItemDialog(self, current)
            if dlg.exec() == QtWidgets.QDialog.Accepted:
                self.items[idx] = dlg.get_data().__dict__
                save_config(self.items)
                self.reload_items()

    def remove_item(self) -> None:
        if not self.items:
            return
        names = [it.get("name", "") for it in self.items]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Remove Item", "Select item", names, 0, False)
        if ok and item:
            idx = names.index(item)
            del self.items[idx]
            save_config(self.items)
            self.reload_items()
