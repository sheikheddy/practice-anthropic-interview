import bisect
import sys
from dataclasses import dataclass
from itertools import chain

from chat_server_level2_impl import HashRingVirtual


@dataclass(slots=True)
class ChatResponse:
    success: bool
    llm_reply: str = ""


def post_fn(server_id: str, chat_id: str, message: str) -> ChatResponse:
    """Simulate a HTTP call to the remote server."""
    raise Exception("post_fn is expected to be mocked in tests")


_DEFAULT_POST_FN = post_fn


def _resolve_post_fn():
    """Return the active post function, supporting compatibility-module patching."""
    if post_fn is not _DEFAULT_POST_FN:
        return post_fn

    compat_module = sys.modules.get("chat_server_impl")
    if compat_module is not None:
        compat_post_fn = getattr(compat_module, "post_fn", None)
        if callable(compat_post_fn) and compat_post_fn is not _DEFAULT_POST_FN:
            return compat_post_fn

    return post_fn


class ChatClient(HashRingVirtual):
    """Client implementing hash-ring routing with failover and affinity."""

    def __init__(self):
        super().__init__()
        # Backward-compatible alias used by tests and existing callers.
        self.ring = self
        self.chat_to_server: dict[str, str] = {}

    def add_server(self, server_id: str, capacity: int = 1) -> bool:
        return super().add_server(server_id, capacity=capacity)

    def _drop_server_affinities_locked(self, server_id: str) -> None:
        self.chat_to_server = {
            chat_id: assigned_server
            for chat_id, assigned_server in self.chat_to_server.items()
            if assigned_server != server_id
        }

    def _get_live_affinity_locked(self, chat_id: str) -> str | None:
        affinity_server = self.chat_to_server.get(chat_id)
        if affinity_server is None:
            return None
        if affinity_server in self._servers:
            return affinity_server
        self.chat_to_server.pop(chat_id, None)
        return None

    def _set_affinity_if_live_locked(self, chat_id: str, server_id: str) -> None:
        if server_id in self._servers:
            self.chat_to_server[chat_id] = server_id

    def _ordered_unique_ring_servers(self, ring_snapshot, chat_id: str) -> list[str]:
        chat_hash = self._hash(chat_id)
        start = bisect.bisect_left(ring_snapshot, chat_hash, key=self._entry_hash)
        wrapped = chain(ring_snapshot[start:], ring_snapshot[:start])
        ordered = [entry[2] for entry in wrapped]
        return list(dict.fromkeys(ordered))

    def remove_server(self, server_id: str) -> bool:
        with self._lock:
            removed = super().remove_server(server_id)
            if not removed:
                return False

            self._drop_server_affinities_locked(server_id)
            return True

    def _iter_ring_servers(self, chat_id: str):
        with self._lock:
            if not self._ring:
                return iter(())
            ring_snapshot = list(self._ring)

        return iter(self._ordered_unique_ring_servers(ring_snapshot, chat_id))

    def send_chat_message(self, chat_id: str, message: str) -> str:
        with self._lock:
            if not self._ring:
                raise RuntimeError("No available servers")
            affinity_server = self._get_live_affinity_locked(chat_id)

        send_fn = _resolve_post_fn()
        tried: set[str] = set()
        if affinity_server is not None:
            tried.add(affinity_server)
            response = send_fn(affinity_server, chat_id, message)
            if response.success:
                return response.llm_reply

        for server_id in self._iter_ring_servers(chat_id):
            if server_id in tried:
                continue
            tried.add(server_id)
            response = send_fn(server_id, chat_id, message)
            if response.success:
                with self._lock:
                    self._set_affinity_if_live_locked(chat_id, server_id)
                return response.llm_reply

        with self._lock:
            self.chat_to_server.pop(chat_id, None)
        raise RuntimeError("All servers failed")

    def get_current_server(self, chat_id: str) -> str:
        with self._lock:
            affinity_server = self._get_live_affinity_locked(chat_id)
            if affinity_server is not None:
                return affinity_server
        return self.get_server(chat_id)
