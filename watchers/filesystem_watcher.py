"""
Filesystem Watcher
──────────────────
Monitors a target directory for new or modified files using watchdog.
Writes task files into AI_Employee_Vault/Inbox/ when events are detected.

Setup:
  pip install watchdog
  Set WATCH_PATH in .env (defaults to ./watched_folder)
"""

import os
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from utils.config import ROOT_DIR
from utils.logger import get_logger
from utils.vault_io import write_inbox_task

log = get_logger("watcher.filesystem")

WATCH_PATH = Path(os.getenv("WATCH_PATH", str(ROOT_DIR / "watched_folder")))
IGNORE_EXTENSIONS = {".tmp", ".swp", ".DS_Store", ""}
IGNORE_PREFIXES = {".", "~"}


def _should_ignore(path: Path) -> bool:
    return (
        path.suffix in IGNORE_EXTENSIONS
        or any(path.name.startswith(p) for p in IGNORE_PREFIXES)
    )


class VaultEventHandler(FileSystemEventHandler):
    """Handle watchdog events and write tasks to Inbox."""

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if _should_ignore(path):
            return
        log.info(f"File created: {path.name}")
        write_inbox_task(
            title=f"New file detected: {path.name}",
            source="filesystem_watcher",
            body=(
                f"A new file was detected in the watched folder.\n\n"
                f"**Path:** `{path}`\n"
                f"**Size:** {path.stat().st_size if path.exists() else 'unknown'} bytes\n\n"
                f"Please review this file and determine if any action is required."
            ),
            priority="LOW",
            metadata={"file_path": str(path), "event": "created"},
        )

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if _should_ignore(path):
            return
        log.info(f"File modified: {path.name}")
        write_inbox_task(
            title=f"File modified: {path.name}",
            source="filesystem_watcher",
            body=(
                f"An existing file was modified in the watched folder.\n\n"
                f"**Path:** `{path}`\n\n"
                f"Please review the changes and determine if any action is required."
            ),
            priority="LOW",
            metadata={"file_path": str(path), "event": "modified"},
        )

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(str(event.src_path))
        if _should_ignore(path):
            return
        log.warning(f"File deleted: {path.name}")
        write_inbox_task(
            title=f"File deleted: {path.name}",
            source="filesystem_watcher",
            body=(
                f"A file was deleted from the watched folder.\n\n"
                f"**Path:** `{path}`\n\n"
                f"**Action Required:** Verify this deletion was intentional."
            ),
            priority="HIGH",
            metadata={"file_path": str(path), "event": "deleted"},
        )


def start_filesystem_watcher(watch_path: Path = WATCH_PATH) -> None:
    watch_path.mkdir(parents=True, exist_ok=True)
    handler = VaultEventHandler()
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=True)
    observer.start()
    log.info(f"Watching: {watch_path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_filesystem_watcher()
