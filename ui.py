"""CustomTkinter user interface for ClearSpace."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from cleaner import (
    TARGET_DIRECTORIES,
    CleanupResult,
    PreviewResult,
    analyze_directories,
    clean_directory,
    format_bytes,
    is_admin,
    load_custom_directories,
    log_event,
    request_admin,
    save_custom_directories,
    validate_cleanup_directory,
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CleanerApp(ctk.CTk):
    """Modern animated interface for the Windows cleaner."""

    # Keeping colors together makes the visual style easy to adjust.
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
        # Set the window size before building the layout.
        self.title("ClearSpace")
        self.geometry("760x700")
        self.minsize(680, 620)
        self.configure(fg_color=self.BG)

        self.running = False
        self.animation_step = 0
        # Worker-thread results are passed back safely through this queue.
        self.results: queue.Queue[tuple[str, object]] = queue.Queue()
        self.folder_records: list[
            tuple[Path, ctk.BooleanVar, ctk.CTkFrame, bool]
        ] = []
        self.custom_directories = load_custom_directories()
        self.last_result: CleanupResult | None = None
        self.last_preview: PreviewResult | None = None

        self._build_header()
        self._build_folder_section()
        self._build_actions()
        self._build_status()
        self._build_report_button()
        self._animate_header()
        self._animate_ui()

    def _build_header(self) -> None:
        # The header identifies the program and shows the current privilege mode.
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
        # Each location gets its own card and checkbox so users can choose
        # exactly which roots to clean.
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
        ctk.CTkButton(
            title_row,
            text="+ Add folder",
            width=105,
            height=28,
            corner_radius=14,
            fg_color=self.CARD,
            hover_color=self.CARD_HOVER,
            text_color=self.SUCCESS,
            command=self._add_folder,
        ).pack(side="right", padx=(0, 8))
        ctk.CTkButton(
            title_row,
            text="− Remove folder",
            width=115,
            height=28,
            corner_radius=14,
            fg_color=self.CARD,
            hover_color=self.CARD_HOVER,
            text_color=self.WARNING,
            command=self._remove_folder,
        ).pack(side="right", padx=(0, 8))

        self.folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.folder_frame.pack(fill="x", padx=36)
        self._rebuild_folder_cards()

    def _rebuild_folder_cards(self) -> None:
        """Refresh folder cards after a user adds or removes a location."""
        for _, _, card, _ in self.folder_records:
            card.destroy()
        self.folder_records.clear()
        for directory in (*TARGET_DIRECTORIES, *self.custom_directories):
            variable = ctk.BooleanVar(value=True)
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
            self.folder_records.append(
                (directory, variable, card, directory not in TARGET_DIRECTORIES)
            )

    def _add_folder(self) -> None:
        """Let the user choose and persist a custom cleanup folder."""
        directory = filedialog.askdirectory(title="Choose a folder to clean")
        if not directory:
            return
        selected = Path(directory)
        validation_error = validate_cleanup_directory(selected)
        if validation_error:
            messagebox.showwarning("Folder cannot be added", validation_error)
            return
        if selected in TARGET_DIRECTORIES or selected in self.custom_directories:
            messagebox.showinfo("Folder already added", "That folder is already in the list.")
            return
        self.custom_directories.append(selected)
        try:
            save_custom_directories(self.custom_directories)
        except OSError as error:
            self.custom_directories.remove(selected)
            log_event(
                "ERROR",
                "CUSTOM_DIRECTORY_ADD_FAILED",
                "Custom directory could not be saved.",
                directory=selected,
                details={"error": str(error)},
            )
            messagebox.showerror("Could not save folder", str(error))
            return
        self._rebuild_folder_cards()
        log_event(
            "INFO",
            "CUSTOM_DIRECTORY_ADDED",
            "Custom directory added to the cleaning list.",
            directory=selected,
        )
        self.status.configure(text="Folder added", text_color=self.SUCCESS)

    def _remove_folder(self) -> None:
        """Remove the selected custom folder from the list without deleting it."""
        selected = next(
            (
                directory
                for directory, variable, _, is_custom in self.folder_records
                if is_custom and variable.get()
            ),
            None,
        )
        if selected is None:
            messagebox.showinfo(
                "Select a custom folder",
                "Select a custom folder first. Built-in folders cannot be removed.",
            )
            return
        self.custom_directories.remove(selected)
        try:
            save_custom_directories(self.custom_directories)
        except OSError as error:
            self.custom_directories.append(selected)
            log_event(
                "ERROR",
                "CUSTOM_DIRECTORY_REMOVE_FAILED",
                "Custom directory could not be removed from the list.",
                directory=selected,
                details={"error": str(error)},
            )
            messagebox.showerror("Could not save folder list", str(error))
            return
        self._rebuild_folder_cards()
        log_event(
            "INFO",
            "CUSTOM_DIRECTORY_REMOVED",
            "Custom directory removed from the cleaning list.",
            directory=selected,
        )
        self.status.configure(text="Folder removed from the list", text_color=self.WARNING)

    def _build_actions(self) -> None:
        # Preview is the only entry point to cleanup; deletion starts only
        # after the user reviews and accepts the read-only analysis.
        self.clean_button = ctk.CTkButton(
            self,
            text="◌  Preview cleanup",
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
        # These labels provide immediate feedback without opening a console.
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

    def _build_report_button(self) -> None:
        self.report_button = ctk.CTkButton(
            self,
            text="⌕  Deleted files",
            height=34,
            corner_radius=17,
            fg_color="transparent",
            hover_color=self.CARD_HOVER,
            text_color=self.ACCENT,
            state="disabled",
            command=self._show_deleted_files,
        )
        self.report_button.pack(pady=(15, 0))

    def _select_all(self) -> None:
        # Toggle all checkboxes together instead of forcing one fixed state.
        new_value = not all(variable.get() for _, variable, _, _ in self.folder_records)
        for _, variable, _, _ in self.folder_records:
            variable.set(new_value)

    def _selected_directories(self) -> list[Path]:
        """Return the locations currently selected in the interface."""
        return [
            directory
            for directory, variable, _, _ in self.folder_records
            if variable.get()
        ]

    def _confirm_cleanup(self) -> None:
        """Start a read-only preview instead of deleting immediately."""
        selected = self._selected_directories()
        if not selected:
            messagebox.showwarning("No locations selected", "Select at least one location.")
            return
        invalid = [
            f"{directory}: {validate_cleanup_directory(directory)}"
            for directory in selected
            if validate_cleanup_directory(directory)
        ]
        if invalid:
            messagebox.showwarning(
                "Location unavailable",
                "Preview could not start:\n\n" + "\n".join(invalid),
            )
            return
        self._start_preview(selected)

    def _start_preview(self, directories: list[Path]) -> None:
        """Analyze selected folders in a worker thread."""
        log_event(
            "INFO",
            "CLEANUP_PREVIEW_STARTED",
            "Cleanup preview started.",
            details={"directory_count": len(directories)},
        )
        self.running = True
        self.last_preview = None
        self.last_result = None
        self.report_button.configure(state="disabled")
        self.clean_button.configure(state="disabled", text="Analyzing…")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status.configure(text="Analyzing selected locations…", text_color=self.ACCENT)
        threading.Thread(
            target=self._preview_worker,
            args=(directories,),
            daemon=True,
        ).start()
        self.after(100, self._poll_results)

    def _preview_worker(self, directories: list[Path]) -> None:
        """Run the read-only backend analysis away from the GUI thread."""
        try:
            preview = analyze_directories(directories)
        except Exception as error:
            log_event(
                "ERROR",
                "UNEXPECTED_EXCEPTION",
                "Unexpected exception during cleanup preview.",
                details={"operation": "preview", "error": str(error)},
            )
            self.results.put(("error", f"Analysis failed: {error}"))
            return
        self.results.put(("preview", preview))

    def _show_preview(self, preview: PreviewResult) -> None:
        """Display actual analysis results and the cleanup decision buttons."""
        window = ctk.CTkToplevel(self)
        window.title("Cleanup preview")
        window.geometry("760x650")
        window.minsize(620, 520)
        window.configure(fg_color=self.BG)
        window.transient(self)
        window.grab_set()

        ctk.CTkLabel(
            window,
            text="Cleanup preview",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.TEXT,
        ).pack(anchor="w", padx=30, pady=(24, 2))
        ctk.CTkLabel(
            window,
            text="Read-only analysis • nothing has been deleted",
            font=ctk.CTkFont(size=13),
            text_color=self.SUCCESS,
        ).pack(anchor="w", padx=30, pady=(0, 18))

        stats = ctk.CTkFrame(window, fg_color="transparent")
        stats.pack(fill="x", padx=24)
        self._preview_stat(stats, "FILES DETECTED", str(preview.files), self.SUCCESS)
        self._preview_stat(
            stats,
            "POTENTIAL SPACE RECLAIMED",
            format_bytes(preview.bytes),
            self.ACCENT,
        )

        breakdown_card = ctk.CTkFrame(
            window, fg_color=self.CARD, corner_radius=18
        )
        breakdown_card.pack(fill="both", expand=True, padx=24, pady=18)
        ctk.CTkLabel(
            breakdown_card,
            text="Directory breakdown",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=self.TEXT,
        ).pack(anchor="w", padx=20, pady=(18, 8))
        for item in preview.directories:
            row = ctk.CTkFrame(breakdown_card, fg_color=self.CARD_HOVER, corner_radius=10)
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(
                row,
                text=item.directory.name or str(item.directory),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.TEXT,
                anchor="w",
            ).pack(side="left", padx=14, pady=10)
            ctk.CTkLabel(
                row,
                text=f"{item.files} files  •  {format_bytes(item.bytes)}",
                font=ctk.CTkFont(size=12),
                text_color=self.MUTED,
            ).pack(side="right", padx=14)

        ctk.CTkLabel(
            window,
            text=f"Directories scanned: {preview.directories_scanned}  •  "
            f"Items not analyzed: {preview.inaccessible}",
            font=ctk.CTkFont(size=12),
            text_color=self.MUTED,
        ).pack(anchor="w", padx=30)
        ctk.CTkLabel(
            window,
            text="Preview values are informational. Files may change before cleanup.",
            font=ctk.CTkFont(size=11),
            text_color=self.WARNING,
        ).pack(anchor="w", padx=30, pady=(5, 12))

        actions = ctk.CTkFrame(window, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=(0, 24))
        ctk.CTkButton(
            actions,
            text="Cancel",
            height=42,
            corner_radius=21,
            fg_color=self.CARD,
            hover_color=self.CARD_HOVER,
            command=window.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Continue to cleanup",
            height=42,
            corner_radius=21,
            fg_color=self.ACCENT,
            hover_color="#78a0ff",
            command=lambda: self._continue_cleanup(window),
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _preview_stat(
        self, parent: ctk.CTkFrame, label: str, value: str, color: str
    ) -> None:
        """Create one large dashboard statistic card."""
        card = ctk.CTkFrame(parent, fg_color=self.CARD, corner_radius=18)
        card.pack(side="left", fill="both", expand=True, padx=6)
        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.MUTED,
        ).pack(anchor="w", padx=18, pady=(16, 0))
        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color,
        ).pack(anchor="w", padx=18, pady=(2, 16))

    def _continue_cleanup(self, preview_window: ctk.CTkToplevel) -> None:
        """Close the preview and begin a fresh deletion pass."""
        if self.last_preview is None:
            preview_window.destroy()
            return
        directories = [item.directory for item in self.last_preview.directories]
        preview_window.destroy()
        self._start_cleanup(directories)

    def _start_cleanup(self, directories: list[Path]) -> None:
        """Run the real cleanup after the preview has been explicitly accepted."""
        selected = [
            directory for directory in directories if directory.is_dir()
        ]
        if not selected:
            messagebox.showwarning("No locations selected", "Select at least one location.")
            return
        log_event(
            "INFO",
            "CLEANUP_STARTED",
            "Cleanup operation started after preview confirmation.",
            details={"directories": [str(directory) for directory in selected]},
        )
        # Indeterminate progress is used because the total number of entries
        # is unknown until each directory has been scanned.
        self.running = True
        self.last_result = None
        self.report_button.configure(state="disabled")
        self.clean_button.configure(state="disabled", text="Cleaning…")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status.configure(text="Preparing cleanup…", text_color=self.ACCENT)
        # A daemon thread keeps the interface responsive during filesystem I/O.
        threading.Thread(
            target=self._cleanup_worker,
            args=(selected,),
            daemon=True,
        ).start()
        self.after(100, self._poll_results)

    def _cleanup_worker(self, directories: list[Path]) -> None:
        # This method must not update Tkinter widgets directly; it only
        # collects results and sends them to the main thread.
        deleted: list[Path] = []
        failed: list[tuple[Path, OSError]] = []
        files_deleted = 0
        space_reclaimed_bytes = 0
        try:
            for directory in directories:
                result = clean_directory(directory)
                deleted.extend(result.deleted)
                failed.extend(result.failed)
                files_deleted += result.files_deleted
                space_reclaimed_bytes += result.space_reclaimed_bytes
        except Exception as error:
            log_event(
                "ERROR",
                "UNEXPECTED_EXCEPTION",
                "Unexpected exception during cleanup.",
                details={"operation": "cleanup", "error": str(error)},
            )
            self.results.put(("error", f"Cleanup failed: {error}"))
            return
        self.results.put(
            (
                "cleanup",
                CleanupResult(
                    deleted,
                    failed,
                    files_deleted,
                    space_reclaimed_bytes,
                ),
            )
        )

    def _poll_results(self) -> None:
        # Tkinter's event loop polls the queue instead of blocking the window.
        try:
            event, payload = self.results.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_results)
            return

        if event == "preview" and isinstance(payload, PreviewResult):
            self.running = False
            self.last_preview = payload
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self.progress.set(1)
            self.clean_button.configure(state="normal", text="◌  Preview cleanup")
            self.status.configure(text="Preview ready", text_color=self.SUCCESS)
            self._show_preview(payload)
        elif event == "cleanup" and isinstance(payload, CleanupResult):
            self._finish_cleanup(payload)
        elif event == "error":
            self.running = False
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self.clean_button.configure(state="normal", text="◌  Preview cleanup")
            self.status.configure(text="Operation failed", text_color=self.WARNING)
            messagebox.showerror("Operation error", payload)

    def _finish_cleanup(self, result: CleanupResult) -> None:
        # All final UI updates happen on the Tkinter main thread.
        self.running = False
        self.last_result = result
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1 if not result.failed else 0.7)
        self.clean_button.configure(state="normal", text="◌  Preview cleanup")
        self.status.configure(
            text="Cleanup complete"
            if not result.failed
            else "Cleanup complete with warnings",
            text_color=self.SUCCESS if not result.failed else self.WARNING,
        )
        self.summary.configure(
            text=f"{len(result.deleted)} item(s) deleted  •  "
            f"{len(result.failed)} item(s) skipped"
        )
        cleanup_details: dict[str, object] = {
            "files_deleted": result.files_deleted,
            "items_deleted": len(result.deleted),
            "space_reclaimed_bytes": result.space_reclaimed_bytes,
            "failed_items": len(result.failed),
        }
        if result.failed:
            cleanup_details["failed_operations"] = [
                {
                    "path": str(path),
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
                for path, error in result.failed
            ]
        log_event(
            "INFO" if not result.failed else "WARNING",
            "CLEANUP_COMPLETED",
            "Cleanup operation completed.",
            details=cleanup_details,
        )

        details = "\n".join(
            f"{number}. {path}"
            for number, path in enumerate(result.deleted, start=1)
        )
        if not details:
            details = "No files or folders were deleted."
        if result.failed:
            details += "\n\nSkipped:\n" + "\n".join(
                f"• {path}: {error}" for path, error in result.failed
            )
        self.report_button.configure(state="normal")
        self.status.configure(text="Cleanup complete — report ready", text_color=self.SUCCESS)

    def _show_deleted_files(self) -> None:
        """Open the optional modern report window after a cleanup."""
        if self.last_result is None:
            return
        report = ctk.CTkToplevel(self)
        report.title("Deleted files")
        report.geometry("720x560")
        report.minsize(560, 400)
        report.configure(fg_color=self.BG)
        report.transient(self)

        ctk.CTkLabel(
            report,
            text="Deleted files",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.TEXT,
        ).pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(
            report,
            text=f"{len(self.last_result.deleted)} item(s) deleted  •  "
            f"{len(self.last_result.failed)} skipped",
            font=ctk.CTkFont(size=13),
            text_color=self.MUTED,
        ).pack(anchor="w", padx=28, pady=(0, 16))
        textbox = ctk.CTkTextbox(
            report,
            corner_radius=14,
            fg_color=self.CARD,
            text_color=self.TEXT,
            font=ctk.CTkFont(size=12),
            wrap="word",
        )
        textbox.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        lines = "\n".join(
            f"{number}. {path}"
            for number, path in enumerate(self.last_result.deleted, start=1)
        )
        if not lines:
            lines = "No files or folders were deleted."
        if self.last_result.failed:
            lines += "\n\nSkipped:\n" + "\n".join(
                f"• {path}: {error}" for path, error in self.last_result.failed
            )
        textbox.insert("1.0", lines)
        textbox.configure(state="disabled")
        ctk.CTkButton(
            report,
            text="Close",
            width=120,
            height=38,
            corner_radius=19,
            fg_color=self.ACCENT,
            hover_color="#78a0ff",
            command=report.destroy,
        ).pack(pady=(0, 24))

    def _animate_header(self) -> None:
        # Schedule a small animation repeatedly without blocking the GUI.
        if self.running:
            self.animation_step = (self.animation_step + 1) % 4
            self.status.configure(text="Cleaning" + "." * self.animation_step)
        self.after(350, self._animate_header)

    def _animate_ui(self) -> None:
        """Pulse the primary action and subtitle for subtle visual motion."""
        if not self.running:
            shade = "#5b8cff" if self.animation_step % 2 == 0 else "#688fff"
            self.clean_button.configure(fg_color=shade)
        self.animation_step += 1
        self.after(900, self._animate_ui)

    def _on_close(self) -> None:
        """Record shutdown before closing the application window."""
        log_event("INFO", "APPLICATION_SHUTDOWN", "ClearSpace is shutting down.")
        self.destroy()


def main() -> None:
    """Launch the graphical cleaner."""
    # The app can still open without elevation, but protected files may fail.
    if os.name != "nt":
        messagebox.showwarning("Windows only", "This program is intended for Windows.")
    if not is_admin():
        request_admin(Path(__file__).with_name("os_cleaner.py"))
    app = CleanerApp()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
