import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from database_impl import DatabaseImpl


class DatabaseLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = DatabaseImpl()

    @timeout(0.4)
    def test_level2_case_01_scan_sorted(self):
        self.db.set("k", "b", "2")
        self.db.set("k", "a", "1")
        self.db.set("k", "c", "3")
        self.assertEqual(self.db.scan("k"), "a(1), b(2), c(3)")

    @timeout(0.4)
    def test_level2_case_02_scan_missing_key(self):
        self.assertEqual(self.db.scan("missing"), "")

    @timeout(0.4)
    def test_level2_case_03_scan_by_prefix_basic(self):
        self.db.set("k", "name", "Alice")
        self.db.set("k", "nation", "US")
        self.db.set("k", "age", "30")
        self.assertEqual(self.db.scan_by_prefix("k", "na"), "name(Alice), nation(US)")

    @timeout(0.4)
    def test_level2_case_04_scan_by_prefix_no_match(self):
        self.db.set("k", "a", "1")
        self.assertEqual(self.db.scan_by_prefix("k", "z"), "")

    @timeout(0.4)
    def test_level2_case_05_scan_after_delete(self):
        self.db.set("k", "a", "1")
        self.db.set("k", "b", "2")
        self.db.delete("k", "a")
        self.assertEqual(self.db.scan("k"), "b(2)")

    @timeout(0.4)
    def test_level2_case_06_scan_by_prefix_all(self):
        self.db.set("k", "x", "1")
        self.db.set("k", "y", "2")
        self.assertEqual(self.db.scan_by_prefix("k", ""), "x(1), y(2)")

    @timeout(0.4)
    def test_level2_case_07_scan_by_prefix_partial(self):
        self.db.set("k", "ab", "1")
        self.db.set("k", "ac", "2")
        self.db.set("k", "b", "3")
        self.assertEqual(self.db.scan_by_prefix("k", "a"), "ab(1), ac(2)")

    @timeout(0.4)
    def test_level2_case_08_scan_multiple_keys(self):
        self.db.set("k1", "a", "1")
        self.db.set("k2", "a", "2")
        self.assertEqual(self.db.scan("k1"), "a(1)")
        self.assertEqual(self.db.scan("k2"), "a(2)")

    @timeout(0.4)
    def test_level2_case_09_scan_numeric_fields(self):
        self.db.set("k", "1", "one")
        self.db.set("k", "10", "ten")
        self.db.set("k", "2", "two")
        self.assertEqual(self.db.scan("k"), "1(one), 10(ten), 2(two)")

    @timeout(0.4)
    def test_level2_case_10_scan_after_overwrite(self):
        self.db.set("k", "a", "1")
        self.db.set("k", "a", "2")
        self.assertEqual(self.db.scan("k"), "a(2)")
