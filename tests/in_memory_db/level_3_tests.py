import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from in_memory_db_impl import InMemoryDBImpl


class InMemoryDBLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = InMemoryDBImpl()

    @timeout(0.4)
    def test_level3_case_01_lock_invalid_key(self):
        self.assertEqual(self.db.lock("u1", "missing"), "invalid_request")

    @timeout(0.4)
    def test_level3_case_02_lock_blocks_set_or_inc(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.lock("u1", "k"), "acquired")
        self.assertEqual(self.db.set_or_inc("k", "f", 5), 1)

    @timeout(0.4)
    def test_level3_case_03_lock_same_caller_noop(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.lock("u1", "k"), "acquired")
        self.assertEqual(self.db.lock("u1", "k"), "")

    @timeout(0.4)
    def test_level3_case_04_unlock_passes_lock(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.lock("u1", "k"), "acquired")
        self.assertEqual(self.db.lock("u2", "k"), "wait")
        self.assertEqual(self.db.unlock("k"), "released")
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 2, "u2"), 3)

    @timeout(0.4)
    def test_level3_case_05_delete_by_caller_wrong_owner(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.assertFalse(self.db.delete_by_caller("k", "f", "u2"))

    @timeout(0.4)
    def test_level3_case_06_delete_by_caller_owner(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.assertTrue(self.db.delete_by_caller("k", "f", "u1"))
        self.assertIsNone(self.db.get("k", "f"))

    @timeout(0.4)
    def test_level3_case_07_set_or_inc_by_caller_owner(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 5, "u1"), 6)

    @timeout(0.4)
    def test_level3_case_08_set_or_inc_by_caller_non_owner(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 5, "u2"), 1)

    @timeout(0.4)
    def test_level3_case_09_unlock_when_not_locked(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.unlock("k"), "")

    @timeout(0.4)
    def test_level3_case_10_unlock_invalid_key(self):
        self.assertEqual(self.db.unlock("missing"), "invalid_request")
