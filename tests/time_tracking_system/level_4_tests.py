import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from time_tracking_system_impl import TimeTrackingSystemImpl


class TimeTrackingSystemLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = TimeTrackingSystemImpl()

    @timeout(0.4)
    def test_level4_case_01_double_pay_basic(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(2, 5)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 130)

    @timeout(0.4)
    def test_level4_case_02_double_pay_overlap_merge(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(2, 5)
        self.system.set_double_paid(4, 8)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 160)

    @timeout(0.4)
    def test_level4_case_03_double_pay_non_overlap(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(1, 3)
        self.system.set_double_paid(7, 9)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 140)

    @timeout(0.4)
    def test_level4_case_04_double_pay_outside_interval(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(20, 30)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 100)

    @timeout(0.4)
    def test_level4_case_05_invalid_double_pay_interval(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(5, 5)
        self.system.set_double_paid(8, 6)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 100)

    @timeout(0.4)
    def test_level4_case_06_double_pay_full_interval(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(0, 10)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 200)

    @timeout(0.4)
    def test_level4_case_07_double_pay_with_promotion(self):
        self.system.add_worker("w1", "Junior", 10)
        self.system.promote("w1", "Senior", 20, 5)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(4, 6)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 180)

    @timeout(0.4)
    def test_level4_case_08_double_pay_multiple_workers(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.add_worker("w2", "Dev", 5)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.register(0, "w2")
        self.system.register(10, "w2")
        self.system.set_double_paid(2, 4)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 120)
        self.assertEqual(self.system.calc_salary("w2", 0, 10), 60)

    @timeout(0.4)
    def test_level4_case_09_double_pay_across_multiple_sessions(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(5, "w1")
        self.system.register(10, "w1")
        self.system.register(15, "w1")
        self.system.set_double_paid(3, 12)
        self.assertEqual(self.system.calc_salary("w1", 0, 20), 140)

    @timeout(0.4)
    def test_level4_case_10_double_pay_adjacent_intervals_merge(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.system.set_double_paid(2, 4)
        self.system.set_double_paid(4, 6)
        self.assertEqual(self.system.calc_salary("w1", 0, 10), 140)
