import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from database_impl import DatabaseImpl


class DatabaseLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = DatabaseImpl()

    @timeout(0.4)
    def test_level4_case_01_backup_counts_non_expired_keys(self):
        self.db.set_at_with_ttl("k1", "a", "1", 0, 10)
        self.db.set_at_with_ttl("k2", "b", "2", 0, 5)
        self.assertEqual(self.db.backup(6), 1)

    @timeout(0.4)
    def test_level4_case_02_restore_without_backup_clears(self):
        self.db.set("k", "f", "v")
        self.db.restore(10, 5)
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level4_case_03_restore_uses_latest_snapshot(self):
        self.db.set_at_with_ttl("k", "f", "v1", 0, 10)
        self.db.backup(5)
        self.db.set_at_with_ttl("k", "f", "v2", 6, 10)
        self.db.backup(10)
        self.db.restore(20, 7)  # should use backup at 5
        self.assertEqual(self.db.get_at("k", "f", 20), "v1")

    @timeout(0.4)
    def test_level4_case_04_restore_adjusts_ttl(self):
        self.db.set_at_with_ttl("k", "f", "v", 10, 10)  # expires at 20
        self.db.backup(15)
        self.db.restore(25, 15)
        self.assertEqual(self.db.get_at("k", "f", 29), "v")
        self.assertIsNone(self.db.get_at("k", "f", 30))

    @timeout(0.4)
    def test_level4_case_05_restore_drops_expired_fields(self):
        self.db.set_at_with_ttl("k", "f", "v", 0, 5)
        self.db.backup(10)
        self.db.restore(20, 10)
        self.assertIsNone(self.db.get_at("k", "f", 20))

    @timeout(0.4)
    def test_level4_case_06_restore_removes_new_fields(self):
        self.db.set_at_with_ttl("k", "a", "1", 0, 10)
        self.db.backup(5)
        self.db.set_at_with_ttl("k", "b", "2", 6, 10)
        self.db.restore(20, 5)
        self.assertEqual(self.db.scan_at("k", 20), "a(1)")

    @timeout(0.4)
    def test_level4_case_07_restore_preserves_multiple_fields(self):
        self.db.set_at_with_ttl("k", "a", "1", 0, 10)
        self.db.set_at_with_ttl("k", "b", "2", 0, 10)
        self.db.backup(5)
        self.db.restore(20, 5)
        self.assertEqual(self.db.scan_at("k", 20), "a(1), b(2)")

    @timeout(0.4)
    def test_level4_case_08_restore_before_any_backup(self):
        self.db.set("k", "f", "v")
        self.db.backup(10)
        self.db.restore(20, 1)  # before first backup
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level4_case_09_backup_key_with_partial_expiry(self):
        self.db.set_at_with_ttl("k", "a", "1", 0, 5)
        self.db.set_at_with_ttl("k", "b", "2", 0, 10)
        self.assertEqual(self.db.backup(6), 1)

    @timeout(0.4)
    def test_level4_case_10_restore_multiple_keys(self):
        self.db.set_at_with_ttl("k1", "a", "1", 0, 10)
        self.db.set_at_with_ttl("k2", "b", "2", 0, 10)
        self.db.backup(5)
        self.db.restore(20, 5)
        self.assertEqual(self.db.get_at("k1", "a", 20), "1")
        self.assertEqual(self.db.get_at("k2", "b", 20), "2")
