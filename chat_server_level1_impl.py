import bisect
import hashlib
import threading

type RingEntry = tuple[int, str]


def _require_str(value: object, arg_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{arg_name} must be a str")
    return value


def hash(key: str) -> int:
    """Given a server or chat ID, return a deterministic hash."""
    key = _require_str(key, "key")
    return int(hashlib.md5(key.encode()).hexdigest()[:16], 16)


class HashRing:
    """Deterministic mapping from chat_id to server_id using hashing."""

    def __init__(self):
        self._ring: list[RingEntry] = []
        self._servers: set[str] = set()
        # Guard all ring/server mutations and bisect operations.
        self._lock = threading.RLock()

    @staticmethod
    def _hash(key: str) -> int:
        return hash(key)

    @staticmethod
    def _entry_hash(entry: RingEntry) -> int:
        return entry[0]

    def add_server(self, server_id: str) -> bool:
        server_id = _require_str(server_id, "server_id")
        with self._lock:
            if server_id in self._servers:
                return False
            self._servers.add(server_id)
            bisect.insort(self._ring, (self._hash(server_id), server_id))
            return True

    def remove_server(self, server_id: str) -> bool:
        server_id = _require_str(server_id, "server_id")
        with self._lock:
            if server_id not in self._servers:
                return False

            self._servers.remove(server_id)
            server_hash = self._hash(server_id)
            idx = bisect.bisect_left(self._ring, server_hash, key=self._entry_hash)

            while idx < len(self._ring) and self._ring[idx][0] == server_hash:
                if self._ring[idx][1] == server_id:
                    del self._ring[idx]
                    break
                idx += 1
            return True

    def get_server(self, chat_id: str) -> str:
        chat_id = _require_str(chat_id, "chat_id")
        with self._lock:
            if not self._ring:
                raise ValueError("No servers in ring")

            chat_hash = self._hash(chat_id)
            idx = bisect.bisect_left(self._ring, chat_hash, key=self._entry_hash)
            if idx == len(self._ring):
                idx = 0
            return self._ring[idx][1]
