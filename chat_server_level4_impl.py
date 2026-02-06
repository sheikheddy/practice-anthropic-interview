from dataclasses import dataclass

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

    @property
    def total_chats(self) -> int:
        return len(self.vram_chats) + len(self.ram_chats)

    def has_chat(self, chat_id: str) -> bool:
        return chat_id in self.vram_chats or chat_id in self.ram_chats

    def remove_chat(self, chat_id: str) -> ChatData | None:
        if (chat := self.vram_chats.pop(chat_id, None)) is not None:
            return chat
        return self.ram_chats.pop(chat_id, None)

    def shutdown(self) -> None:
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

    def handle_request(
        self, chat_id: str, timestamp: int, message: str
    ) -> ChatResponse:
        if not self.is_online:
            return ChatResponse(success=False)

        if chat_id in self.vram_chats:
            self.num_cache_hits += 1
            self.vram_chats[chat_id].last_timestamp = timestamp
            return ChatResponse(success=True, llm_reply="")

        if chat_id in self.ram_chats:
            self.num_cache_hits += 1
            chat_data = self.ram_chats[chat_id]
            chat_data.last_timestamp = timestamp

            if len(self.vram_chats) >= self.max_vram_chats:
                if len(self.ram_chats) >= self.max_ram_chats:
                    victim_ram = self._oldest_chat(
                        self.ram_chats, exclude_chat_id=chat_id
                    )
                    if victim_ram is not None:
                        del self.ram_chats[victim_ram.chat_id]
                self._evict_oldest_vram_to_ram()

            del self.ram_chats[chat_id]
            self.vram_chats[chat_id] = chat_data
            return ChatResponse(success=True, llm_reply="")

        self.num_cache_misses += 1
        new_chat = ChatData(chat_id=chat_id, last_timestamp=timestamp)

        if len(self.vram_chats) >= self.max_vram_chats:
            if len(self.ram_chats) >= self.max_ram_chats:
                victim_ram = self._oldest_chat(self.ram_chats)
                if victim_ram is not None:
                    del self.ram_chats[victim_ram.chat_id]
            self._evict_oldest_vram_to_ram()

        self.vram_chats[chat_id] = new_chat
        return ChatResponse(success=True, llm_reply="")
