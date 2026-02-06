import bisect
import sys
from dataclasses import dataclass

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

    def add_server(self, server_id: str, capacity_factor: int) -> bool:
        return super().add_server(server_id, capacity_factor)

    def remove_server(self, server_id: str) -> bool:
        removed = super().remove_server(server_id)
        if not removed:
            return False

        self.chat_to_server = {
            chat_id: assigned_server
            for chat_id, assigned_server in self.chat_to_server.items()
            if assigned_server != server_id
        }
        return True

    def _iter_ring_servers(self, chat_id: str):
        if not self._ring:
            return

        chat_hash = self._hash(chat_id)
        start = bisect.bisect_left(self._ring, chat_hash, key=self._entry_hash)
        seen: set[str] = set()

        for offset in range(len(self._ring)):
            idx = (start + offset) % len(self._ring)
            server_id = self._ring[idx][2]
            if server_id in seen:
                continue
            seen.add(server_id)
            yield server_id

    def send_chat_message(self, chat_id: str, message: str) -> str:
        if not self._ring:
            raise RuntimeError("No available servers")

        send_fn = _resolve_post_fn()
        tried: set[str] = set()
        affinity_server = self.chat_to_server.get(chat_id)
        if affinity_server is not None and affinity_server in self._servers:
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
                self.chat_to_server[chat_id] = server_id
                return response.llm_reply

        self.chat_to_server.pop(chat_id, None)
        raise RuntimeError("All servers failed")

    def get_current_server(self, chat_id: str) -> str:
        affinity_server = self.chat_to_server.get(chat_id)
        if affinity_server is not None and affinity_server in self._servers:
            return affinity_server
        if affinity_server is not None and affinity_server not in self._servers:
            self.chat_to_server.pop(chat_id, None)
        return self.get_server(chat_id)
