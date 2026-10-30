"""Backend cleanup logic for ClearSpace.

This module contains no graphical-interface code, so it can be tested or
reused independently from the CustomTkinter application.
"""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path


# These are the only root folders the application is allowed to clean.
TARGET_DIRECTORIES = (
    Path(r"C:\Windows\Prefetch"),
    Path(r"C:\Windows\Temp"),
    Path(r"C:\Users\rishi\AppData\Local\Temp"),
)
CUSTOM_DIRECTORIES_FILE = Path(__file__).with_name("custom_directories.json")
LOGS_FILE = Path(__file__).with_name("logs.json")
APPLICATION_NAME = "ClearSpace"
APPLICATION_VERSION = "1.0"
REPARSE_POINT_ATTRIBUTE = 0x0400
_LOG_LOCK = threading.RLock()


@dataclass
class CleanupResult:
    """Files/folders removed successfully and items that could not be removed."""

    deleted: list[Path]
    failed: list[tuple[Path, OSError]]
    files_deleted: int = 0
    space_reclaimed_bytes: int = 0


@dataclass
class DirectoryPreview:
    """Read-only cleanup statistics for one selected directory."""

    directory: Path
    files: int
    bytes: int
    directories: int
    inaccessible: int


@dataclass
class PreviewResult:
    """Read-only statistics collected from all selected directories."""

    directories: list[DirectoryPreview]
    inaccessible: int

    @property
    def files(self) -> int:
        return sum(item.files for item in self.directories)

    @property
    def bytes(self) -> int:
        return sum(item.bytes for item in self.directories)

    @property
    def directories_scanned(self) -> int:
        return sum(item.directories for item in self.directories)


def _new_log_document() -> dict[str, object]:
    """Create the stable top-level structure used by ``logs.json``."""
    return {
        "application": APPLICATION_NAME,
        "version": APPLICATION_VERSION,
        "logs": [],
    }


def _load_log_document() -> dict[str, object]:
    """Load logs safely, retaining corrupted content in the new JSON document."""
    if not LOGS_FILE.exists():
        return _new_log_document()

    try:
        raw = LOGS_FILE.read_text(encoding="utf-8")
        document = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        try:
            raw = LOGS_FILE.read_text(encoding="utf-8", errors="replace")
        except OSError:
            raw = ""
        document = _new_log_document()
        document["recovery"] = {
            "message": "Previous logs.json content could not be parsed.",
            "error": str(error),
            "content": raw,
        }
        return document

    if not isinstance(document, dict):
        document = _new_log_document()
        document["recovery"] = {
            "message": "Previous logs.json did not contain a JSON object.",
            "content": raw,
        }
        return document

    logs = document.get("logs")
    if not isinstance(logs, list):
        document["logs"] = []
    document.setdefault("application", APPLICATION_NAME)
    document.setdefault("version", APPLICATION_VERSION)
    return document


def _write_log_document(document: dict[str, object]) -> None:
    """Atomically replace logs.json so interrupted writes cannot corrupt it."""
    LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=LOGS_FILE.parent,
            prefix=f"{LOGS_FILE.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            json.dump(document, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, LOGS_FILE)
        temporary_path = None
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def log_event(
    level: str,
    event: str,
    message: str,
    *,
    directory: Path | None = None,
    details: dict[str, object] | None = None,
) -> bool:
    """Append one structured event without allowing logging to crash the app."""
    if level not in {"INFO", "WARNING", "ERROR", "DEBUG"}:
        level = "ERROR"
        message = f"Invalid log level supplied. Original message: {message}"
        event = "LOGGING_ERROR"

    entry: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        "message": message,
    }
    if directory is not None:
        entry["directory"] = str(directory)
    if details:
        entry["details"] = details

    try:
        with _LOG_LOCK:
            document = _load_log_document()
            logs = document.setdefault("logs", [])
            if not isinstance(logs, list):
                logs = []
                document["logs"] = logs
            if "recovery" in document:
                logs.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": "ERROR",
                        "event": "JSON_LOGGING_ERROR",
                        "message": "Previous logs.json content was recovered.",
                        "details": document["recovery"],
                    }
                )
            logs.append(entry)
            document.pop("recovery", None)
            _write_log_document(document)
        return True
    except Exception:
        # Logging must never become the reason the cleaner stops working.
        return False


def _is_reparse_point(path: Path) -> bool:
    """Return whether a path is a symlink or Windows reparse point."""
    try:
        if path.is_symlink():
            return True
        attributes = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & REPARSE_POINT_ATTRIBUTE)


def analyze_directory(directory: Path) -> DirectoryPreview:
    """Scan one directory without modifying any filesystem data."""
    files = 0
    total_bytes = 0
    directories = 0
    inaccessible = 0

    if not directory.is_dir() or _is_reparse_point(directory):
        return DirectoryPreview(directory, 0, 0, 0, 1)

    def scan(folder: Path) -> None:
        nonlocal files, total_bytes, directories, inaccessible
        directories += 1
        try:
            entries = list(folder.iterdir())
        except OSError:
            inaccessible += 1
            return

        for entry in entries:
            if _is_reparse_point(entry):
                inaccessible += 1
                continue
            try:
                if entry.is_dir():
                    scan(entry)
                elif entry.is_file():
                    files += 1
                    total_bytes += entry.stat(follow_symlinks=False).st_size
            except OSError:
                inaccessible += 1

    scan(directory)
    return DirectoryPreview(
        directory, files, total_bytes, directories, inaccessible
    )


def analyze_directories(directories: list[Path]) -> PreviewResult:
    """Analyze selected directories without deleting, moving, or changing files."""
    previews = [analyze_directory(directory) for directory in directories]
    result = PreviewResult(previews, sum(item.inaccessible for item in previews))
    log_event(
        "INFO",
        "CLEANUP_PREVIEW_COMPLETED",
        "Cleanup preview completed.",
        details={
            "files_detected": result.files,
            "space_reclaimable_bytes": result.bytes,
            "directories_scanned": result.directories_scanned,
            "inaccessible_items": result.inaccessible,
        },
    )
    return result


def format_bytes(size: int) -> str:
    """Format a byte count using a compact human-readable unit."""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return "0 B"


def validate_cleanup_directory(directory: Path) -> str | None:
    """Return a user-facing error for an unsafe or invalid cleanup directory."""
    if not directory.is_dir():
        return "The selected path is not an existing folder."
    try:
        resolved = directory.resolve()
        if resolved == Path(resolved.anchor):
            return "A drive root cannot be added."
        windows_root = Path(os.environ.get("WINDIR", r"C:\Windows")).resolve()
        if resolved in (windows_root, windows_root / "System32", windows_root / "SysWOW64"):
            return "This protected Windows system folder cannot be added."
    except OSError as error:
        return f"The folder could not be validated: {error}"
    return None





def load_custom_directories() -> list[Path]:
    """Load user-added folders, ignoring invalid or duplicated entries."""
    if not CUSTOM_DIRECTORIES_FILE.is_file():
        return []
    try:
        values = json.loads(CUSTOM_DIRECTORIES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        log_event(
            "WARNING",
            "CUSTOM_DIRECTORIES_LOAD_FAILED",
            "Custom directories could not be loaded.",
            details={"error": str(error)},
        )
        return []
    if not isinstance(values, list):
        return []
    directories: list[Path] = []
    for value in values:
        if isinstance(value, str):
            directory = Path(value)
            if directory not in TARGET_DIRECTORIES and directory not in directories:
                directories.append(directory)
    return directories


def save_custom_directories(directories: list[Path]) -> None:
    """Persist user-added folders for the next application launch."""
    CUSTOM_DIRECTORIES_FILE.write_text(
        json.dumps([str(directory) for directory in directories], indent=2),
        encoding="utf-8",
    )


def is_admin() -> bool:
    """Return whether the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def request_admin(script_path: Path | None = None) -> bool:
    """Ask Windows to relaunch the application with administrator privileges."""
    if is_admin():
        return True

    try:
        # Relaunch the same script through Windows UAC ("run as administrator").
        executable = script_path or Path(__file__).resolve()
        arguments = subprocess.list2cmdline(
            [str(executable.resolve()), *sys.argv[1:]]
        )
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            arguments,
            str(executable.resolve().parent),
            1,
        )
    except (AttributeError, OSError):
        return False

    return result > 32


def clean_directory(directory: Path) -> CleanupResult:
    """Remove all contents in a directory while preserving its root folder."""
    deleted: list[Path] = []
    failed: list[tuple[Path, OSError]] = []
    deleted_files = 0
    reclaimed_bytes = 0

    validation_error = validate_cleanup_directory(directory)
    if validation_error:
        failed.append((directory, OSError(validation_error)))
        log_event(
            "WARNING",
            "CLEANUP_DIRECTORY_REJECTED",
            "Cleanup directory rejected by safety validation.",
            directory=directory,
            details={"error": validation_error},
        )
        return CleanupResult(deleted, failed)

    def remove_contents(folder: Path) -> None:
        nonlocal deleted_files, reclaimed_bytes
        # Read one folder at a time so nested folders can be handled recursively.
        try:
            entries = list(folder.iterdir())
        except OSError as error:
            failed.append((folder, error))
            return

        for entry in entries:
            if entry.is_dir() and not _is_reparse_point(entry):
                # Clean a subfolder before removing it, leaving the selected
                # root directory untouched.
                remove_contents(entry)
                try:
                    entry.rmdir()
                    deleted.append(entry)
                except OSError as error:
                    failed.append((entry, error))
                continue

            try:
                file_size = (
                    entry.stat(follow_symlinks=False).st_size
                    if entry.is_file()
                    else 0
                )
                entry.unlink()
                deleted.append(entry)
                deleted_files += 1
                reclaimed_bytes += file_size
            except OSError as error:
                failed.append((entry, error))

    if not directory.is_dir():
        error = OSError("folder not found")
        failed.append((directory, error))
        log_event(
            "WARNING",
            "CLEANUP_DIRECTORY_FAILED",
            "Cleanup directory was not found.",
            directory=directory,
            details={"error": str(error)},
        )
        return CleanupResult(deleted, failed)

    remove_contents(directory)
    return CleanupResult(deleted, failed, deleted_files, reclaimed_bytes)
