import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from database_impl import DatabaseImpl


class DatabaseLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = DatabaseImpl()

    @timeout(0.4)
    def test_level1_case_01_set_get(self):
        self.db.set("user:1", "name", "Alice")
        self.assertEqual(self.db.get("user:1", "name"), "Alice")

    @timeout(0.4)
    def test_level1_case_02_overwrite_value(self):
        self.db.set("k", "f", "1")
        self.db.set("k", "f", "2")
        self.assertEqual(self.db.get("k", "f"), "2")

    @timeout(0.4)
    def test_level1_case_03_get_missing(self):
        self.assertIsNone(self.db.get("missing", "field"))
        self.db.set("k", "f", "v")
        self.assertIsNone(self.db.get("k", "missing"))

    @timeout(0.4)
    def test_level1_case_04_delete_existing(self):
        self.db.set("k", "f", "v")
        self.assertTrue(self.db.delete("k", "f"))
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level1_case_05_delete_missing(self):
        self.assertFalse(self.db.delete("k", "f"))

    @timeout(0.4)
    def test_level1_case_06_multiple_fields(self):
        self.db.set("k", "a", "1")
        self.db.set("k", "b", "2")
        self.assertTrue(self.db.delete("k", "a"))
        self.assertEqual(self.db.get("k", "b"), "2")

    @timeout(0.4)
    def test_level1_case_07_delete_last_field_removes_key(self):
        self.db.set("k", "a", "1")
        self.assertTrue(self.db.delete("k", "a"))
        self.assertIsNone(self.db.get("k", "a"))
        self.assertIsNone(self.db.get("k", "b"))

    @timeout(0.4)
    def test_level1_case_08_multiple_keys_independent(self):
        self.db.set("k1", "f", "1")
        self.db.set("k2", "f", "2")
        self.assertEqual(self.db.get("k1", "f"), "1")
        self.assertEqual(self.db.get("k2", "f"), "2")

    @timeout(0.4)
    def test_level1_case_09_delete_does_not_affect_other_keys(self):
        self.db.set("k1", "f", "1")
        self.db.set("k2", "f", "2")
        self.assertTrue(self.db.delete("k1", "f"))
        self.assertEqual(self.db.get("k2", "f"), "2")

    @timeout(0.4)
    def test_level1_case_10_set_after_delete(self):
        self.db.set("k", "f", "1")
        self.db.delete("k", "f")
        self.db.set("k", "f", "3")
        self.assertEqual(self.db.get("k", "f"), "3")
