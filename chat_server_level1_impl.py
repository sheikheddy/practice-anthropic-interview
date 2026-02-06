import bisect
import hashlib

type RingEntry = tuple[int, str]


def hash(key: str) -> int:
    """Given a server or chat ID, return a deterministic hash."""
    return int(hashlib.md5(key.encode()).hexdigest()[:16], 16)


class HashRing:
    """Deterministic mapping from chat_id to server_id using hashing."""

    def __init__(self):
        self._ring: list[RingEntry] = []
        self._servers: set[str] = set()

    @staticmethod
    def _hash(key: str) -> int:
        return hash(key)

    @staticmethod
    def _entry_hash(entry: RingEntry) -> int:
        return entry[0]

    def add_server(self, server_id: str) -> bool:
        if server_id in self._servers:
            return False
        self._servers.add(server_id)
        bisect.insort(self._ring, (self._hash(server_id), server_id))
        return True

    def remove_server(self, server_id: str) -> bool:
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
        if not self._ring:
            raise ValueError("No servers in ring")

        chat_hash = self._hash(chat_id)
        idx = bisect.bisect_left(self._ring, chat_hash, key=self._entry_hash)
        if idx == len(self._ring):
            idx = 0
        return self._ring[idx][1]
