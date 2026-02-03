import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from in_memory_db_impl import InMemoryDBImpl


class InMemoryDBLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = InMemoryDBImpl()

    @timeout(0.4)
    def test_level2_case_01_top_n_single_key(self):
        self.db.set_or_inc("a", "f", 1)
        self.assertEqual(self.db.top_n_keys(1), "a(1)")

    @timeout(0.4)
    def test_level2_case_02_order_by_count(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.assertEqual(self.db.top_n_keys(2), "a(2), b(1)")

    @timeout(0.4)
    def test_level2_case_03_tie_break_by_key(self):
        self.db.set_or_inc("b", "f", 1)
        self.db.set_or_inc("a", "f", 1)
        self.assertEqual(self.db.top_n_keys(2), "a(1), b(1)")

    @timeout(0.4)
    def test_level2_case_04_n_greater_than_keys(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.assertEqual(self.db.top_n_keys(5), "a(1), b(1)")

    @timeout(0.4)
    def test_level2_case_05_delete_increments_modif(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("a", "f", 1)
        self.db.delete("a", "f")
        self.assertEqual(self.db.top_n_keys(1), "a(3)")

    @timeout(0.4)
    def test_level2_case_06_delete_last_field_removes_key_from_ranking(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.delete("a", "f")
        self.assertEqual(self.db.top_n_keys(1), "")

    @timeout(0.4)
    def test_level2_case_07_multiple_fields_modif_counts(self):
        self.db.set_or_inc("a", "f1", 1)
        self.db.set_or_inc("a", "f2", 2)
        self.db.set_or_inc("a", "f2", 1)
        self.assertEqual(self.db.top_n_keys(1), "a(3)")

    @timeout(0.4)
    def test_level2_case_08_empty_db(self):
        self.assertEqual(self.db.top_n_keys(3), "")

    @timeout(0.4)
    def test_level2_case_09_multiple_keys_counts(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.db.set_or_inc("c", "f", 1)
        self.assertEqual(self.db.top_n_keys(2), "b(2), a(1)")

    @timeout(0.4)
    def test_level2_case_10_negative_increment_counts(self):
        self.db.set_or_inc("a", "f", 10)
        self.db.set_or_inc("a", "f", -2)
        self.assertEqual(self.db.top_n_keys(1), "a(2)")
