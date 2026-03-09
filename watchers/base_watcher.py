"""
BaseWatcher — abstract base class for all event watchers.
Subclass and implement `poll()` to add new event sources.
"""

import time
from abc import ABC, abstractmethod

from utils.config import LOOP_INTERVAL, MAX_RETRIES
from utils.logger import get_logger


class BaseWatcher(ABC):
    """Poll an external source and write discovered events as Inbox tasks."""

    def __init__(self, name: str, poll_interval: int = LOOP_INTERVAL):
        self.name = name
        self.poll_interval = poll_interval
        self.log = get_logger(f"watcher.{name}")
        self._running = False

    @abstractmethod
    def poll(self) -> None:
        """Check the source for new events and write them to Inbox."""
        ...

    def start(self) -> None:
        self._running = True
        self.log.info(f"{self.name} watcher started (interval={self.poll_interval}s)")
        while self._running:
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    self.poll()
                    break
                except Exception as e:
                    retries += 1
                    self.log.error(f"Poll failed (attempt {retries}/{MAX_RETRIES}): {e}")
                    if retries < MAX_RETRIES:
                        time.sleep(2 ** retries)
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
        self.log.info(f"{self.name} watcher stopped")
