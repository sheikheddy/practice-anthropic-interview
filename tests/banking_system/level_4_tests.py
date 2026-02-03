import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from banking_system_impl import BankingSystemImpl


class BankingSystemLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = BankingSystemImpl()

    @timeout(0.4)
    def test_level4_case_01_cancel_at_execution_time_fails(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        payment_id = self.system.schedule_payment(3, "acc", 40, 2)  # exec at 5
        self.assertFalse(self.system.cancel_payment(5, "acc", payment_id))
        self.assertEqual(self.system.deposit(6, "acc", 0), 60)

    @timeout(0.4)
    def test_level4_case_02_processing_before_cancel_same_timestamp(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        payment_id = self.system.schedule_payment(3, "acc", 30, 2)  # exec at 5
        self.assertFalse(self.system.cancel_payment(5, "acc", payment_id))
        self.assertEqual(self.system.deposit(5, "acc", 0), 70)

    @timeout(0.4)
    def test_level4_case_03_cross_account_processing(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 100)
        self.system.deposit(4, "b", 50)
        self.system.schedule_payment(5, "a", 40, 2)  # exec at 7
        # trigger processing via operation on another account
        self.assertEqual(self.system.deposit(8, "b", 0), 50)
        self.assertEqual(self.system.deposit(9, "a", 0), 60)

    @timeout(0.4)
    def test_level4_case_04_top_spenders_includes_scheduled(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 200)
        self.system.deposit(4, "b", 200)
        self.system.schedule_payment(5, "a", 50, 2)
        self.system.pay(6, "b", 40)
        self.system.deposit(7, "a", 0)
        self.assertEqual(self.system.top_spenders(8, 2), ["a", "b"])

    @timeout(0.4)
    def test_level4_case_05_cancel_one_of_multiple(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 200)
        p1 = self.system.schedule_payment(3, "acc", 60, 5)
        p2 = self.system.schedule_payment(4, "acc", 50, 4)
        self.assertTrue(self.system.cancel_payment(5, "acc", p1))
        self.assertEqual(self.system.deposit(8, "acc", 0), 150)
        self.assertFalse(self.system.cancel_payment(9, "acc", p1))
        self.assertFalse(self.system.cancel_payment(9, "acc", p2))

    @timeout(0.4)
    def test_level4_case_06_delay_zero_then_cancel_late(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        payment_id = self.system.schedule_payment(3, "acc", 20, 0)
        self.assertEqual(self.system.deposit(4, "acc", 0), 80)
        self.assertFalse(self.system.cancel_payment(5, "acc", payment_id))

    @timeout(0.4)
    def test_level4_case_07_multiple_payments_insufficient(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 90)
        self.system.schedule_payment(3, "acc", 60, 2)
        self.system.schedule_payment(4, "acc", 60, 1)
        self.assertEqual(self.system.deposit(5, "acc", 0), 30)
        self.assertEqual(self.system.top_spenders(6, 1), ["acc"])

    @timeout(0.4)
    def test_level4_case_08_skipped_payment_not_retried(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 10)
        self.system.schedule_payment(3, "acc", 50, 1)
        self.assertEqual(self.system.deposit(4, "acc", 0), 10)
        self.system.deposit(5, "acc", 100)
        self.assertEqual(self.system.deposit(6, "acc", 0), 110)
        self.assertEqual(self.system.top_spenders(7, 1), [])

    @timeout(0.4)
    def test_level4_case_09_payment_order_same_exec_time(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 70)
        self.system.schedule_payment(3, "acc", 40, 2)  # payment1
        self.system.schedule_payment(4, "acc", 40, 1)  # payment2
        self.assertEqual(self.system.deposit(5, "acc", 0), 30)

    @timeout(0.4)
    def test_level4_case_10_process_pending_before_other_ops(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 100)
        self.system.deposit(4, "b", 100)
        self.system.schedule_payment(5, "a", 50, 1)  # exec at 6
        self.assertEqual(self.system.transfer(6, "b", "a", 10), 90)
        self.assertEqual(self.system.deposit(7, "a", 0), 60)

    @timeout(0.4)
    def test_level4_case_11_all_operations_mixed(self):
        self.assertTrue(self.system.create_account(1, "a"))
        self.assertTrue(self.system.create_account(2, "b"))
        self.assertFalse(self.system.create_account(3, "a"))

        self.assertEqual(self.system.deposit(4, "a", 200), 200)
        self.assertIsNone(self.system.deposit(5, "missing", 10))
        self.assertIsNone(self.system.deposit(6, "a", -1))

        self.assertEqual(self.system.pay(7, "a", 30), 170)
        self.assertIsNone(self.system.pay(8, "a", 0))
        self.assertIsNone(self.system.pay(9, "missing", 10))

        self.assertEqual(self.system.transfer(10, "a", "b", 70), 100)
        self.assertIsNone(self.system.transfer(11, "a", "b", 2000))
        self.assertIsNone(self.system.transfer(12, "a", "a", 10))
        self.assertIsNone(self.system.transfer(13, "a", "missing", 10))

        p1 = self.system.schedule_payment(14, "a", 40, 2)  # exec at 16
        p2 = self.system.schedule_payment(15, "a", 50, 5)  # exec at 20
        self.assertIsNotNone(p1)
        self.assertIsNotNone(p2)

        self.assertTrue(self.system.cancel_payment(17, "a", p2))  # processes p1 first
        self.assertEqual(self.system.deposit(18, "a", 0), 60)
        self.assertEqual(self.system.deposit(19, "b", 0), 70)
        self.assertEqual(self.system.top_spenders(19, 2), ["a"])
        self.assertEqual(self.system.deposit(21, "a", 0), 60)
