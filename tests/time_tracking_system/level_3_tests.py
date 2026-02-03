import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from time_tracking_system_impl import TimeTrackingSystemImpl


class TimeTrackingSystemLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = TimeTrackingSystemImpl()

    @timeout(0.4)
    def test_level3_case_01_promote_invalid_worker(self):
        self.assertEqual(self.system.promote("missing", "Senior", 200, 10), "invalid_request")

    @timeout(0.4)
    def test_level3_case_02_promote_pending_rejected(self):
        self.system.add_worker("w1", "Junior", 100)
        self.assertEqual(self.system.promote("w1", "Senior", 200, 10), "success")
        self.assertEqual(self.system.promote("w1", "Lead", 300, 20), "invalid_request")

    @timeout(0.4)
    def test_level3_case_03_activation_at_effective_timestamp(self):
        self.system.add_worker("w1", "Junior", 100)
        self.assertEqual(self.system.promote("w1", "Senior", 200, 50), "success")
        self.assertEqual(self.system.register(50, "w1"), "registered")
        self.assertIsNone(self.system.get("w1"))
        self.system.register(60, "w1")
        self.system.register(70, "w1")
        self.assertEqual(self.system.get("w1"), 10)

    @timeout(0.4)
    def test_level3_case_04_calc_salary_no_intervals(self):
        self.system.add_worker("w1", "Dev", 100)
        self.assertEqual(self.system.calc_salary("w1", 0, 100), 0)

    @timeout(0.4)
    def test_level3_case_05_calc_salary_missing_worker(self):
        self.assertIsNone(self.system.calc_salary("missing", 0, 10))

    @timeout(0.4)
    def test_level3_case_06_calc_salary_across_promotion(self):
        self.system.add_worker("w1", "Junior", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.assertEqual(self.system.promote("w1", "Senior", 20, 15), "success")
        self.system.register(15, "w1")
        self.system.register(20, "w1")
        self.system.register(30, "w1")
        self.assertEqual(self.system.calc_salary("w1", 0, 30), 300)

    @timeout(0.4)
    def test_level3_case_07_promotion_splits_interval(self):
        self.system.add_worker("w1", "Junior", 10)
        self.assertEqual(self.system.promote("w1", "Senior", 20, 50), "success")
        self.system.register(40, "w1")
        self.system.register(60, "w1")
        self.assertEqual(self.system.calc_salary("w1", 0, 100), 300)

    @timeout(0.4)
    def test_level3_case_08_promotion_not_active_before_effective(self):
        self.system.add_worker("w1", "Junior", 10)
        self.assertEqual(self.system.promote("w1", "Senior", 20, 50), "success")
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.assertEqual(self.system.calc_salary("w1", 0, 20), 100)

    @timeout(0.4)
    def test_level3_case_09_top_n_after_promotion(self):
        self.system.add_worker("w1", "Junior", 100)
        self.system.promote("w1", "Senior", 200, 10)
        self.system.register(10, "w1")
        self.assertEqual(self.system.top_n_workers(1, "Senior"), "w1(0)")

    @timeout(0.4)
    def test_level3_case_10_calc_salary_partial_range(self):
        self.system.add_worker("w1", "Dev", 10)
        self.system.register(0, "w1")
        self.system.register(10, "w1")
        self.assertEqual(self.system.calc_salary("w1", 5, 8), 30)
