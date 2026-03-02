import bisect
import threading
from typing import Any


class BaseHashRing:
    """Shared ring behavior with stage-specific hooks."""

    def __init__(self):
        self._ring: list[Any] = []
        self._lock = threading.RLock()

    @staticmethod
    def _entry_hash(entry: Any) -> int:
        return entry[0]

    @staticmethod
    def _entry_server(entry: Any) -> str:
        raise NotImplementedError

    def _hash(self, key: str) -> int:
        raise NotImplementedError

    def _add_server_locked(self, server_id: str, **kwargs: Any) -> bool:
        raise NotImplementedError

    def _remove_server_locked(self, server_id: str) -> bool:
        raise NotImplementedError

    def add_server(self, server_id: str, *args: Any, **kwargs: Any) -> bool:
        with self._lock:
            return self._add_server_locked(server_id, *args, **kwargs)

    def remove_server(self, server_id: str) -> bool:
        with self._lock:
            return self._remove_server_locked(server_id)

    def _ring_index_for_hash(self, key_hash: int) -> int:
        idx = bisect.bisect_left(self._ring, key_hash, key=self._entry_hash)
        if idx == len(self._ring):
            idx = 0
        return idx

    def get_server(self, chat_id: str) -> str:
        with self._lock:
            if not self._ring:
                raise ValueError("No servers in ring")

            chat_hash = self._hash(chat_id)
            idx = self._ring_index_for_hash(chat_hash)
            return self._entry_server(self._ring[idx])
