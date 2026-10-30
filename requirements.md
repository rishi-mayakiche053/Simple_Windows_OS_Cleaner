# Installation guide

This project uses Python's built-in modules and one external package.

## Required modules

### CustomTkinter

CustomTkinter provides the modern widgets, rounded buttons, dark theme, and
progress bar used by the graphical interface.

Install it with:

```powershell
python -m pip install customtkinter
```

### Tkinter

Tkinter provides the base graphical interface and is included with the
standard Windows Python installer. It normally does not require a separate
installation.

To check that Tkinter is available:

```powershell
python -c "import tkinter; print('Tkinter is installed')"
```

If that command fails, reinstall Python from
[python.org](https://www.python.org/downloads/windows/) and make sure the
standard library is included.

## Install everything

From the project directory, run:

```powershell
python -m pip install customtkinter
```

The other imported modules are part of Python's standard library and require
no additional packages:

- `ctypes`
- `dataclasses`
- `os`
- `pathlib`
- `queue`
- `subprocess`
- `sys`
- `threading`

## Start the application

```powershell
python os_cleaner.py
```
