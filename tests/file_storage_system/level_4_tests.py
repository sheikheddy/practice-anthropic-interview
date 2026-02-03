import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from file_storage_system_impl import FileStorageSystemImpl


class FileStorageSystemLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.storage = FileStorageSystemImpl()

    @timeout(0.4)
    def test_level4_case_01_backup_basic(self):
        self.storage.add_user("u1", 100)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 40)
        self.storage.add_file_by_user("/u1/b.txt", "u1", 20)
        self.assertEqual(self.storage.backup_user("u1"), 2)

    @timeout(0.4)
    def test_level4_case_02_restore_basic(self):
        self.storage.add_user("u1", 100)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 40)
        self.storage.add_file_by_user("/u1/b.txt", "u1", 30)
        self.storage.backup_user("u1")
        self.storage.delete_file("/u1/b.txt")
        restored = self.storage.restore_user("u1")
        self.assertEqual(restored, 2)
        self.assertEqual(self.storage.get_file_size("/u1/a.txt"), 40)
        self.assertEqual(self.storage.get_file_size("/u1/b.txt"), 30)

    @timeout(0.4)
    def test_level4_case_03_restore_no_backup(self):
        self.storage.add_user("u1", 50)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 20)
        self.assertEqual(self.storage.restore_user("u1"), 0)
        self.assertIsNone(self.storage.get_file_size("/u1/a.txt"))
        self.assertEqual(self.storage.add_file_by_user("/u1/b.txt", "u1", 50), 0)

    @timeout(0.4)
    def test_level4_case_04_multiple_users_backup_restore(self):
        self.storage.add_user("u1", 100)
        self.storage.add_user("u2", 80)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 40)
        self.storage.add_file_by_user("/u2/b.txt", "u2", 30)
        self.storage.backup_user("u1")
        self.storage.backup_user("u2")
        self.storage.delete_file("/u1/a.txt")
        self.storage.delete_file("/u2/b.txt")
        self.assertEqual(self.storage.restore_user("u1"), 1)
        self.assertEqual(self.storage.restore_user("u2"), 1)
        self.assertEqual(self.storage.get_file_size("/u1/a.txt"), 40)
        self.assertEqual(self.storage.get_file_size("/u2/b.txt"), 30)

    @timeout(0.4)
    def test_level4_case_05_multiple_backups(self):
        self.storage.add_user("u1", 100)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 10)
        self.assertEqual(self.storage.backup_user("u1"), 1)
        self.storage.add_file_by_user("/u1/b.txt", "u1", 20)
        self.assertEqual(self.storage.backup_user("u1"), 2)
        self.storage.delete_file("/u1/a.txt")
        restored = self.storage.restore_user("u1")
        self.assertEqual(restored, 2)
        self.assertEqual(self.storage.get_file_size("/u1/a.txt"), 10)
        self.assertEqual(self.storage.get_file_size("/u1/b.txt"), 20)

    @timeout(0.4)
    def test_level4_case_06_unexisting_users(self):
        self.assertIsNone(self.storage.backup_user("missing"))
        self.assertIsNone(self.storage.restore_user("missing"))

    @timeout(0.4)
    def test_level4_case_07_mixed_conflict_restore(self):
        self.storage.add_user("u1", 100)
        self.storage.add_user("u2", 100)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 40)
        self.storage.backup_user("u1")
        self.storage.delete_file("/u1/a.txt")
        self.storage.add_file_by_user("/u1/a.txt", "u2", 40)
        restored = self.storage.restore_user("u1")
        self.assertEqual(restored, 0)
        self.assertEqual(self.storage.add_file_by_user("/u1/new.txt", "u1", 100), 0)

    @timeout(0.4)
    def test_level4_case_08_mixed_restore_removes_new_files(self):
        self.storage.add_user("u1", 100)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 30)
        self.storage.add_file_by_user("/u1/b.txt", "u1", 20)
        self.storage.backup_user("u1")
        self.storage.delete_file("/u1/a.txt")
        self.storage.add_file_by_user("/u1/c.txt", "u1", 10)
        restored = self.storage.restore_user("u1")
        self.assertEqual(restored, 2)
        self.assertEqual(self.storage.get_file_size("/u1/a.txt"), 30)
        self.assertEqual(self.storage.get_file_size("/u1/b.txt"), 20)
        self.assertIsNone(self.storage.get_file_size("/u1/c.txt"))

    @timeout(0.4)
    def test_level4_case_09_restore_does_not_affect_others(self):
        self.storage.add_user("u1", 100)
        self.storage.add_user("u2", 100)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 30)
        self.storage.add_file_by_user("/u2/b.txt", "u2", 40)
        self.storage.backup_user("u1")
        self.storage.delete_file("/u1/a.txt")
        restored = self.storage.restore_user("u1")
        self.assertEqual(restored, 1)
        self.assertEqual(self.storage.get_file_size("/u2/b.txt"), 40)

    @timeout(0.4)
    def test_level4_case_10_mixed_empty_backup(self):
        self.storage.add_user("u1", 50)
        self.assertEqual(self.storage.backup_user("u1"), 0)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 20)
        self.assertEqual(self.storage.restore_user("u1"), 0)
        self.assertIsNone(self.storage.get_file_size("/u1/a.txt"))
