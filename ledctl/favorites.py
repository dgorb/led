import json
import logging
import os
import threading

from .colors import normalize_hex

log = logging.getLogger(__name__)

MAX_FAVORITES = 48


class Favorites:
    def __init__(self, path):
        self._path = path
        self._lock = threading.Lock()

    def list(self):
        with self._lock:
            return self._read()

    def add(self, color):
        color = normalize_hex(color)
        with self._lock:
            items = self._read()
            if color in items:
                return items
            if len(items) >= MAX_FAVORITES:
                raise ValueError(f"at most {MAX_FAVORITES} favorites allowed")
            items.append(color)
            self._write(items)
            return items

    def remove(self, color):
        color = normalize_hex(color)
        with self._lock:
            items = [c for c in self._read() if c != color]
            self._write(items)
            return items

    def _read(self):
        try:
            items = json.loads(self._path.read_text())
            return [normalize_hex(c) for c in items]
        except FileNotFoundError:
            return []
        except (OSError, ValueError, TypeError):
            log.warning("Ignoring unreadable favorites file %s", self._path)
            return []

    def _write(self, items):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items))
        os.replace(tmp, self._path)
