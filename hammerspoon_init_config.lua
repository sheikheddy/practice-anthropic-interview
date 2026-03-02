-- use this file as your Hammerspoon init.lua

hs.alert.show("Hammerspoon config loaded!")

-- Guard so synthetic keystrokes don't re-trigger snippets.
local injecting = false
-- Many web/chat inputs require Shift+Return for a literal newline.
-- Set this to {} if your target editor expects plain Return.
local NEWLINE_MODS = { "shift" }
local KEY_GAP_US = 12000

local function pressKey(mods, key)
  hs.eventtap.keyStroke(mods, key, 0)
  hs.timer.usleep(KEY_GAP_US)
end

local function clearCurrentLine()
  -- Remove editor auto-indent so snippet indentation stays exact.
  pressKey({ "cmd" }, "left")
  pressKey({ "cmd", "shift" }, "right")
  pressKey({}, "delete")
end

local function splitLines(s)
  local normalized = s:gsub("\r\n", "\n")
  local out = {}
  for line in (normalized .. "\n"):gmatch("(.-)\n") do
    table.insert(out, line)
  end
  if #out > 0 and out[#out] == "" then
    table.remove(out, #out)
  end
  return out
end

-- Inserts multiline text via simulated keypresses (no clipboard use).
local function typeMultiline(s)
  local lines = splitLines(s)
  for i, line in ipairs(lines) do
    if i > 1 then
      clearCurrentLine()
    end
    if #line > 0 then
      hs.eventtap.keyStrokes(line)
      hs.timer.usleep(KEY_GAP_US)
    end
    if i < #lines then
      pressKey(NEWLINE_MODS, "return")
    end
  end
end

local SNIPPET_CHATBASE = [=[
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

    def add_server(self, server_id: str, **kwargs: Any) -> bool:
        with self._lock:
            return self._add_server_locked(server_id, **kwargs)

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
]=]

local SNIPPET_CHAT1 = [=[
import bisect
import hashlib

from chat_server_ring_base import BaseHashRing

type RingEntry = tuple[int, str]

def hash(key: str) -> int:
    """Given a server or chat ID, return a deterministic hash."""
    return int(hashlib.md5(key.encode()).hexdigest()[:16], 16)


class HashRing(BaseHashRing):
    """Deterministic mapping from chat_id to server_id using hashing."""

    def __init__(self):
        super().__init__()
        self._ring: list[RingEntry] = []
        self._servers: set[str] = set()

    @staticmethod
    def _hash(key: str) -> int:
        return hash(key)

    @staticmethod
    def _entry_hash(entry: RingEntry) -> int:
        return entry[0]

    @staticmethod
    def _entry_server(entry: RingEntry) -> str:
        return entry[1]

    def _add_server_locked(self, server_id: str) -> bool:
        if server_id in self._servers:
            return False
        self._servers.add(server_id)
        bisect.insort(self._ring, (self._hash(server_id), server_id))
        return True

    def _remove_server_locked(self, server_id: str) -> bool:
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
]=]

local SNIPPET_CHAT2 = [=[
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

    @staticmethod
    def _entry_server(entry: VirtualRingEntry) -> str:
        return entry[2]

    @property
    def servers(self) -> set[str]:
        with self._lock:
            return set(self._servers.keys())

    def add_server(self, server_id: str, capacity_factor: int = 1) -> bool:
        assert capacity_factor >= 1
        return super().add_server(server_id, capacity_factor=capacity_factor)

    def _add_server_locked(self, server_id: str, capacity_factor: int = 1) -> bool:
        if server_id in self._servers:
            return False

        self._servers[server_id] = capacity_factor
        for i in range(capacity_factor):
            virtual_id = f"{server_id}:{i}"
            bisect.insort(self._ring, (self._hash(virtual_id), virtual_id, server_id))
        return True

    def _remove_server_locked(self, server_id: str) -> bool:
        if server_id not in self._servers:
            return False
        del self._servers[server_id]
        self._ring = [entry for entry in self._ring if entry[2] != server_id]
        return True
]=]

local SNIPPET_CHAT3 = [=[
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

    def add_server(self, server_id: str, capacity_factor: int) -> bool:
        return super().add_server(server_id, capacity_factor)

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
]=]

local SNIPPET_CHAT4 = [=[
from dataclasses import dataclass
import threading

from chat_server_level3_impl import ChatResponse


@dataclass(slots=True)
class ChatData:
    """Placeholder for cached chat metadata."""

    chat_id: str
    last_timestamp: int


class Server:
    """A server with VRAM and RAM capacity for cached chats."""

    def __init__(self, max_vram_chats: int, max_ram_chats: int):
        assert max_vram_chats > 1, "system requires at least 2 to function"
        assert max_ram_chats > 1, "system requires at least 2 to function"
        self.max_vram_chats = max_vram_chats
        self.max_ram_chats = max_ram_chats
        self.num_cache_hits = 0
        self.num_cache_misses = 0
        self.is_online = True
        self.vram_chats: dict[str, ChatData] = {}
        self.ram_chats: dict[str, ChatData] = {}
        self._lock = threading.RLock()

    @property
    def total_chats(self) -> int:
        with self._lock:
            return len(self.vram_chats) + len(self.ram_chats)

    def has_chat(self, chat_id: str) -> bool:
        with self._lock:
            return chat_id in self.vram_chats or chat_id in self.ram_chats

    def remove_chat(self, chat_id: str) -> ChatData | None:
        with self._lock:
            if (chat := self.vram_chats.pop(chat_id, None)) is not None:
                return chat
            return self.ram_chats.pop(chat_id, None)

    def shutdown(self) -> None:
        with self._lock:
            if not self.is_online:
                raise RuntimeError("Server is already offline")
            self.is_online = False
            self.vram_chats.clear()
            self.ram_chats.clear()

    @staticmethod
    def _oldest_chat(
        chats: dict[str, ChatData], exclude_chat_id: str | None = None
    ) -> ChatData | None:
        candidates = [
            chat for chat_id, chat in chats.items() if chat_id != exclude_chat_id
        ]
        if not candidates:
            return None
        # Timestamp-only ordering; ties keep dict insertion order determinism.
        return min(candidates, key=lambda chat: chat.last_timestamp)

    def _evict_oldest_vram_to_ram(self) -> None:
        victim = self._oldest_chat(self.vram_chats)
        if victim is None:
            return
        del self.vram_chats[victim.chat_id]
        self.ram_chats[victim.chat_id] = victim

    def _ensure_vram_slot(self, exclude_chat_id: str | None = None) -> None:
        if len(self.vram_chats) < self.max_vram_chats:
            return

        if len(self.ram_chats) >= self.max_ram_chats:
            victim_ram = self._oldest_chat(self.ram_chats, exclude_chat_id=exclude_chat_id)
            if victim_ram is not None:
                del self.ram_chats[victim_ram.chat_id]

        self._evict_oldest_vram_to_ram()

    def _handle_vram_hit(self, chat_id: str, timestamp: int) -> ChatResponse:
        self.num_cache_hits += 1
        self.vram_chats[chat_id].last_timestamp = timestamp
        return ChatResponse(success=True, llm_reply="")

    def _handle_ram_hit(self, chat_id: str, timestamp: int) -> ChatResponse:
        self.num_cache_hits += 1
        chat_data = self.ram_chats[chat_id]
        chat_data.last_timestamp = timestamp

        self._ensure_vram_slot(exclude_chat_id=chat_id)
        del self.ram_chats[chat_id]
        self.vram_chats[chat_id] = chat_data
        return ChatResponse(success=True, llm_reply="")

    def _handle_cache_miss(self, chat_id: str, timestamp: int) -> ChatResponse:
        self.num_cache_misses += 1
        new_chat = ChatData(chat_id=chat_id, last_timestamp=timestamp)

        self._ensure_vram_slot()
        self.vram_chats[chat_id] = new_chat
        return ChatResponse(success=True, llm_reply="")

    def handle_request(
        self, chat_id: str, timestamp: int, message: str
    ) -> ChatResponse:
        with self._lock:
            if not self.is_online:
                return ChatResponse(success=False)

            if chat_id in self.vram_chats:
                return self._handle_vram_hit(chat_id, timestamp)

            if chat_id in self.ram_chats:
                return self._handle_ram_hit(chat_id, timestamp)

            return self._handle_cache_miss(chat_id, timestamp)
]=]

local snippets = {
  [";;chatbase"] = SNIPPET_CHATBASE,
  [";;chat1"] = SNIPPET_CHAT1,
  [";;chat2"] = SNIPPET_CHAT2,
  [";;chat3"] = SNIPPET_CHAT3,
  [";;chat4"] = SNIPPET_CHAT4,
}

-- Rolling buffer of recent typed chars to detect triggers.
local buffer = ""

local tap = hs.eventtap.new({ hs.eventtap.event.types.keyDown }, function(e)
  if injecting then return false end

  local f = e:getFlags()
  if f.cmd or f.alt or f.ctrl then return false end

  local keyCode = e:getKeyCode()
  local char = e:getCharacters()

  if keyCode == hs.keycodes.map.delete then
    buffer = buffer:sub(1, -2)
    return false
  end

  if keyCode == hs.keycodes.map.space
      or keyCode == hs.keycodes.map["return"]
      or keyCode == hs.keycodes.map.tab
      or keyCode == hs.keycodes.map.escape then
    buffer = ""
    return false
  end

  if char and #char > 0 then
    buffer = buffer .. char
    if #buffer > 80 then buffer = buffer:sub(-80) end

    for trig, out in pairs(snippets) do
      if #buffer >= #trig and buffer:sub(-#trig) == trig then
        injecting = true
        hs.timer.doAfter(0, function()
          -- In some apps the final trigger key may still land, so delete
          -- the full trigger token before injecting the snippet.
          for _ = 1, #trig do
            pressKey({}, "delete")
          end
          typeMultiline(out)
          hs.timer.doAfter(0.05, function() injecting = false end)
        end)
        buffer = ""
        return true
      end
    end
  end

  return false
end)

tap:start()
hs.alert.show("Hotstrings: ;;chatbase ;;chat1 ;;chat2 ;;chat3 ;;chat4")
