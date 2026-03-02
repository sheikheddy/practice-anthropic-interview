import bisect
from typing import Any

from chat_server_level1_impl import HashRing

type VirtualRingEntry = tuple[int, str, str]


class HashRingVirtual(HashRing):
    """Deterministic mapping from chat_id to server_id using virtual servers."""

    def __init__(self):
        super().__init__()
        # Level 2 builds on Level 1 behavior but changes ring entry shape.
        # (hash, virtual_id, physical_server_id)
        self._ring: list[VirtualRingEntry] = []
        self._servers: set[str] = set()
        self._capacity_by_server: dict[str, int] = {}

    @staticmethod
    def _entry_hash(entry: VirtualRingEntry) -> int:
        return entry[0]

    @staticmethod
    def _entry_server(entry: VirtualRingEntry) -> str:
        return entry[2]

    @property
    def servers(self) -> set[str]:
        with self._lock:
            return set(self._servers)

    @staticmethod
    def _coerce_capacity_factor(args: tuple[Any, ...], kwargs: dict[str, Any]) -> int:
        has_positional = len(args) > 0
        if len(args) > 1:
            raise TypeError("add_server() takes at most 2 positional arguments")

        has_capacity_factor = "capacity_factor" in kwargs
        has_capacity = "capacity" in kwargs
        if has_capacity_factor and has_capacity:
            raise TypeError("add_server() got multiple capacity keyword arguments")
        if len(kwargs) > int(has_capacity_factor) + int(has_capacity):
            raise TypeError("add_server() got unexpected keyword argument")
        if has_positional and (has_capacity_factor or has_capacity):
            raise TypeError("add_server() got multiple values for capacity")

        if has_positional:
            return args[0]
        if has_capacity_factor:
            return kwargs["capacity_factor"]
        if has_capacity:
            return kwargs["capacity"]
        return 1

    def add_server(self, server_id: str, *args: Any, **kwargs: Any) -> bool:
        capacity_factor = self._coerce_capacity_factor(args, kwargs)
        assert capacity_factor >= 1
        return super().add_server(server_id, capacity_factor=capacity_factor)

    def _add_server_locked(self, server_id: str, capacity_factor: int = 1) -> bool:
        if server_id in self._servers:
            return False

        self._servers.add(server_id)
        self._capacity_by_server[server_id] = capacity_factor
        for i in range(capacity_factor):
            virtual_id = f"{server_id}:{i}"
            bisect.insort(self._ring, (self._hash(virtual_id), virtual_id, server_id))
        return True

    def _remove_server_locked(self, server_id: str) -> bool:
        if server_id not in self._servers:
            return False
        self._servers.remove(server_id)
        self._capacity_by_server.pop(server_id, None)
        self._ring = [entry for entry in self._ring if entry[2] != server_id]
        return True
