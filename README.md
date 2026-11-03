# ClearSpace

### A lightweight Windows cleaner built with Python and CustomTkinter

[![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/Interface-CustomTkinter-245C9C?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)

ClearSpace previews and cleans selected Windows folders through a modern, responsive dashboard.

> [!WARNING]
> **Deletion is permanent.** Files are not moved to the Recycle Bin and cannot be restored through ClearSpace. Always review the preview before continuing.

---

## Features

- Preview files, sizes, and directory breakdowns before deletion.
- Clean built-in and custom folders recursively.
- Skip inaccessible files, symbolic links, and reparse points.
- Cancel active cleanup using the **Cancel cleanup** button.
- Use administrator privileges through UAC when available.
- Validate paths to protect important system directories.
- View, filter, copy, and save cleanup reports.
- Modern dark interface with progress feedback and animations.
- Keyboard shortcuts: `Ctrl+P` (preview), `Escape` (cancel), `Enter` (confirm).
- Default window size: `760x890`.

## Cleaning locations

Default folders:

- `C:\Windows\Prefetch`
- `C:\Windows\Temp`
- `%LOCALAPPDATA%\Temp`

Custom folders can be added through the interface and are saved automatically.

## Requirements and installation

- Windows
- Python 3.9+
- Tkinter and CustomTkinter

Install and launch:

```powershell
python -m pip install customtkinter
python os_cleaner.py
```

**Important:** Always launch ClearSpace using `os_cleaner.py`.

## How to use

1. Select the folders to clean.
2. Click **Preview cleanup**.
3. Review the files and estimated space to reclaim.
4. Click **Continue to cleanup** to proceed.
5. Use **Cancel cleanup** to request cancellation during an operation.
6. Open **View last report** to inspect the results.

The preview is read-only. A fresh scan is performed before deletion.

## Configuration and logs

ClearSpace automatically creates and maintains:

| File | Purpose |
|---|---|
| `custom_directories.json` | Saves custom cleanup locations. |
| `logs.json` | Stores activity, cleanup history, cancellations, and errors. |

Both files use atomic writes to reduce the risk of data corruption.

## Testing

Run the automated tests:

```powershell
python -m unittest discover -s tests -v
```

## Project structure

| File or folder | Purpose |
|---|---|
| `cleaner.py` | Cleanup engine and safety checks. |
| `ui.py` | Graphical interface. |
| `os_cleaner.py` | Application launcher. |
| `requirements.md` | Installation guide. |
| `diagram organisation.md` | Project planning notes. |

## Safety

- Deletion is permanent.
- Locked or inaccessible files may be skipped.
- Files may change between preview and cleanup.
- Cancellation takes effect after the current filesystem operation finishes.
- Avoid force-closing the application during cleanup.

## License

ClearSpace is a personal project created for learning and experimentation.
