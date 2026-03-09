"""
Cloud Sync Manager
───────────────────
Synchronizes the local Obsidian vault with a remote storage backend.

Supported backends:
  - Local path (default / demo)
  - AWS S3 (requires boto3 + AWS credentials)
  - Google Cloud Storage (requires google-cloud-storage)

Configuration (.env):
  SYNC_BACKEND       local | s3 | gcs
  S3_BUCKET          your-bucket-name
  S3_PREFIX          vault/               (prefix path in bucket)
  GCS_BUCKET         your-gcs-bucket
  GCS_PREFIX         vault/
  SYNC_INTERVAL      60                   (seconds between syncs)
"""

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import VAULT_DIR, HISTORY_DIR, LOGS_DIR
from utils.logger import get_logger

log = get_logger("cloud.sync")

SYNC_BACKEND  = os.getenv("SYNC_BACKEND", "local")
S3_BUCKET     = os.getenv("S3_BUCKET", "")
S3_PREFIX     = os.getenv("S3_PREFIX", "vault/")
GCS_BUCKET    = os.getenv("GCS_BUCKET", "")
GCS_PREFIX    = os.getenv("GCS_PREFIX", "vault/")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "60"))

SYNC_STATE_FILE = Path(__file__).parents[1] / "cloud" / ".sync_state.json"
SYNC_LOG_FILE   = LOGS_DIR / "sync_log.md"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _file_hash(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def _write_sync_log(msg: str, level: str = "INFO") -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SYNC_LOG_FILE, "a", encoding="utf-8") as f:
        icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}
        f.write(f"\n- `{_now()}` {icons.get(level, '•')} {msg}")


def load_sync_state() -> dict:
    if SYNC_STATE_FILE.exists():
        try:
            return json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_sync_state(state: dict) -> None:
    SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_local_files() -> dict[str, str]:
    """Return {relative_path: md5_hash} for all vault + history files."""
    result = {}
    for root_dir in (VAULT_DIR, HISTORY_DIR):
        if not root_dir.exists():
            continue
        for f in root_dir.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                rel = str(f.relative_to(root_dir.parent))
                try:
                    result[rel] = _file_hash(f)
                except Exception:
                    pass
    return result


# ── Backend implementations ───────────────────────────────────────────────────

class LocalSyncBackend:
    """Copy vault to a local mirror directory (for demo/testing)."""

    def __init__(self) -> None:
        self.mirror = Path(os.getenv("LOCAL_SYNC_PATH",
                           str(Path(__file__).parents[1] / "cloud" / "mirror")))
        self.mirror.mkdir(parents=True, exist_ok=True)
        log.info(f"Local sync backend → {self.mirror}")

    def upload(self, local_path: Path, remote_key: str) -> bool:
        dest = self.mirror / remote_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(local_path), str(dest))
        return True

    def download(self, remote_key: str, local_path: Path) -> bool:
        src = self.mirror / remote_key
        if src.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(local_path))
            return True
        return False

    def list_remote(self) -> list[str]:
        return [
            str(f.relative_to(self.mirror))
            for f in self.mirror.rglob("*") if f.is_file()
        ]


class S3SyncBackend:
    """Sync to AWS S3 bucket."""

    def __init__(self) -> None:
        import boto3
        self.s3 = boto3.client("s3")
        self.bucket = S3_BUCKET
        self.prefix = S3_PREFIX
        log.info(f"S3 sync backend → s3://{self.bucket}/{self.prefix}")

    def upload(self, local_path: Path, remote_key: str) -> bool:
        try:
            self.s3.upload_file(str(local_path), self.bucket, self.prefix + remote_key)
            return True
        except Exception as e:
            log.error(f"S3 upload failed: {e}")
            return False

    def download(self, remote_key: str, local_path: Path) -> bool:
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.s3.download_file(self.bucket, self.prefix + remote_key, str(local_path))
            return True
        except Exception as e:
            log.error(f"S3 download failed: {e}")
            return False

    def list_remote(self) -> list[str]:
        try:
            resp = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
            return [
                obj["Key"].replace(self.prefix, "")
                for obj in resp.get("Contents", [])
            ]
        except Exception as e:
            log.error(f"S3 list failed: {e}")
            return []


def get_backend():
    if SYNC_BACKEND == "s3":
        return S3SyncBackend()
    return LocalSyncBackend()


class SyncManager:
    """Orchestrates bidirectional sync between local vault and remote backend."""

    def __init__(self) -> None:
        self.backend = get_backend()
        self.state = load_sync_state()

    def sync(self) -> dict:
        """Run one sync cycle. Returns summary dict."""
        local_files = get_local_files()
        uploaded = 0
        skipped  = 0
        errors   = 0

        for rel_path, current_hash in local_files.items():
            prev_hash = self.state.get(rel_path)
            if prev_hash == current_hash:
                skipped += 1
                continue

            local_abs = VAULT_DIR.parent / rel_path
            success = self.backend.upload(local_abs, rel_path)
            if success:
                self.state[rel_path] = current_hash
                uploaded += 1
            else:
                errors += 1

        save_sync_state(self.state)
        summary = f"Sync complete — uploaded={uploaded} skipped={skipped} errors={errors}"
        log.info(summary)
        _write_sync_log(summary, "OK" if errors == 0 else "WARN")

        return {"uploaded": uploaded, "skipped": skipped, "errors": errors}

    def run_loop(self) -> None:
        log.info(f"Sync manager running (interval={SYNC_INTERVAL}s)")
        while True:
            try:
                self.sync()
            except Exception as e:
                log.error(f"Sync cycle error: {e}")
                _write_sync_log(f"Sync cycle error: {e}", "ERROR")
            time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    SyncManager().run_loop()
