# Watchers

Watchers are Python processes that detect external events and translate them into task files in the Obsidian vault `Inbox/`.

---

## Base Watcher

All watchers inherit from `watchers/base_watcher.py`:

```python
class BaseWatcher(ABC):
    def poll(self) -> None: ...   # implement per source
    def start(self) -> None: ...  # retry loop
    def stop(self) -> None: ...
```

Retry logic: exponential backoff up to `MAX_RETRIES` (default 3).

---

## Gmail Watcher

**File:** `watchers/gmail_watcher.py`

**Method:** IMAP4_SSL poll

**Configuration:**
```env
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
GMAIL_POLL_INTERVAL=60
```

**Task format:**
```markdown
---
task_id: abc12345
title: Email: Partnership proposal from Acme Corp
source: gmail
priority: HIGH
status: inbox
created_at: 2026-03-06 10:00:00 UTC
sender: partner@acme.com
email_id: 42
---
```

**Demo mode:** If credentials are absent, injects one simulated email task.

---

## Filesystem Watcher

**File:** `watchers/filesystem_watcher.py`

**Method:** `watchdog` library observer

**Configuration:**
```env
WATCH_PATH=./watched_folder
```

**Events detected:**
- File created → MEDIUM priority task
- File modified → LOW priority task
- File deleted → HIGH priority task (confirmation needed)

**Install:** `pip install watchdog`

---

## WhatsApp Watcher

**File:** `watchers/whatsapp_watcher.py`

**Method:** WhatsApp Business API polling

**Configuration:**
```env
WHATSAPP_API_URL=https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID
WHATSAPP_API_KEY=your_bearer_token
```

**Demo mode:** If credentials are absent, injects one simulated message task.

---

## Adding a New Watcher

1. Create `watchers/my_source_watcher.py`
2. Inherit from `BaseWatcher`
3. Implement `poll()` to call your source and call `write_inbox_task()`
4. Add to `ecosystem.config.js` for PM2 management

```python
from watchers.base_watcher import BaseWatcher
from utils.vault_io import write_inbox_task

class MySourceWatcher(BaseWatcher):
    def __init__(self):
        super().__init__("my_source", poll_interval=30)

    def poll(self):
        # detect events...
        write_inbox_task(
            title="Event from my source",
            source="my_source",
            body="Details...",
            priority="MEDIUM",
        )
```
