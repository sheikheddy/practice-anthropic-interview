import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from time_tracking_system_impl import TimeTrackingSystemImpl


class TimeTrackingSystemLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = TimeTrackingSystemImpl()

    @timeout(0.4)
    def test_level1_case_01_add_worker_duplicate(self):
        self.assertTrue(self.system.add_worker("w1", "Dev", 100))
        self.assertFalse(self.system.add_worker("w1", "QA", 80))

    @timeout(0.4)
    def test_level1_case_02_register_invalid(self):
        self.assertEqual(self.system.register(10, "missing"), "invalid_request")

    @timeout(0.4)
    def test_level1_case_03_register_and_get(self):
        self.system.add_worker("w1", "Dev", 100)
        self.assertEqual(self.system.register(10, "w1"), "registered")
        self.assertEqual(self.system.register(20, "w1"), "registered")
        self.assertEqual(self.system.get("w1"), 10)

    @timeout(0.4)
    def test_level1_case_04_incomplete_session(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.register(10, "w1")
        self.assertIsNone(self.system.get("w1"))

    @timeout(0.4)
    def test_level1_case_05_multiple_sessions_sum(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.register(10, "w1")
        self.system.register(20, "w1")
        self.system.register(30, "w1")
        self.system.register(50, "w1")
        self.assertEqual(self.system.get("w1"), 30)

    @timeout(0.4)
    def test_level1_case_06_get_missing_worker(self):
        self.assertIsNone(self.system.get("missing"))

    @timeout(0.4)
    def test_level1_case_07_multiple_workers_independent(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.add_worker("w2", "QA", 80)
        self.system.register(10, "w1")
        self.system.register(20, "w1")
        self.system.register(15, "w2")
        self.system.register(25, "w2")
        self.assertEqual(self.system.get("w1"), 10)
        self.assertEqual(self.system.get("w2"), 10)

    @timeout(0.4)
    def test_level1_case_08_incomplete_then_complete(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.register(10, "w1")
        self.system.register(20, "w1")
        self.system.register(30, "w1")
        self.assertEqual(self.system.get("w1"), 10)

    @timeout(0.4)
    def test_level1_case_09_zero_length_session(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.register(10, "w1")
        self.system.register(10, "w1")
        self.assertEqual(self.system.get("w1"), 0)

    @timeout(0.4)
    def test_level1_case_10_register_returns_registered(self):
        self.system.add_worker("w1", "Dev", 100)
        self.assertEqual(self.system.register(1, "w1"), "registered")
        self.assertEqual(self.system.register(2, "w1"), "registered")
