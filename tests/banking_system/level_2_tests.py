import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from banking_system_impl import BankingSystemImpl


class BankingSystemLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = BankingSystemImpl()

    @timeout(0.4)
    def test_level2_case_01_no_spenders(self):
        self.system.create_account(1, "a")
        self.system.deposit(2, "a", 100)
        self.assertEqual(self.system.top_spenders(3, 5), [])

    @timeout(0.4)
    def test_level2_case_02_ranking_by_spent(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 200)
        self.system.deposit(4, "b", 200)
        self.system.pay(5, "a", 50)
        self.system.transfer(6, "b", "a", 100)
        self.assertEqual(self.system.top_spenders(7, 2), ["b", "a"])

    @timeout(0.4)
    def test_level2_case_03_ranking_tie_break(self):
        self.system.create_account(1, "z")
        self.system.create_account(2, "a")
        self.system.deposit(3, "z", 100)
        self.system.deposit(4, "a", 100)
        self.system.pay(5, "z", 50)
        self.system.pay(6, "a", 50)
        self.assertEqual(self.system.top_spenders(7, 2), ["a", "z"])

    @timeout(0.4)
    def test_level2_case_04_num_accounts_more_than_spenders(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 50)
        self.system.pay(4, "a", 10)
        self.assertEqual(self.system.top_spenders(5, 5), ["a"])

    @timeout(0.4)
    def test_level2_case_05_spent_updates_after_transfer(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 300)
        self.system.transfer(4, "a", "b", 120)
        self.system.transfer(5, "a", "b", 30)
        self.assertEqual(self.system.top_spenders(6, 1), ["a"])

    @timeout(0.4)
    def test_level2_case_06_spent_updates_after_pay(self):
        self.system.create_account(1, "a")
        self.system.deposit(2, "a", 100)
        self.system.pay(3, "a", 20)
        self.system.pay(4, "a", 30)
        self.assertEqual(self.system.top_spenders(5, 1), ["a"])

    @timeout(0.4)
    def test_level2_case_07_ignore_zero_spent(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 100)
        self.system.deposit(4, "b", 100)
        self.system.pay(5, "a", 10)
        self.assertEqual(self.system.top_spenders(6, 5), ["a"])

    @timeout(0.4)
    def test_level2_case_08_multiple_spenders_order(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.create_account(3, "c")
        self.system.deposit(4, "a", 100)
        self.system.deposit(5, "b", 100)
        self.system.deposit(6, "c", 100)
        self.system.pay(7, "a", 10)
        self.system.pay(8, "b", 20)
        self.system.pay(9, "c", 15)
        self.assertEqual(self.system.top_spenders(10, 3), ["b", "c", "a"])

    @timeout(0.4)
    def test_level2_case_09_spenders_after_failed_pay(self):
        self.system.create_account(1, "a")
        self.system.deposit(2, "a", 10)
        self.assertIsNone(self.system.pay(3, "a", 20))
        self.assertEqual(self.system.top_spenders(4, 1), [])

    @timeout(0.4)
    def test_level2_case_10_spenders_after_failed_transfer(self):
        self.system.create_account(1, "a")
        self.system.create_account(2, "b")
        self.system.deposit(3, "a", 10)
        self.assertIsNone(self.system.transfer(4, "a", "b", 20))
        self.assertEqual(self.system.top_spenders(5, 2), [])
