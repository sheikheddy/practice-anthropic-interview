import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from in_memory_db_impl import InMemoryDBImpl


class InMemoryDBLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = InMemoryDBImpl()

    @timeout(0.4)
    def test_level1_case_01_set_new_key(self):
        self.assertEqual(self.db.set_or_inc("k", "f", 5), 5)

    @timeout(0.4)
    def test_level1_case_02_increment_existing(self):
        self.db.set_or_inc("k", "f", 5)
        self.assertEqual(self.db.set_or_inc("k", "f", 3), 8)

    @timeout(0.4)
    def test_level1_case_03_get_missing(self):
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level1_case_04_delete_existing(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertTrue(self.db.delete("k", "f"))
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level1_case_05_delete_missing(self):
        self.assertFalse(self.db.delete("k", "f"))

    @timeout(0.4)
    def test_level1_case_06_delete_last_field_removes_key(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.delete("k", "f")
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level1_case_07_negative_increment(self):
        self.db.set_or_inc("k", "f", 10)
        self.assertEqual(self.db.set_or_inc("k", "f", -3), 7)

    @timeout(0.4)
    def test_level1_case_08_add_new_field(self):
        self.db.set_or_inc("k", "f1", 1)
        self.assertEqual(self.db.set_or_inc("k", "f2", 2), 2)
        self.assertEqual(self.db.get("k", "f1"), 1)

    @timeout(0.4)
    def test_level1_case_09_multiple_keys(self):
        self.db.set_or_inc("k1", "f", 1)
        self.db.set_or_inc("k2", "f", 2)
        self.assertEqual(self.db.get("k1", "f"), 1)
        self.assertEqual(self.db.get("k2", "f"), 2)

    @timeout(0.4)
    def test_level1_case_10_increment_missing_field(self):
        self.db.set_or_inc("k", "f1", 1)
        self.assertEqual(self.db.set_or_inc("k", "f2", 5), 5)
