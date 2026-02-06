import bisect

from chat_server_level1_impl import HashRing

type VirtualRingEntry = tuple[int, str, str]


class HashRingVirtual(HashRing):
    """Deterministic mapping from chat_id to server_id using virtual servers."""

    def __init__(self):
        super().__init__()
        # Level 2 builds on Level 1 behavior but changes ring entry shape.
        # (hash, virtual_id, physical_server_id)
        self._ring: list[VirtualRingEntry] = []
        self._servers: dict[str, int] = {}

    @staticmethod
    def _entry_hash(entry: VirtualRingEntry) -> int:
        return entry[0]

    @property
    def servers(self) -> set[str]:
        return set(self._servers.keys())

    def add_server(self, server_id: str, capacity_factor: int = 1) -> bool:
        assert capacity_factor >= 1
        if server_id in self._servers:
            return False

        self._servers[server_id] = capacity_factor
        for i in range(capacity_factor):
            virtual_id = f"{server_id}:{i}"
            bisect.insort(self._ring, (self._hash(virtual_id), virtual_id, server_id))
        return True

    def remove_server(self, server_id: str) -> bool:
        if server_id not in self._servers:
            return False
        del self._servers[server_id]
        self._ring = [entry for entry in self._ring if entry[2] != server_id]
        return True

    def get_server(self, chat_id: str) -> str:
        if not self._ring:
            raise ValueError("No servers in ring")

        chat_hash = self._hash(chat_id)
        idx = bisect.bisect_left(self._ring, chat_hash, key=self._entry_hash)
        if idx == len(self._ring):
            idx = 0
        return self._ring[idx][2]
