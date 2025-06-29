"""Dialogs used by the launcher."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from PySide6 import QtWidgets, QtGui


@dataclass
class ItemData:
    name: str
    type: str
    command: str
    icon: str | None = None


class ItemDialog(QtWidgets.QDialog):
    """Dialog to create or edit launcher items."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, data: ItemData | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Launcher Item")
        self._data = data

        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit(data.name if data else "")
        layout.addRow("Name", self.name_edit)

        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["application", "script", "url"])
        self.type_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.type_combo.setFixedHeight(24)
        self.type_combo.view().setFixedHeight(120)
        if data:
            index = self.type_combo.findText(data.type)
            self.type_combo.setCurrentIndex(max(0, index))
        layout.addRow("Type", self.type_combo)

        self.command_edit = QtWidgets.QLineEdit(data.command if data else "")
        layout.addRow("Command/URL", self.command_edit)

        self.icon_edit = QtWidgets.QLineEdit(data.icon if data and data.icon else "")
        icon_button = QtWidgets.QPushButton("Browse")
        icon_button.clicked.connect(self._select_icon)
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(icon_button)
        layout.addRow("Icon", icon_layout)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _select_icon(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Icon", "", "Images (*.png *.svg *.jpg *.jpeg *.bmp)")
        if path:
            self.icon_edit.setText(path)

    def get_data(self) -> ItemData:
        return ItemData(
            name=self.name_edit.text().strip(),
            type=self.type_combo.currentText(),
            command=self.command_edit.text().strip(),
            icon=self.icon_edit.text().strip() or None,
        )


class SectionDialog(QtWidgets.QDialog):
    """Dialog to create or edit sections."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, name: str = "", icon: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Section")

        layout = QtWidgets.QFormLayout(self)
        self.name_edit = QtWidgets.QLineEdit(name)
        layout.addRow("Name", self.name_edit)

        self.icon_edit = QtWidgets.QLineEdit(icon or "")
        icon_button = QtWidgets.QPushButton("Browse")
        icon_button.clicked.connect(self._select_icon)
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(icon_button)
        layout.addRow("Icon", icon_layout)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _select_icon(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Icon", "", "Images (*.png *.svg *.jpg *.jpeg *.bmp)")
        if path:
            self.icon_edit.setText(path)

    def get_name(self) -> str:
        return self.name_edit.text().strip()

    def get_icon(self) -> str | None:
        text = self.icon_edit.text().strip()
        return text or None


class ListSelectDialog(QtWidgets.QDialog):
    """Simple dialog with a combo box for selecting from a list."""

    def __init__(self, title: str, label: str, items: list[str], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(label))

        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(items)
        self.combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.combo.setFixedHeight(24)
        self.combo.view().setFixedHeight(120)
        layout.addWidget(self.combo)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def get_item(title: str, label: str, items: list[str], parent: QtWidgets.QWidget | None = None) -> tuple[str, bool]:
        dlg = ListSelectDialog(title, label, items, parent)
        ok = dlg.exec() == QtWidgets.QDialog.Accepted
        return dlg.combo.currentText(), ok
