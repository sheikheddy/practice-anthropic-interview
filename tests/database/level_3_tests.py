import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from database_impl import DatabaseImpl


class DatabaseLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = DatabaseImpl()

    @timeout(0.4)
    def test_level3_case_01_get_at_before_after_expiry(self):
        self.db.set_at_with_ttl("k", "f", "v", 10, 5)  # expires at 15
        self.assertEqual(self.db.get_at("k", "f", 14), "v")
        self.assertIsNone(self.db.get_at("k", "f", 15))

    @timeout(0.4)
    def test_level3_case_02_delete_at_after_expiry(self):
        self.db.set_at_with_ttl("k", "f", "v", 10, 5)
        self.assertFalse(self.db.delete_at("k", "f", 15))

    @timeout(0.4)
    def test_level3_case_03_scan_at_excludes_expired(self):
        self.db.set_at_with_ttl("k", "a", "1", 0, 5)
        self.db.set_at_with_ttl("k", "b", "2", 0, 10)
        self.assertEqual(self.db.scan_at("k", 6), "b(2)")

    @timeout(0.4)
    def test_level3_case_04_scan_by_prefix_at(self):
        self.db.set_at_with_ttl("k", "ab", "1", 0, 5)
        self.db.set_at_with_ttl("k", "ac", "2", 0, 10)
        self.db.set_at_with_ttl("k", "b", "3", 0, 10)
        self.assertEqual(self.db.scan_by_prefix_at("k", "a", 6), "ac(2)")

    @timeout(0.4)
    def test_level3_case_05_set_at_infinite_ttl(self):
        self.db.set_at("k", "f", "v", 10)
        self.assertEqual(self.db.get_at("k", "f", 1000), "v")

    @timeout(0.4)
    def test_level3_case_06_ttl_zero_expires_immediately(self):
        self.db.set_at_with_ttl("k", "f", "v", 10, 0)
        self.assertIsNone(self.db.get_at("k", "f", 10))

    @timeout(0.4)
    def test_level3_case_07_overwrite_resets_ttl(self):
        self.db.set_at_with_ttl("k", "f", "v1", 0, 5)
        self.db.set_at_with_ttl("k", "f", "v2", 4, 10)  # expires at 14
        self.assertEqual(self.db.get_at("k", "f", 13), "v2")
        self.assertIsNone(self.db.get_at("k", "f", 14))

    @timeout(0.4)
    def test_level3_case_08_multiple_fields_different_ttl(self):
        self.db.set_at_with_ttl("k", "a", "1", 0, 3)
        self.db.set_at_with_ttl("k", "b", "2", 0, 6)
        self.assertEqual(self.db.scan_at("k", 2), "a(1), b(2)")
        self.assertEqual(self.db.scan_at("k", 4), "b(2)")

    @timeout(0.4)
    def test_level3_case_09_delete_at_unexpired(self):
        self.db.set_at_with_ttl("k", "f", "v", 0, 10)
        self.assertTrue(self.db.delete_at("k", "f", 5))
        self.assertIsNone(self.db.get_at("k", "f", 5))

    @timeout(0.4)
    def test_level3_case_10_get_at_missing(self):
        self.assertIsNone(self.db.get_at("missing", "f", 0))
