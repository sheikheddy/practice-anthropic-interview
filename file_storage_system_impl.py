import copy


class FileStorageSystemImpl:
    """
    An in-memory implementation of a simplified file storage system.
    """

    _INF_CAPACITY = 10**18

    def __init__(self):
        """
        Initializes the data structures for the file system.
        - self.files: Stores file paths and their sizes.
        - self.users: Stores user IDs and their remaining storage capacity.
        - self.file_ownership: Maps each file path to its owner's user ID.
        - self.user_files: Stores per-user file maps.
        - self.backups: Stores per-user backups of file ownership.
        """
        self.files = {}  # {file_path: size}
        self.users = {"admin": self._INF_CAPACITY}  # {user_id: remaining_capacity}
        self.file_ownership = {}  # {file_path: user_id}
        self.user_files = {"admin": {}}  # {user_id: {file_path: size}}
        self.backups = {}  # {user_id: {file_path: size}}
        self.backup_caps = {}  # {user_id: remaining_capacity}

    def add_file(self, file_path: str, file_size: int) -> bool:
        """
        Creates a new file owned by the 'admin' user.
        """
        return self.add_file_by_user(file_path, "admin", file_size) is not None

    def delete_file(self, file_path: str) -> int | None:
        """
        Deletes a file and restores capacity to its owner.
        """
        if file_path not in self.files:
            return None

        size = self.files[file_path]
        owner = self.file_ownership.get(file_path)

        if owner in self.users:
            self.users[owner] += size
        if owner in self.user_files and file_path in self.user_files[owner]:
            del self.user_files[owner][file_path]

        del self.files[file_path]
        del self.file_ownership[file_path]
        return size

    def get_file_size(self, file_path: str) -> int | None:
        """
        Retrieves the size of a specified file.
        """
        if file_path not in self.files:
            return None
        return self.files[file_path]

    def get_n_files_by_prefix(self, prefix: str, count: int) -> str:
        """
        Finds and ranks files matching a given prefix.
        """
        candidates = {
            path: size for path, size in self.files.items() if path.startswith(prefix)
        }
        sorted_items = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))
        top_items = sorted_items[:int(count)]
        formatted_results = [f"{path}({size})" for path, size in top_items]
        return ", ".join(formatted_results)

    def add_user(self, user_id: str, capacity: int) -> bool:
        """
        Creates a new user with a specified storage capacity.
        """
        if user_id in self.users:
            return False
        self.users[user_id] = int(capacity)
        self.user_files[user_id] = {}
        return True

    def add_file_by_user(self, file_path: str, user_id: str, file_size: int) -> int | None:
        """
        Adds a file on behalf of a specific user, deducting from their capacity.
        """
        size = int(file_size)

        if user_id not in self.users:
            return None
        if file_path in self.files:
            return None
        if size > self.users[user_id]:
            return None

        self.files[file_path] = size
        self.file_ownership[file_path] = user_id
        self.user_files.setdefault(user_id, {})[file_path] = size
        self.users[user_id] -= size
        return self.users[user_id]

    def merge_users(self, target_user_id: str, source_user_id: str) -> int | None:
        """
        Merges the source user's files and capacity into the target user.
        """
        if target_user_id not in self.users or source_user_id not in self.users:
            return None
        if target_user_id == source_user_id:
            return None

        self.users[target_user_id] += self.users[source_user_id]

        for path, owner in list(self.file_ownership.items()):
            if owner == source_user_id:
                self.file_ownership[path] = target_user_id
                self.user_files.setdefault(target_user_id, {})[path] = self.files[path]
        if source_user_id in self.user_files:
            del self.user_files[source_user_id]

        if source_user_id in self.backups:
            del self.backups[source_user_id]
        if source_user_id in self.backup_caps:
            del self.backup_caps[source_user_id]

        del self.users[source_user_id]
        return self.users[target_user_id]

    def backup_user(self, user_id: str) -> int | None:
        """
        Creates or updates a user's backup.
        """
        if user_id not in self.users:
            return None

        files_snapshot = copy.deepcopy(self.user_files.get(user_id, {}))
        self.backups[user_id] = files_snapshot
        self.backup_caps[user_id] = self.users[user_id]
        return len(files_snapshot)

    def restore_user(self, user_id: str) -> int | None:
        """
        Restores a user's files from backup. Files already owned by others are skipped.
        """
        if user_id not in self.users:
            return None

        # Remove all current files owned by the user.
        current_items = list(self.user_files.get(user_id, {}).items())
        for path, size in current_items:
            if path in self.files:
                del self.files[path]
            if path in self.file_ownership:
                del self.file_ownership[path]
        self.user_files[user_id] = {}

        if user_id not in self.backups:
            # Restore capacity after removing files.
            for _, size in current_items:
                self.users[user_id] += size
            return 0

        self.users[user_id] = self.backup_caps[user_id]
        restored_count = 0

        for path, size in self.backups[user_id].items():
            owner = self.file_ownership.get(path)
            if owner is not None and owner != user_id:
                # File already taken by another user; capacity should be freed.
                self.users[user_id] += size
                continue

            self.files[path] = size
            self.file_ownership[path] = user_id
            self.user_files[user_id][path] = size
            restored_count += 1

        return restored_count
