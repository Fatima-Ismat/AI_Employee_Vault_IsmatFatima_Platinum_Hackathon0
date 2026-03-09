"""
Filesystem MCP Server
──────────────────────
Model Context Protocol tool for local file operations.

All writes go to a sandboxed output directory to prevent accidental
modification of system or project files.
"""

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from utils.config import ROOT_DIR
from utils.logger import get_logger

log = get_logger("mcp.filesystem")

OUTPUT_DIR = Path(os.getenv("FS_OUTPUT_DIR", str(ROOT_DIR / "agent_outputs")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Public MCP Tool Functions ─────────────────────────────────────────────────

def write_file(filename: str, content: str, subdir: str = "") -> dict:
    """
    Write content to a file in the sandboxed output directory.

    Args:
        filename: Filename (basename only — no path traversal)
        content: Text content to write
        subdir: Optional subdirectory within output dir

    Returns:
        {"success": bool, "path": str}
    """
    # Sanitize filename to prevent path traversal
    safe_name = Path(filename).name
    target_dir = OUTPUT_DIR / subdir if subdir else OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name

    try:
        target_path.write_text(content, encoding="utf-8")
        log.info(f"File written: {target_path}")
        return {"success": True, "path": str(target_path)}
    except Exception as e:
        log.error(f"Failed to write file {safe_name}: {e}")
        return {"success": False, "path": str(e)}


def read_file(filepath: str) -> dict:
    """
    Read a file's content.

    Args:
        filepath: Absolute or relative path to the file

    Returns:
        {"success": bool, "content": str, "size": int}
    """
    try:
        path = Path(filepath)
        if not path.is_absolute():
            path = ROOT_DIR / filepath
        content = path.read_text(encoding="utf-8")
        log.info(f"File read: {path}")
        return {"success": True, "content": content, "size": len(content)}
    except FileNotFoundError:
        return {"success": False, "content": "", "size": 0}
    except Exception as e:
        log.error(f"Failed to read file {filepath}: {e}")
        return {"success": False, "content": str(e), "size": 0}


def list_files(directory: str = "", pattern: str = "*") -> list[dict]:
    """
    List files in a directory.

    Args:
        directory: Directory path (defaults to output dir)
        pattern: Glob pattern

    Returns:
        List of {"name": str, "size": int, "modified": str}
    """
    try:
        target = Path(directory) if directory else OUTPUT_DIR
        if not target.is_absolute():
            target = ROOT_DIR / directory
        results = []
        for f in sorted(target.glob(pattern)):
            if f.is_file():
                stat = f.stat()
                results.append({
                    "name":     f.name,
                    "path":     str(f),
                    "size":     stat.st_size,
                    "modified": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                })
        return results
    except Exception as e:
        log.error(f"Failed to list files in {directory}: {e}")
        return []


def delete_file(filepath: str, require_in_output: bool = True) -> dict:
    """
    Delete a file. By default only allows deleting files inside the output dir.

    Args:
        filepath: Path to delete
        require_in_output: Safety check — only delete files in OUTPUT_DIR

    Returns:
        {"success": bool, "message": str}
    """
    try:
        path = Path(filepath)
        if not path.is_absolute():
            path = OUTPUT_DIR / path.name

        if require_in_output and OUTPUT_DIR not in path.parents and path.parent != OUTPUT_DIR:
            msg = f"Safety check: {path} is outside output dir — deletion blocked"
            log.warning(msg)
            return {"success": False, "message": msg}

        path.unlink(missing_ok=True)
        log.info(f"File deleted: {path}")
        return {"success": True, "message": f"Deleted {path.name}"}
    except Exception as e:
        log.error(f"Failed to delete {filepath}: {e}")
        return {"success": False, "message": str(e)}


def copy_file(src: str, dest: str) -> dict:
    """
    Copy a file within the output directory.

    Returns:
        {"success": bool, "destination": str}
    """
    try:
        src_path  = Path(src)
        dest_path = OUTPUT_DIR / Path(dest).name
        shutil.copy2(str(src_path), str(dest_path))
        log.info(f"File copied: {src_path.name} → {dest_path}")
        return {"success": True, "destination": str(dest_path)}
    except Exception as e:
        log.error(f"Failed to copy file: {e}")
        return {"success": False, "destination": str(e)}
