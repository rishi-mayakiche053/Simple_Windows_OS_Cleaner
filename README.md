# ClearSpace

### A lightweight Windows cleaner built with Python and CustomTkinter

[![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/Interface-CustomTkinter-245C9C?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)

ClearSpace previews and cleans selected Windows folders through a responsive
dashboard.

> [!WARNING]
> **Deletion is permanent.** Files are not moved to the Recycle Bin and there
> is no undo function. Always review the selected locations and preview before
> continuing.

---

## Features

- Preview files, sizes, warnings, and directory breakdowns before deletion.
- Clean built-in or custom folders recursively while preserving their roots.
- Skip inaccessible, locked, symbolic-link, and other reparse-point items.
- Cancel cleanup safely while keeping the interface responsive.
- Use UAC elevation when available, with safe standard-mode fallback.
- Reject drive roots and protected Windows, user-profile, Users, and Program
  Files locations.
- Use normalized paths and atomic configuration/log writes.
- Use a modern dark, scrollable dashboard with grouped locations, status
  animation, availability labels, hover feedback, and safe Exit controls.
- Use `Ctrl+P` for preview, `Escape` to cancel/close, and `Enter` to continue.
- View, filter, copy, or save deleted and skipped-item reports.
- Default window size: `760x890`.

## Cleaning locations

ClearSpace offers these default locations:

- `C:\Windows\Prefetch`
- `C:\Windows\Temp`
- `%LOCALAPPDATA%\Temp`

The local temporary folder uses the current user's `%LOCALAPPDATA%`, with a
`Path.home()` fallback.

You can add custom folders through the interface. Custom selections are saved
in `custom_directories.json`, and removing a custom folder from the list does
not delete its contents.

## Requirements

- Windows
- Python 3.9 or newer
- Tkinter
- CustomTkinter

Install the required package:

```powershell
python -m pip install customtkinter
```

Tkinter is normally included with Windows Python. Check it with:

```powershell
python -c "import tkinter; print('Tkinter is installed')"
```

## Installation and launch

From the project directory, run:

```powershell
python -m pip install customtkinter
python os_cleaner.py
```

ClearSpace may request UAC elevation. If refused, it continues in standard
mode, but some protected files may not be removable.

## How to use

1. Select the locations you want to clean.
2. Add custom locations if needed.
3. Click **Preview cleanup** or press `Ctrl+P`.
4. Review the file count, potential space reclaimed, warnings, and directory
   breakdown.
5. Click **Continue to cleanup** to begin deletion, or **Cancel** to return.
6. Use **Cancel cleanup** or press `Escape` to request cancellation during an
   active cleanup.
7. Open **View last report** to inspect, filter, copy, or save the results.
8. Use **Exit** to close the application safely.

The preview is read-only, and ClearSpace performs a fresh cleanup pass after
confirmation because files may change.

## Testing

Run the automated tests from the project directory:

```powershell
python -m unittest discover -s tests -v
```

Tests cover path detection, root preservation, safety validation, duplicate
handling, atomic writes, administrator relaunch, cancellation, reparse-point
protection, and log recovery.

## Project structure

| File or folder | Purpose |
|---|---|
| `cleaner.py` | Cleanup engine, safety validation, logging, and persistence |
| `ui.py` | CustomTkinter dashboard and application controls |
| `os_cleaner.py` | Application launcher |
| `tests/` | Automated backend tests |
| `custom_directories.json` | Saved custom cleanup locations |
| `logs.json` | Generated structured activity history |
| `requirements.md` | Installation guide |
| `diagram organisation.md` | Original project planning notes |
| `new_changes_list.txt` | Detailed implementation change history |
| `README_updated_draft.md` | Draft documentation containing the latest changes |

## Logging

ClearSpace stores structured activity history in `logs.json`, including
timestamps, levels, events, messages, operation details, cancellations, and
errors. Logs are created automatically and written atomically.

## Safety limitations

- Deletion is permanent.
- Deleted files are not moved to the Recycle Bin.
- Locked or inaccessible files may be skipped.
- Files can change between preview and cleanup.
- Cancellation stops before the next item; the current filesystem operation
  may finish first.
- The application should not be force-terminated during cleanup.

## License

ClearSpace is a personal project created for learning and experimentation.

Use it carefully and review the selected folders before starting a cleanup.
