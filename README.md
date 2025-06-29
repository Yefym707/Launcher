# Custom Launcher for Ubuntu

This project is a simple customizable launcher written in Python using
[PySide6](https://doc.qt.io/qtforpython/).

## Features

- **Horizontal panel** with icons and names for each item.
- **Organize items into tabs** for different sections.
- **Configurable** via external YAML file (`config.yaml`).
- Launch applications, scripts and open URLs.
- Edit items directly from the application or by modifying `config.yaml`.

## Installation

1. Install Python 3.8+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the launcher from the repository root. The application starts hidden in
the system tray to keep your desktop uncluttered. Click the tray icon to
toggle a slim panel at the top of the screen:

```bash
python -m launcher.main
```

The launcher reads `config.yaml` located in the project root. Modify this
file to change sections, buttons, icons and commands.

### Editing within the app

Use the **Configure** options in the tray icon menu or open the **Settings**
tab to manage sections and items without editing YAML manually. The Settings
tab presents an interactive list where you can add, edit and remove sections
or items. Changes are saved back to `config.yaml` and the UI can be reloaded
from the same menu.

## Configuration file format

```yaml
sections:
  - name: Applications
    items:
      - name: Firefox
        type: application
        command: firefox
        icon: /usr/share/icons/hicolor/48x48/apps/firefox.png
      - name: Terminal
        type: application
        command: gnome-terminal
  - name: Scripts
    items:
      - name: Update Script
        type: script
        command: /home/user/update.sh
  - name: Websites
    items:
      - name: Open GitHub
        type: url
        command: https://github.com
```

Each item has:

- `name`: label shown in the UI.
- `type`: one of `application`, `script` or `url`.
- `command`: command to run or URL to open.
- `icon` (optional): path to an icon image.

Each section has:

- `name`: section title displayed in the launcher.
- `items`: list of items within the section.

## Extending

New buttons can be added by editing `config.yaml` or via the **Add Item**
option in the launcher menu. To customize behaviour or appearance, modify
files in the `launcher/` package.

## License

MIT
