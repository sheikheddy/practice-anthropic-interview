import copy
import typing as tp


class DatabaseImpl:
    """
    An in-memory key-value database that supports time-to-live (TTL) features.
    """

    _INF_TTL = 10**18

    def __init__(self):
        """
        Initializes the database.
        The data is stored in a nested dictionary structure:
        {
            "key1": {
                "field1": (value, creation_timestamp, ttl),
                "field2": (value, creation_timestamp, ttl),
            },
            ...
        }
        """
        self.db: tp.Dict[str, tp.Dict[str, tp.Tuple[str, int, int]]] = {}
        self.backups: tp.List[tp.Tuple[int, tp.Dict[str, tp.Dict[str, tp.Tuple[str, int, int]]]]] = []

    def _is_expired(self, value_info: tp.Tuple[str, int, int], current_timestamp: int) -> bool:
        _, creation_ts, ttl = value_info
        return current_timestamp >= creation_ts + ttl

    # --------------------------------------------------------------------------
    # Level 1 & 3: SET, GET, DELETE Methods
    # --------------------------------------------------------------------------

    def set(self, key: str, field: str, value: str) -> None:
        """Level 1: Sets a value. Backward compatible, assumes timestamp=0."""
        self.set_at(key, field, value, 0)

    def set_at(self, key: str, field: str, value: str, timestamp: int) -> None:
        """Level 3: Sets a value at a specific timestamp with infinite TTL."""
        self.set_at_with_ttl(key, field, value, timestamp, self._INF_TTL)

    def set_at_with_ttl(self, key: str, field: str, value: str, timestamp: int, ttl: int) -> None:
        """Level 3: Sets a value with a creation timestamp and a TTL."""
        if key not in self.db:
            self.db[key] = {}
        self.db[key][field] = (value, int(timestamp), int(ttl))

    def get(self, key: str, field: str) -> str | None:
        """Level 1: Gets a value. Backward compatible, assumes timestamp=0."""
        return self.get_at(key, field, 0)

    def get_at(self, key: str, field: str, timestamp: int) -> str | None:
        """Level 3: Gets a value at a specific timestamp, respecting TTL."""
        if key not in self.db or field not in self.db[key]:
            return None

        value_info = self.db[key][field]
        if self._is_expired(value_info, int(timestamp)):
            return None

        return value_info[0]

    def delete(self, key: str, field: str) -> bool:
        """Level 1: Deletes a value. Backward compatible, assumes timestamp=0."""
        return self.delete_at(key, field, 0)

    def delete_at(self, key: str, field: str, timestamp: int) -> bool:
        """Level 3: Deletes a value at a specific timestamp, respecting TTL."""
        if key not in self.db or field not in self.db[key]:
            return False

        value_info = self.db[key][field]
        if self._is_expired(value_info, int(timestamp)):
            return False

        del self.db[key][field]
        if not self.db[key]:
            del self.db[key]
        return True

    # --------------------------------------------------------------------------
    # Level 2 & 3: SCAN Methods
    # --------------------------------------------------------------------------

    def scan(self, key: str) -> str:
        """Level 2: Scans all records for a key. Assumes timestamp=0."""
        return self.scan_at(key, 0)

    def scan_at(self, key: str, timestamp: int) -> str:
        """Level 3: Scans all non-expired records for a key at a given timestamp."""
        if key not in self.db:
            return ""

        records = []
        for field, value_info in sorted(self.db[key].items()):
            if not self._is_expired(value_info, int(timestamp)):
                value = value_info[0]
                records.append(f"{field}({value})")

        return ", ".join(records)

    def scan_by_prefix(self, key: str, prefix: str) -> str:
        """Level 2: Scans records matching a prefix. Assumes timestamp=0."""
        return self.scan_by_prefix_at(key, prefix, 0)

    def scan_by_prefix_at(self, key: str, prefix: str, timestamp: int) -> str:
        """Level 3: Scans non-expired records matching a prefix at a given timestamp."""
        if key not in self.db:
            return ""

        records = []
        for field, value_info in sorted(self.db[key].items()):
            if field.startswith(prefix) and not self._is_expired(value_info, int(timestamp)):
                value = value_info[0]
                records.append(f"{field}({value})")

        return ", ".join(records)

    # --------------------------------------------------------------------------
    # Level 4: Backup and Restore
    # --------------------------------------------------------------------------

    def backup(self, timestamp: int) -> int:
        """
        Stores a snapshot of the database and returns the number of keys
        with at least one non-expired record at the given timestamp.
        """
        ts = int(timestamp)
        snapshot = copy.deepcopy(self.db)
        self.backups.append((ts, snapshot))

        count = 0
        for fields in snapshot.values():
            if any(not self._is_expired(value_info, ts) for value_info in fields.values()):
                count += 1
        return count

    def restore(self, timestamp: int, timestamp_to_restore: int) -> None:
        """
        Restores the database state to the latest snapshot at or before timestamp_to_restore.
        TTLs are adjusted relative to the restore timestamp.
        """
        ts = int(timestamp)
        target_ts = int(timestamp_to_restore)

        chosen = None
        for backup_ts, snapshot in reversed(self.backups):
            if backup_ts <= target_ts:
                chosen = (backup_ts, snapshot)
                break

        if chosen is None:
            self.db = {}
            return None

        backup_ts, snapshot = chosen
        self.db = copy.deepcopy(snapshot)

        for key in list(self.db.keys()):
            fields = self.db[key]
            for field in list(fields.keys()):
                value, creation_ts, ttl = fields[field]
                remaining_ttl = ttl - (backup_ts - creation_ts)
                if remaining_ttl <= 0:
                    del fields[field]
                    continue
                fields[field] = (value, ts, remaining_ttl)

            if not fields:
                del self.db[key]

        return None
