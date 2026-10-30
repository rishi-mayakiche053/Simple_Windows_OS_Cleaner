# 🧹 ClearSpace — Simple Windows OS Cleaner

> **A modern, animated Windows temporary-file cleaner built with Python and
> CustomTkinter.**

ClearSpace removes the contents of selected Windows temporary directories while
keeping the three main directories themselves. It provides a dark modern
interface, rounded controls, animated status feedback, confirmation dialogs,
and a numbered cleanup summary.

---

## 🟢 Important things to know / Requirements

### ⚠️ Quick summary

- **Windows + Python** are required.
- Install the interface package:

```powershell
python -m pip install customtkinter
```

- Tkinter is included with standard Python; no separate installation is
  normally needed.
- The cleaner permanently deletes contents, not the three root folders.
- It can clean `Prefetch`, `Windows\Temp`, and the user's temporary folder.
- Administrator access may be needed for protected files.
- Locked files are skipped and reported.

Start it with:

```powershell
python os_cleaner.py
```

---

## ✨ Main features

- **Modern dark interface** with blue accent colors and rounded controls.
- **Animated cleanup state** with a responsive progress indicator.
- **Non-blocking cleanup** using a background worker thread.
- **Folder selection cards** with individual checkboxes.
- **Select all** control for quick cleanup.
- **Confirmation dialog** before permanent deletion.
- **Administrator-mode badge** showing the current privilege level.
- **Numbered result report** listing every successfully deleted file and folder.
- **Failure report** showing items that could not be deleted and the reason.
- **Root-folder protection** so the configured root folders remain available.

---

## 🔧 Advanced Informations

### Cleanup behavior

The `clean_directory()` function receives one root directory and:

1. Checks whether the directory exists.
2. Reads its contents.
3. Recursively enters normal subfolders.
4. Deletes files and symbolic links with `unlink()`.
5. Removes subfolders after their contents have been removed.
6. Keeps the selected root directory untouched.
7. Records successful deletions in a list.
8. Records `OSError` failures instead of stopping the complete cleanup.

Symbolic-link directories are not traversed as normal folders. This prevents
the cleaner from following a link outside the selected Windows directory.

### Deletion and recovery

The program uses Python's `Path.unlink()` and `Path.rmdir()` methods. These
perform direct filesystem deletion:

- Deleted files do **not** go to the Recycle Bin.
- The application does not provide an undo function.
- A locked file may remain if Windows or another application is using it.
- The final dialog reports every successful deletion and every skipped item.

Review the selected locations carefully before confirming a cleanup.

### Administrator elevation

The application checks Windows administrator status with
`ctypes.windll.shell32.IsUserAnAdmin()`. If administrator privileges are not
available, it requests elevation with Windows UAC by calling
`ShellExecuteW(..., "runas", ...)`.

If elevation is cancelled, the application can still open in standard mode.
Some protected files may then be skipped.

### Interface and animation

The interface is built with `customtkinter` and uses:

- `CTk` for the application window.
- `CTkFrame` for layout cards.
- `CTkCheckBox` for folder selection.
- `CTkButton` for rounded modern actions.
- `CTkProgressBar` for animated cleanup feedback.
- Tkinter's `after()` scheduler for lightweight status animation.

No separate animation package is required.

### Threading model

Filesystem cleanup runs in a daemon background thread so the interface remains
responsive. Results are transferred safely to the GUI thread through
`queue.Queue`. Tkinter widgets are updated only by the main GUI thread.

### Python standard-library modules

These modules are included with Python and do not need to be installed:

```text
ctypes
dataclasses
os
pathlib
queue
subprocess
sys
threading
tkinter
```

Only `customtkinter` is an external dependency.

### Troubleshooting

#### `ModuleNotFoundError: No module named 'customtkinter'`

Install the package using the same Python interpreter used to start the
program:

```powershell
python -m pip install customtkinter
```

#### Tkinter cannot be imported

Reinstall Python from [python.org](https://www.python.org/downloads/windows/)
and make sure the standard library and Tcl/Tk components are included.

#### Some files cannot be deleted

This is expected when files are locked, protected, or currently in use. Close
the application using the file, run ClearSpace as administrator, and try again.

#### The application does not start with administrator privileges

Right-click PowerShell or Command Prompt, select **Run as administrator**, then
launch the program again:

```powershell
python os_cleaner.py
```

### Project files

| File | Purpose |
|---|---|
| [`os_cleaner.py`](os_cleaner.py) | Main graphical application and cleanup logic |
| [`requirements.md`](requirements.md) | Installation and dependency guide |
| [`diagram organisation.md`](diagram%20organisation.md) | Original project organization notes |

---

## 📄 License and project status

This is a personal project created for learning and experimentation. Review
the code and the selected paths before using it on an important computer.
