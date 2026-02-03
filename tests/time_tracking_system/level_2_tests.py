import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from time_tracking_system_impl import TimeTrackingSystemImpl


class TimeTrackingSystemLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = TimeTrackingSystemImpl()

    @timeout(0.4)
    def test_level2_case_01_basic_ranking(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.add_worker("w2", "Dev", 100)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.register(0, "w2")
        self.system.register(30, "w2")
        self.assertEqual(self.system.top_n_workers(2, "Dev"), "w2(30), w1(10)")

    @timeout(0.4)
    def test_level2_case_02_tie_breaker(self):
        self.system.add_worker("a", "QA", 100)
        self.system.add_worker("b", "QA", 100)
        self.system.register(0, "b")
        self.system.register(10, "b")
        self.system.register(0, "a")
        self.system.register(10, "a")
        self.assertEqual(self.system.top_n_workers(2, "QA"), "a(10), b(10)")

    @timeout(0.4)
    def test_level2_case_03_no_matching_position(self):
        self.system.add_worker("w1", "Dev", 100)
        self.assertEqual(self.system.top_n_workers(2, "QA"), "")

    @timeout(0.4)
    def test_level2_case_04_includes_zero_time_workers(self):
        self.system.add_worker("w1", "Dev", 100)
        self.assertEqual(self.system.top_n_workers(1, "Dev"), "w1(0)")

    @timeout(0.4)
    def test_level2_case_05_n_greater_than_workers(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.add_worker("w2", "Dev", 100)
        result = self.system.top_n_workers(5, "Dev")
        self.assertEqual(result, "w1(0), w2(0)")

    @timeout(0.4)
    def test_level2_case_06_filter_by_position(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.add_worker("w2", "QA", 100)
        self.system.register(0, "w2")
        self.system.register(10, "w2")
        self.assertEqual(self.system.top_n_workers(2, "Dev"), "w1(0)")

    @timeout(0.4)
    def test_level2_case_07_multiple_sessions(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.register(20, "w1")
        self.system.register(40, "w1")
        self.assertEqual(self.system.top_n_workers(1, "Dev"), "w1(30)")

    @timeout(0.4)
    def test_level2_case_08_mixed_workers(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.add_worker("w2", "Dev", 100)
        self.system.add_worker("w3", "Dev", 100)
        self.system.register(0, "w1")
        self.system.register(5, "w1")
        self.system.register(0, "w2")
        self.system.register(20, "w2")
        self.system.register(0, "w3")
        self.system.register(10, "w3")
        self.assertEqual(self.system.top_n_workers(2, "Dev"), "w2(20), w3(10)")

    @timeout(0.4)
    def test_level2_case_09_zero_time_tie_order(self):
        self.system.add_worker("b", "Dev", 100)
        self.system.add_worker("a", "Dev", 100)
        self.assertEqual(self.system.top_n_workers(2, "Dev"), "a(0), b(0)")

    @timeout(0.4)
    def test_level2_case_10_top_one(self):
        self.system.add_worker("w1", "Dev", 100)
        self.system.add_worker("w2", "Dev", 100)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.register(0, "w2")
        self.system.register(5, "w2")
        self.assertEqual(self.system.top_n_workers(1, "Dev"), "w1(10)")
