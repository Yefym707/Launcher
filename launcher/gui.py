"""Graphical user interface for the launcher."""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Any, Callable, cast

import yaml

from PySide6 import QtWidgets, QtGui, QtCore

from .config import (
    load_config,
    save_config,
    CONFIG_PATH,
    load_theme,
    load_panel_geometry,
    save_panel_geometry,
)
from .dialogs import ItemDialog, ItemData, SectionDialog, ListSelectDialog


def load_stylesheet(theme: str) -> str:
    """Load QSS stylesheet from the ``styles`` directory."""
    path = Path(__file__).resolve().parent / "styles" / f"{theme}.qss"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


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


class ConfigManager(QtWidgets.QWidget):
    """Interactive interface to manage ``config.yaml`` without editing text."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.sections: List[Dict[str, Any]] = []

        layout = QtWidgets.QVBoxLayout(self)

        # --- section list ---
        sec_layout = QtWidgets.QHBoxLayout()
        self.section_list = QtWidgets.QListWidget()
        self.section_list.currentRowChanged.connect(self._show_items)
        self.section_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.section_list.model().rowsMoved.connect(self._sections_reordered)
        sec_buttons = QtWidgets.QVBoxLayout()
        self.add_section_btn = QtWidgets.QPushButton("Add")
        self.add_section_btn.clicked.connect(self._add_section)
        self.edit_section_btn = QtWidgets.QPushButton("Edit")
        self.edit_section_btn.clicked.connect(self._edit_section)
        self.remove_section_btn = QtWidgets.QPushButton("Remove")
        self.remove_section_btn.clicked.connect(self._remove_section)
        for b in (self.add_section_btn, self.edit_section_btn, self.remove_section_btn):
            sec_buttons.addWidget(b)
        sec_buttons.addStretch()
        sec_layout.addWidget(self.section_list, 1)
        sec_layout.addLayout(sec_buttons)

        # --- item list ---
        item_layout = QtWidgets.QHBoxLayout()
        self.item_list = QtWidgets.QListWidget()
        self.item_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.item_list.model().rowsMoved.connect(self._items_reordered)
        item_buttons = QtWidgets.QVBoxLayout()
        self.add_item_btn = QtWidgets.QPushButton("Add")
        self.add_item_btn.clicked.connect(self._add_item)
        self.edit_item_btn = QtWidgets.QPushButton("Edit")
        self.edit_item_btn.clicked.connect(self._edit_item)
        self.remove_item_btn = QtWidgets.QPushButton("Remove")
        self.remove_item_btn.clicked.connect(self._remove_item)
        for b in (self.add_item_btn, self.edit_item_btn, self.remove_item_btn):
            item_buttons.addWidget(b)
        item_buttons.addStretch()
        item_layout.addWidget(self.item_list, 1)
        item_layout.addLayout(item_buttons)

        # --- save/reload ---
        bottom_layout = QtWidgets.QHBoxLayout()
        self.reload_btn = QtWidgets.QPushButton("Reload")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.save)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.reload_btn)
        bottom_layout.addWidget(self.save_btn)

        layout.addLayout(sec_layout)
        layout.addLayout(item_layout)
        layout.addLayout(bottom_layout)

        self.reload()

    # --- data helpers ---
    def reload(self) -> None:
        self.sections = load_config()
        self.section_list.clear()
        for sec in self.sections:
            self.section_list.addItem(sec.get("name", ""))
        if self.section_list.count() > 0:
            self.section_list.setCurrentRow(0)

    def save(self) -> None:
        save_config(self.sections)

    def _show_items(self, idx: int) -> None:
        self.item_list.clear()
        if idx < 0 or idx >= len(self.sections):
            return
        for it in self.sections[idx].get("items", []):
            self.item_list.addItem(it.get("name", ""))

    # --- section actions ---
    def _add_section(self) -> None:
        dlg = SectionDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections.append({"name": dlg.get_name(), "icon": dlg.get_icon(), "items": []})
            self.section_list.addItem(dlg.get_name())
            self.section_list.setCurrentRow(self.section_list.count() - 1)

    def _edit_section(self) -> None:
        idx = self.section_list.currentRow()
        if idx < 0:
            return
        dlg = SectionDialog(self, self.sections[idx].get("name", ""), self.sections[idx].get("icon"))
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections[idx]["name"] = dlg.get_name()
            self.sections[idx]["icon"] = dlg.get_icon()
            self.section_list.item(idx).setText(dlg.get_name())

    def _remove_section(self) -> None:
        idx = self.section_list.currentRow()
        if idx < 0:
            return
        self.section_list.takeItem(idx)
        del self.sections[idx]
        self._show_items(self.section_list.currentRow())

    # --- item actions ---
    def _add_item(self) -> None:
        sec_idx = self.section_list.currentRow()
        if sec_idx < 0:
            return
        dlg = ItemDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections[sec_idx].setdefault("items", []).append(dlg.get_data().__dict__)
            self.item_list.addItem(dlg.get_data().name)

    def _edit_item(self) -> None:
        sec_idx = self.section_list.currentRow()
        item_idx = self.item_list.currentRow()
        if sec_idx < 0 or item_idx < 0:
            return
        current = ItemData(**self.sections[sec_idx]["items"][item_idx])
        dlg = ItemDialog(self, current)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections[sec_idx]["items"][item_idx] = dlg.get_data().__dict__
            self.item_list.item(item_idx).setText(dlg.get_data().name)

    def _remove_item(self) -> None:
        sec_idx = self.section_list.currentRow()
        item_idx = self.item_list.currentRow()
        if sec_idx < 0 or item_idx < 0:
            return
        self.item_list.takeItem(item_idx)
        del self.sections[sec_idx]["items"][item_idx]

    # --- reorder handlers ---
    def _sections_reordered(self, parent: QtCore.QModelIndex, start: int, end: int, dest: QtCore.QModelIndex, row: int) -> None:
        if start == row or start == row - 1:
            return
        moved = self.sections.pop(start)
        if row > start:
            row -= 1
        self.sections.insert(row, moved)

    def _items_reordered(self, parent: QtCore.QModelIndex, start: int, end: int, dest: QtCore.QModelIndex, row: int) -> None:
        sec_idx = self.section_list.currentRow()
        if sec_idx < 0:
            return
        items = self.sections[sec_idx].setdefault("items", [])
        if start == row or start == row - 1:
            return
        moved = items.pop(start)
        if row > start:
            row -= 1
        items.insert(row, moved)


class CollapsibleSection(QtWidgets.QWidget):
    """Simple collapsible container with animation."""

    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.toggle_button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.clicked.connect(self._on_toggled)

        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self._anim = QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        self._anim.setDuration(200)

    def setContentLayout(self, layout: QtWidgets.QLayout) -> None:
        w = QtWidgets.QWidget()
        w.setLayout(layout)
        self.content_area.setWidget(w)
        self._anim.setEndValue(w.sizeHint().height())

    def _on_toggled(self) -> None:
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
        end = self.content_area.widget().sizeHint().height() if checked else 0
        self._anim.stop()
        self._anim.setEndValue(end)
        self._anim.start()


class DropdownSection(QtWidgets.QWidget):
    """Section that shows its items in a popup menu outside the main window."""

    def __init__(
        self,
        title: str,
        items: List[Dict[str, Any]],
        trigger: Callable[[Dict[str, Any]], None],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._items = items
        self._trigger = trigger

        self.button = QtWidgets.QToolButton(text=title)
        self.button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.button.setArrowType(QtCore.Qt.DownArrow)
        self.button.clicked.connect(self._toggle_menu)

        self._menu: QtWidgets.QMenu | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if obj is self._menu and event.type() == QtCore.QEvent.MouseButtonPress:
            pos = cast(QtGui.QMouseEvent, event).globalPos()
            if self.button.rect().contains(self.button.mapFromGlobal(pos)):
                self._menu.close()
                return True
        return super().eventFilter(obj, event)

    def _toggle_menu(self) -> None:
        """Show the dropdown menu or hide it if already visible."""
        if self._menu and self._menu.isVisible():
            self._menu.close()
            return

        menu = QtWidgets.QMenu(self)
        menu.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        menu.installEventFilter(self)
        for item in self._items:
            action = QtGui.QAction(item.get("name", ""), menu)
            icon_path = item.get("icon")
            if icon_path and Path(icon_path).exists():
                action.setIcon(QtGui.QIcon(icon_path))
            action.triggered.connect(lambda _, it=item: self._trigger(it))
            menu.addAction(action)

        pos = self.button.mapToGlobal(QtCore.QPoint(0, self.button.height()))
        menu.popup(pos)
        menu.aboutToHide.connect(lambda: setattr(self, "_menu", None))
        self._menu = menu


class LauncherWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Launcher")
        self.setWindowFlags(
            self.windowFlags()
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )

        self.setStyleSheet(load_stylesheet(load_theme()))
        x, y = load_panel_geometry()
        self.move(x, y)

        self._drag_pos: QtCore.QPoint | None = None

        self.sections: List[Dict[str, Any]] = []

        # central widget that will contain all collapsible sections
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.layout = QtWidgets.QHBoxLayout(central)
        # leave a small gap of 5px above and below the section buttons
        self.layout.setContentsMargins(8, 5, 8, 5)
        self.section_widgets: List[QtWidgets.QWidget] = []

        self._create_menu()
        self.menuBar().hide()
        self.reload_items()

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

        theme_action = QtGui.QAction("Toggle Theme", self)
        theme_action.triggered.connect(self._toggle_theme)
        config_menu.addAction(theme_action)

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
        menu.addAction("Toggle Theme", self._toggle_theme)
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
            anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(200)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.finished.connect(self.hide)
            anim.start()
            self._fade = anim
        else:
            self.setWindowOpacity(0.0)
            self.show()
            anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
            anim.setDuration(200)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()
            self._fade = anim

    def add_section(self) -> None:
        dlg = SectionDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections.append({"name": dlg.get_name(), "icon": dlg.get_icon(), "items": []})
            save_config(self.sections)
            self.reload_items()

    def edit_section(self) -> None:
        if not self.sections:
            return
        idx = self._select_section("Edit Section", "Select section")
        if idx is None:
            return
        dlg = SectionDialog(self, self.sections[idx].get("name", ""), self.sections[idx].get("icon"))
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.sections[idx]["name"] = dlg.get_name()
            self.sections[idx]["icon"] = dlg.get_icon()
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
        for w in self.section_widgets:
            self.layout.removeWidget(w)
            w.deleteLater()
        self.section_widgets.clear()

        for section in self.sections:
            sec = DropdownSection(
                section.get("name", ""),
                section.get("items", []),
                self.launch_item,
            )
            self.layout.addWidget(sec)
            self.section_widgets.append(sec)

        # settings section appended after all user defined sections
        settings_section = DropdownSection(
            "Settings",
            [{"name": "Open Settings"}],
            lambda _item: self._open_settings(),
        )
        self.layout.addWidget(settings_section)
        self.section_widgets.append(settings_section)

        self.adjustSize()
        # match window height to the button height plus 5px padding on top and bottom
        if self.section_widgets:
            btn_h = self.section_widgets[0].button.sizeHint().height()
            self.setFixedHeight(btn_h + 10)

    # --- actions ---
    def launch_item(self, item: Dict[str, Any]) -> None:
        """Run command or open URL depending on item type."""
        typ = item.get("type")
        cmd = item.get("command")
        if not cmd:
            return
        try:
            if typ == "url":
                ok = webbrowser.open(cmd)
                if not ok:
                    raise RuntimeError("Unable to open URL")
            else:
                subprocess.Popen(cmd, shell=True)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Launch Failed",
                f"Failed to launch {item.get('name', '')}: {exc}",
            )

    def _open_settings(self) -> None:
        """Show the configuration manager in a popup dialog."""
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        layout = QtWidgets.QVBoxLayout(dlg)
        editor = ConfigManager(dlg)
        layout.addWidget(editor)
        editor.reload()
        dlg.exec()
        self.reload_items()


    def _toggle_theme(self) -> None:
        current = load_theme()
        new = "light" if current == "dark" else "dark"
        data = {}
        if CONFIG_PATH.exists():
            data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        data["theme"] = new
        CONFIG_PATH.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        self.setStyleSheet(load_stylesheet(new))

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
        item, ok = ListSelectDialog.get_item("Edit Item", "Select item", names, self)
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
        item, ok = ListSelectDialog.get_item("Remove Item", "Select item", names, self)
        if ok and item:
            idx = names.index(item)
            del self.sections[sec_idx]["items"][idx]
            save_config(self.sections)
            self.reload_items()

    def _select_section(self, title: str, label: str) -> int | None:
        names = [sec.get("name", "") for sec in self.sections]
        section, ok = ListSelectDialog.get_item(title, label, names, self)
        if ok and section:
            return names.index(section)
        return None

    # --- drag handling ---
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._drag_pos is not None:
            self._drag_pos = None
            save_panel_geometry(self.x(), self.y())
        super().mouseReleaseEvent(event)
