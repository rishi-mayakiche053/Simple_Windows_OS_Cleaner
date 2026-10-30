"""Modern Windows temporary-file cleaner."""

from __future__ import annotations

import ctypes
import os
import queue
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk


TARGET_DIRECTORIES = (
    Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Prefetch",
    Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Temp",
    Path(r"C:\Users\rishi\AppData\Local\Temp"),
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


@dataclass
class CleanupResult:
    deleted: list[Path]
    failed: list[tuple[Path, OSError]]


def is_admin() -> bool:
    """Return whether the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def request_admin() -> bool:
    """Ask Windows to relaunch the application with administrator privileges."""
    if is_admin():
        return True

    try:
        arguments = subprocess.list2cmdline(
            [str(Path(__file__).resolve()), *sys.argv[1:]]
        )
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            arguments,
            str(Path(__file__).resolve().parent),
            1,
        )
    except (AttributeError, OSError):
        return False

    return result > 32


def clean_directory(directory: Path) -> CleanupResult:
    """Remove all contents in a directory while preserving its root folder."""
    deleted: list[Path] = []
    failed: list[tuple[Path, OSError]] = []

    def remove_contents(folder: Path) -> None:
        try:
            entries = list(folder.iterdir())
        except OSError as error:
            failed.append((folder, error))
            return

        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                remove_contents(entry)
                try:
                    entry.rmdir()
                    deleted.append(entry)
                except OSError as error:
                    failed.append((entry, error))
                continue

            try:
                entry.unlink()
                deleted.append(entry)
            except OSError as error:
                failed.append((entry, error))

    if not directory.is_dir():
        failed.append((directory, OSError("folder not found")))
        return CleanupResult(deleted, failed)

    remove_contents(directory)
    return CleanupResult(deleted, failed)


class CleanerApp(ctk.CTk):
    """Modern animated interface for the Windows cleaner."""

    BG = "#101318"
    CARD = "#191e27"
    CARD_HOVER = "#222a36"
    TEXT = "#f4f7fb"
    MUTED = "#9ca8b8"
    ACCENT = "#5b8cff"
    SUCCESS = "#4dd49a"
    WARNING = "#ffbd69"

    def __init__(self) -> None:
        super().__init__()
        self.title("ClearSpace")
        self.geometry("760x700")
        self.minsize(680, 620)
        self.configure(fg_color=self.BG)

        self.running = False
        self.animation_step = 0
        self.results: queue.Queue[tuple[str, object]] = queue.Queue()
        self.folder_vars: list[ctk.BooleanVar] = []
        self.folder_cards: list[ctk.CTkFrame] = []

        self._build_header()
        self._build_folder_section()
        self._build_actions()
        self._build_status()
        self._animate_header()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=36, pady=(30, 12))

        ctk.CTkLabel(
            header,
            text="ClearSpace",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.TEXT,
        ).pack(anchor="w")
        self.subtitle = ctk.CTkLabel(
            header,
            text="A cleaner, calmer Windows workspace",
            font=ctk.CTkFont(size=14),
            text_color=self.MUTED,
        )
        self.subtitle.pack(anchor="w", pady=(3, 0))

        self.admin_badge = ctk.CTkLabel(
            header,
            text="● Administrator mode" if is_admin() else "● Standard mode",
            corner_radius=12,
            padx=12,
            pady=5,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.SUCCESS if is_admin() else self.WARNING,
            fg_color="#17382e" if is_admin() else "#40301d",
        )
        self.admin_badge.pack(anchor="w", pady=(16, 0))

    def _build_folder_section(self) -> None:
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=36, pady=(18, 8))
        ctk.CTkLabel(
            title_row,
            text="Cleaning locations",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT,
        ).pack(side="left")
        ctk.CTkButton(
            title_row,
            text="Select all",
            width=90,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=self.CARD_HOVER,
            text_color=self.ACCENT,
            command=self._select_all,
        ).pack(side="right")

        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.pack(fill="x", padx=36)
        for directory in TARGET_DIRECTORIES:
            variable = ctk.BooleanVar(value=True)
            self.folder_vars.append(variable)
            card = ctk.CTkFrame(
                self.folder_frame,
                fg_color=self.CARD,
                corner_radius=16,
                height=68,
            )
            card.pack(fill="x", pady=5)
            card.pack_propagate(False)
            check = ctk.CTkCheckBox(
                card,
                text="",
                variable=variable,
                width=30,
                checkbox_width=22,
                checkbox_height=22,
                hover_color=self.ACCENT,
                fg_color=self.ACCENT,
            )
            check.pack(side="left", padx=(18, 5))
            text_frame = ctk.CTkFrame(card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, pady=10)
            ctk.CTkLabel(
                text_frame,
                text=directory.name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.TEXT,
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                text_frame,
                text=str(directory),
                font=ctk.CTkFont(size=11),
                text_color=self.MUTED,
                anchor="w",
            ).pack(anchor="w")
            self.folder_cards.append(card)

    def _build_actions(self) -> None:
        self.clean_button = ctk.CTkButton(
            self,
            text="✦  Clean selected locations",
            height=52,
            corner_radius=26,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.ACCENT,
            hover_color="#78a0ff",
            command=self._confirm_cleanup,
        )
        self.clean_button.pack(fill="x", padx=36, pady=(25, 10))

        self.progress = ctk.CTkProgressBar(
            self,
            height=5,
            corner_radius=3,
            progress_color=self.ACCENT,
            fg_color=self.CARD,
        )
        self.progress.pack(fill="x", padx=36)
        self.progress.set(0)

    def _build_status(self) -> None:
        self.status = ctk.CTkLabel(
            self,
            text="Ready when you are",
            font=ctk.CTkFont(size=13),
            text_color=self.MUTED,
        )
        self.status.pack(pady=(13, 3))
        self.summary = ctk.CTkLabel(
            self,
            text="Root folders are always preserved",
            font=ctk.CTkFont(size=11),
            text_color="#697688",
        )
        self.summary.pack()

    def _select_all(self) -> None:
        new_value = not all(variable.get() for variable in self.folder_vars)
        for variable in self.folder_vars:
            variable.set(new_value)

    def _confirm_cleanup(self) -> None:
        selected = [
            directory
            for directory, variable in zip(TARGET_DIRECTORIES, self.folder_vars)
            if variable.get()
        ]
        if not selected:
            messagebox.showwarning("No locations selected", "Select at least one location.")
            return

        locations = "\n".join(f"• {directory}" for directory in selected)
        confirmed = messagebox.askyesno(
            "Confirm cleanup",
            f"All contents inside these locations will be permanently deleted:\n\n"
            f"{locations}\n\nThe root folders will be preserved.",
            icon="warning",
        )
        if confirmed:
            self._start_cleanup(selected)

    def _start_cleanup(self, directories: list[Path]) -> None:
        self.running = True
        self.clean_button.configure(state="disabled", text="Cleaning…")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status.configure(text="Preparing cleanup…", text_color=self.ACCENT)
        threading.Thread(
            target=self._cleanup_worker,
            args=(directories,),
            daemon=True,
        ).start()
        self.after(100, self._poll_results)

    def _cleanup_worker(self, directories: list[Path]) -> None:
        deleted: list[Path] = []
        failed: list[tuple[Path, OSError]] = []
        for directory in directories:
            result = clean_directory(directory)
            deleted.extend(result.deleted)
            failed.extend(result.failed)
        self.results.put(("done", (deleted, failed)))

    def _poll_results(self) -> None:
        try:
            event, payload = self.results.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_results)
            return

        if event != "done":
            return
        deleted, failed = payload
        self._finish_cleanup(deleted, failed)

    def _finish_cleanup(
        self, deleted: list[Path], failed: list[tuple[Path, OSError]]
    ) -> None:
        self.running = False
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1 if not failed else 0.7)
        self.clean_button.configure(state="normal", text="✦  Clean selected locations")
        self.status.configure(
            text="Cleanup complete" if not failed else "Cleanup complete with warnings",
            text_color=self.SUCCESS if not failed else self.WARNING,
        )
        self.summary.configure(
            text=f"{len(deleted)} item(s) deleted  •  {len(failed)} item(s) skipped"
        )

        details = "\n".join(
            f"{number}. {path}" for number, path in enumerate(deleted, start=1)
        )
        if not details:
            details = "No files or folders were deleted."
        if failed:
            details += "\n\nSkipped:\n" + "\n".join(
                f"• {path}: {error}" for path, error in failed
            )
        messagebox.showinfo("Cleanup summary", details)

    def _animate_header(self) -> None:
        if self.running:
            self.animation_step = (self.animation_step + 1) % 4
            self.status.configure(text="Cleaning" + "." * self.animation_step)
        self.after(350, self._animate_header)


def main() -> None:
    """Launch the graphical cleaner."""
    if os.name != "nt":
        messagebox.showwarning("Windows only", "This program is intended for Windows.")
    if not is_admin() and not request_admin():
        pass
    app = CleanerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
