import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from banking_system_impl import BankingSystemImpl


class BankingSystemLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = BankingSystemImpl()

    @timeout(0.4)
    def test_level3_case_01_schedule_payment_basic(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 200)
        payment_id = self.system.schedule_payment(3, "acc", 50, 5)
        self.assertEqual(payment_id, "payment1")
        self.assertEqual(self.system.deposit(7, "acc", 0), 200)
        self.assertEqual(self.system.deposit(8, "acc", 0), 150)

    @timeout(0.4)
    def test_level3_case_02_schedule_invalid_inputs(self):
        self.system.create_account(1, "acc")
        self.assertIsNone(self.system.schedule_payment(2, "missing", 10, 1))
        self.assertIsNone(self.system.schedule_payment(3, "acc", -10, 1))
        self.assertIsNone(self.system.schedule_payment(4, "acc", 10, -1))

    @timeout(0.4)
    def test_level3_case_03_skip_insufficient_funds(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 20)
        payment_id = self.system.schedule_payment(3, "acc", 50, 2)
        self.assertEqual(payment_id, "payment1")
        self.assertEqual(self.system.deposit(5, "acc", 0), 20)
        self.assertEqual(self.system.deposit(10, "acc", 100), 120)
        self.assertEqual(self.system.top_spenders(11, 1), [])

    @timeout(0.4)
    def test_level3_case_04_cancel_success(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        payment_id = self.system.schedule_payment(3, "acc", 40, 10)
        self.assertTrue(self.system.cancel_payment(4, "acc", payment_id))
        self.assertEqual(self.system.deposit(20, "acc", 0), 100)

    @timeout(0.4)
    def test_level3_case_05_cancel_wrong_account(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 100)
        payment_id = self.system.schedule_payment(4, "a", 30, 5)
        self.assertFalse(self.system.cancel_payment(5, "b", payment_id))

    @timeout(0.4)
    def test_level3_case_06_cancel_nonexistent(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        self.assertFalse(self.system.cancel_payment(3, "acc", "payment999"))

    @timeout(0.4)
    def test_level3_case_07_cancel_after_execution(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        payment_id = self.system.schedule_payment(3, "acc", 60, 2)
        self.assertEqual(self.system.deposit(5, "acc", 0), 40)
        self.assertFalse(self.system.cancel_payment(6, "acc", payment_id))

    @timeout(0.4)
    def test_level3_case_08_multiple_payments_order(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        p1 = self.system.schedule_payment(3, "acc", 60, 2)
        p2 = self.system.schedule_payment(4, "acc", 50, 1)
        self.assertEqual(p1, "payment1")
        self.assertEqual(p2, "payment2")
        # exec at t=5 for p1 and t=5 for p2; order by payment id
        self.assertEqual(self.system.deposit(5, "acc", 0), 40)
        self.assertEqual(self.system.top_spenders(6, 1), ["acc"])

    @timeout(0.4)
    def test_level3_case_09_delay_zero_executes_on_next_op(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 100)
        payment_id = self.system.schedule_payment(3, "acc", 30, 0)
        self.assertEqual(payment_id, "payment1")
        # next operation at same timestamp should process
        self.assertEqual(self.system.deposit(3, "acc", 0), 70)

    @timeout(0.4)
    def test_level3_case_10_cancel_after_skip(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 10)
        payment_id = self.system.schedule_payment(3, "acc", 50, 1)
        self.assertEqual(self.system.deposit(4, "acc", 0), 10)
        self.assertFalse(self.system.cancel_payment(5, "acc", payment_id))
