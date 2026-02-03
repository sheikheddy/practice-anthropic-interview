import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from in_memory_db_impl import InMemoryDBImpl


class InMemoryDBLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = InMemoryDBImpl()

    @timeout(0.4)
    def test_level4_case_01_lock_queue_order(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.lock("u1", "k"), "acquired")
        self.assertEqual(self.db.lock("u2", "k"), "wait")
        self.assertEqual(self.db.lock("u3", "k"), "wait")
        self.assertEqual(self.db.unlock("k"), "released")
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 1, "u2"), 2)
        self.assertEqual(self.db.unlock("k"), "released")
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 1, "u3"), 3)

    @timeout(0.4)
    def test_level4_case_02_delete_removes_lock(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.assertTrue(self.db.delete_by_caller("k", "f", "u1"))
        self.assertEqual(self.db.unlock("k"), "invalid_request")

    @timeout(0.4)
    def test_level4_case_03_modif_counts_with_caller_ops(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.db.set_or_inc_by_caller("k", "f", 1, "u1")
        self.db.delete_by_caller("k", "f", "u1")
        self.assertEqual(self.db.top_n_keys(1), "")

    @timeout(0.4)
    def test_level4_case_04_locked_set_or_inc_no_modif(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.assertEqual(self.db.set_or_inc("k", "f", 5), 1)
        self.assertEqual(self.db.top_n_keys(1), "k(1)")

    @timeout(0.4)
    def test_level4_case_05_lock_same_waiting_caller_noop(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.lock("u1", "k"), "acquired")
        self.assertEqual(self.db.lock("u2", "k"), "wait")
        self.assertEqual(self.db.lock("u2", "k"), "")

    @timeout(0.4)
    def test_level4_case_06_unlock_passes_lock_and_blocks_others(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.db.lock("u2", "k")
        self.db.unlock("k")
        self.assertEqual(self.db.set_or_inc("k", "f", 5), 1)
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 2, "u2"), 3)

    @timeout(0.4)
    def test_level4_case_07_set_or_inc_by_caller_unlocked(self):
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 5, "u1"), 5)
        self.assertEqual(self.db.top_n_keys(1), "k(1)")

    @timeout(0.4)
    def test_level4_case_08_delete_and_lock_invalid(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.db.unlock("k")
        self.assertTrue(self.db.delete("k", "f"))
        self.assertEqual(self.db.lock("u2", "k"), "invalid_request")

    @timeout(0.4)
    def test_level4_case_09_top_n_with_locks(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.db.lock("u1", "a")
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.assertEqual(self.db.top_n_keys(2), "b(2), a(1)")

    @timeout(0.4)
    def test_level4_case_10_delete_by_new_owner_after_unlock(self):
        self.db.set_or_inc("k", "f", 1)
        self.db.lock("u1", "k")
        self.db.lock("u2", "k")
        self.assertFalse(self.db.delete_by_caller("k", "f", "u2"))
        self.db.unlock("k")
        self.assertTrue(self.db.delete_by_caller("k", "f", "u2"))
