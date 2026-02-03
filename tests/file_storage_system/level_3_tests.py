import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from file_storage_system_impl import FileStorageSystemImpl


class FileStorageSystemLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.storage = FileStorageSystemImpl()

    @timeout(0.4)
    def test_level3_case_01_add_user_duplicate(self):
        self.assertTrue(self.storage.add_user("u1", 100))
        self.assertFalse(self.storage.add_user("u1", 200))

    @timeout(0.4)
    def test_level3_case_02_add_file_by_user_success(self):
        self.storage.add_user("u1", 100)
        remaining = self.storage.add_file_by_user("/u1/a.txt", "u1", 40)
        self.assertEqual(remaining, 60)
        self.assertEqual(self.storage.get_file_size("/u1/a.txt"), 40)

    @timeout(0.4)
    def test_level3_case_03_add_file_by_user_missing_user(self):
        self.assertIsNone(self.storage.add_file_by_user("/u1/a.txt", "missing", 10))

    @timeout(0.4)
    def test_level3_case_04_add_file_by_user_duplicate_path(self):
        self.storage.add_user("u1", 100)
        self.assertIsNotNone(self.storage.add_file_by_user("/u1/a.txt", "u1", 10))
        self.assertIsNone(self.storage.add_file_by_user("/u1/a.txt", "u1", 5))

    @timeout(0.4)
    def test_level3_case_05_add_file_by_user_over_capacity(self):
        self.storage.add_user("u1", 50)
        self.assertIsNone(self.storage.add_file_by_user("/u1/a.txt", "u1", 60))
        self.assertIsNotNone(self.storage.add_file_by_user("/u1/a.txt", "u1", 50))

    @timeout(0.4)
    def test_level3_case_06_merge_users_transfers_capacity_and_files(self):
        self.storage.add_user("u1", 100)
        self.storage.add_user("u2", 50)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 40)  # u1 remaining 60
        self.storage.add_file_by_user("/u2/b.txt", "u2", 20)  # u2 remaining 30
        merged = self.storage.merge_users("u1", "u2")
        self.assertEqual(merged, 90)
        self.assertEqual(self.storage.get_file_size("/u2/b.txt"), 20)
        self.assertIsNone(self.storage.add_file_by_user("/u2/c.txt", "u2", 5))
        self.assertEqual(self.storage.add_file_by_user("/u1/c.txt", "u1", 90), 0)

    @timeout(0.4)
    def test_level3_case_07_merge_users_missing_user(self):
        self.storage.add_user("u1", 100)
        self.assertIsNone(self.storage.merge_users("u1", "missing"))
        self.assertIsNone(self.storage.merge_users("missing", "u1"))

    @timeout(0.4)
    def test_level3_case_08_merge_users_same_user(self):
        self.storage.add_user("u1", 100)
        self.assertIsNone(self.storage.merge_users("u1", "u1"))

    @timeout(0.4)
    def test_level3_case_09_merge_users_no_files(self):
        self.storage.add_user("u1", 70)
        self.storage.add_user("u2", 30)
        merged = self.storage.merge_users("u1", "u2")
        self.assertEqual(merged, 100)
        self.assertIsNone(self.storage.add_file_by_user("/u2/a.txt", "u2", 1))

    @timeout(0.4)
    def test_level3_case_10_delete_file_restores_capacity(self):
        self.storage.add_user("u1", 50)
        self.storage.add_file_by_user("/u1/a.txt", "u1", 30)
        self.assertEqual(self.storage.delete_file("/u1/a.txt"), 30)
        self.assertEqual(self.storage.add_file_by_user("/u1/b.txt", "u1", 50), 0)
