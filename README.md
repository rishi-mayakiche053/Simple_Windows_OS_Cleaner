# ClearSpace

### A lightweight Windows cleaner built with Python and CustomTkinter

[![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/Interface-CustomTkinter-245C9C?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)

ClearSpace is a personal project designed to clean selected Windows temporary directories through a modern dark interface.

It lets you manage cleaning locations, monitor the process and review the results.

> [!WARNING]
> **Deletion is permanent.** Files are not moved to the Recycle Bin, and there is no undo function. Always review your selected folders before cleaning.

---

## ✨ Features

- Modern dark interface with blue accents.
- Select built-in or custom cleaning locations.
- Add and remove custom folders.
- Recursive file and folder cleanup.
- Background processing to keep the interface responsive.
- Read-only cleanup preview with file-count and size statistics.
- Directory-by-directory preview breakdown before deletion.
- Animated progress and status feedback.
- Administrator privileges through Windows UAC.
- Cleanup reports showing deleted and skipped items.
- Persistent structured activity history in `logs.json`.

## 📁 Cleaning locations

ClearSpace offers these default locations:

- `C:\Windows\Prefetch`
- `C:\Windows\Temp`
- `%LOCALAPPDATA%\Temp`

You can also add your own folders.

**The selected root directories are preserved.** Only their contents are targeted.

Custom folder selections are saved in `custom_directories.json`.

## 📦 Installation

**Requirements:** Windows, Python and CustomTkinter.

Install the required package:

```powershell
python -m pip install customtkinter
```

Launch ClearSpace:

```powershell
python os_cleaner.py
```

## ▶️ How to use

1. Select the folders you want to clean.
2. Add custom locations if needed.
3. Click **Preview cleanup**.
4. Review the read-only analysis.
5. Click **Continue to cleanup** or **Cancel**.
6. Open **Deleted files** to inspect the results.

Some protected or currently used files may be skipped. Administrator access can help with restricted locations.

The preview never deletes, moves, or changes files. Its values are
informational: ClearSpace performs a fresh cleanup pass after confirmation
because files may change between analysis and deletion.

## 🧩 Project structure

| File | Purpose |
|---|---|
| `cleaner.py` | Cleanup engine and backend operations |
| `ui.py` | CustomTkinter interface and application controls |
| `os_cleaner.py` | Application launcher |
| `requirements.md` | Installation guide |
| `diagram organisation.md` | Original project planning notes |

The launcher connects the interface to the backend, keeping the project organized into separate files.

## 📝 JSON logging

ClearSpace stores structured application history in the single JSON file
`logs.json` next to the application files. The file is created automatically
when the first event is recorded.

Logged events include application startup and shutdown, administrator status,
preview start and completion, cleanup start and completion, custom-folder
changes, and unexpected or logging errors. Cleanup results are kept in the
single completion event rather than duplicated across separate deleted/skipped
events.

Each entry includes an ISO 8601 timestamp, log level, event name, message, and
optional directory and operation details such as file counts, failure counts,
and reclaimed bytes.

The logger uses Python's built-in `json` module, a thread lock, and an atomic
temporary-file replacement. Missing or empty files are initialized safely. If
`logs.json` contains invalid JSON, the unreadable content is preserved in a
recoverable JSON `details` entry before normal logging continues. Logging
failures are isolated so they cannot crash the cleaner or freeze its UI.

## 🔒 Safety

- Deletion is permanent.
- Root folders are preserved.
- Locked or inaccessible files may be skipped.
- Custom folders can be removed from the list without deleting their contents.
- Cleanup requires explicit confirmation.

## 📄 License

ClearSpace is a personal project created for learning and experimentation.

Use it carefully and review the selected locations before starting a cleanup.