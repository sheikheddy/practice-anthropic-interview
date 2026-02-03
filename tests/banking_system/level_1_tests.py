import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from banking_system_impl import BankingSystemImpl


class BankingSystemLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = BankingSystemImpl()

    @timeout(0.4)
    def test_level1_case_01_create_account_duplicate(self):
        self.assertTrue(self.system.create_account(1, "acc1"))
        self.assertFalse(self.system.create_account(2, "acc1"))

    @timeout(0.4)
    def test_level1_case_02_deposit_valid_invalid(self):
        self.system.create_account(1, "acc")
        self.assertEqual(self.system.deposit(2, "acc", 100), 100)
        self.assertIsNone(self.system.deposit(3, "missing", 50))
        self.assertIsNone(self.system.deposit(4, "acc", -1))

    @timeout(0.4)
    def test_level1_case_03_pay_basic(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 200)
        self.assertIsNone(self.system.pay(3, "acc", 0))
        self.assertIsNone(self.system.pay(4, "acc", -5))
        self.assertIsNone(self.system.pay(5, "missing", 10))
        self.assertEqual(self.system.pay(6, "acc", 50), 150)

    @timeout(0.4)
    def test_level1_case_04_pay_insufficient(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 30)
        self.assertIsNone(self.system.pay(3, "acc", 40))
        self.assertEqual(self.system.deposit(4, "acc", 0), 30)

    @timeout(0.4)
    def test_level1_case_05_transfer_success(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 100)
        self.assertEqual(self.system.transfer(4, "a", "b", 40), 60)
        self.assertEqual(self.system.deposit(5, "b", 0), 40)

    @timeout(0.4)
    def test_level1_case_06_transfer_invalid(self):
        self.system.create_account(1, "a")
        self.system.deposit(2, "a", 100)
        self.assertIsNone(self.system.transfer(3, "a", "missing", 10))
        self.assertIsNone(self.system.transfer(4, "missing", "a", 10))
        self.assertIsNone(self.system.transfer(5, "a", "a", 10))
        self.assertIsNone(self.system.transfer(6, "a", "a", -1))

    @timeout(0.4)
    def test_level1_case_07_transfer_exact_balance(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 70)
        self.assertEqual(self.system.transfer(4, "a", "b", 70), 0)
        self.assertEqual(self.system.deposit(5, "b", 0), 70)

    @timeout(0.4)
    def test_level1_case_08_multiple_transfers(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.create_account(3, "c")
        self.system.deposit(4, "a", 300)
        self.assertEqual(self.system.transfer(5, "a", "b", 100), 200)
        self.assertEqual(self.system.transfer(6, "a", "c", 50), 150)
        self.assertEqual(self.system.deposit(7, "b", 0), 100)
        self.assertEqual(self.system.deposit(8, "c", 0), 50)

    @timeout(0.4)
    def test_level1_case_09_pay_exact_balance(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 60)
        self.assertEqual(self.system.pay(3, "acc", 60), 0)
        self.assertEqual(self.system.deposit(4, "acc", 0), 0)

    @timeout(0.4)
    def test_level1_case_10_deposit_missing_account(self):
        self.assertIsNone(self.system.deposit(1, "ghost", 10))
