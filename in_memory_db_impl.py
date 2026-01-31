from collections import deque


class InMemoryDBImpl:
    """
    In-memory DB with modification counts and key-level locking.
    """

    def __init__(self):
        self.db = {}  # {key: {field: value}}
        self.modifs = {}  # {key: modification_count}
        self.locks = {}  # {key: deque([caller_id, ...])}

    def _inc_modif(self, key: str) -> None:
        self.modifs[key] = self.modifs.get(key, 0) + 1

    def _is_locked(self, key: str) -> bool:
        return key in self.locks and len(self.locks[key]) > 0

    def set_or_inc(self, key: str, field: str, value: int) -> int:
        value = int(value)
        if key not in self.db:
            self.db[key] = {field: value}
            self._inc_modif(key)
            return value

        if not self._is_locked(key):
            self.db[key][field] = self.db[key].get(field, 0) + value
            self._inc_modif(key)
            return self.db[key][field]

        return self.db[key].get(field, 0)

    def get(self, key: str, field: str) -> int | None:
        if key not in self.db:
            return None
        if field not in self.db[key]:
            return None
        return self.db[key][field]

    def delete(self, key: str, field: str) -> bool:
        if key not in self.db or field not in self.db[key]:
            return False
        if self._is_locked(key):
            return False

        del self.db[key][field]
        self._inc_modif(key)
        if not self.db[key]:
            del self.db[key]
            self.modifs.pop(key, None)
            self.locks.pop(key, None)
        return True

    def top_n_keys(self, n: int) -> str:
        n = int(n)
        candidates = sorted(self.modifs.items(), key=lambda item: (-item[1], item[0]))[:n]
        return ", ".join([f"{k}({v})" for k, v in candidates])

    def set_or_inc_by_caller(self, key: str, field: str, value: int, caller_id: str) -> int:
        value = int(value)
        if key not in self.db:
            self.db[key] = {field: value}
            self._inc_modif(key)
            return value

        if not self._is_locked(key):
            self.db[key][field] = self.db[key].get(field, 0) + value
            self._inc_modif(key)
            return self.db[key][field]

        if self.locks[key][0] == caller_id:
            self.db[key][field] = self.db[key].get(field, 0) + value
            self._inc_modif(key)
            return self.db[key][field]

        return self.db[key].get(field, 0)

    def delete_by_caller(self, key: str, field: str, caller_id: str) -> bool:
        if key not in self.db or field not in self.db[key]:
            return False
        if self._is_locked(key) and self.locks[key][0] != caller_id:
            return False

        del self.db[key][field]
        self._inc_modif(key)
        if not self.db[key]:
            del self.db[key]
            self.modifs.pop(key, None)
            self.locks.pop(key, None)
        return True

    def lock(self, caller_id: str, key: str) -> str:
        if key not in self.db:
            return "invalid_request"
        if not self._is_locked(key):
            self.locks[key] = deque([caller_id])
            return "acquired"
        if self.locks[key][0] == caller_id or caller_id in self.locks[key]:
            return ""
        self.locks[key].append(caller_id)
        return "wait"

    def unlock(self, key: str) -> str:
        if key not in self.db:
            return "invalid_request"
        if not self._is_locked(key):
            return ""
        self.locks[key].popleft()
        if not self.locks[key]:
            del self.locks[key]
        return "released"
