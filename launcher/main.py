"""Entry point for the launcher."""

from PySide6 import QtWidgets

from .gui import LauncherWindow


def main() -> None:
    app = QtWidgets.QApplication([])
    window = LauncherWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
