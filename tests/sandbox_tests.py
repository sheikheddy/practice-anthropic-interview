import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest

from banking_system_impl import BankingSystemImpl
from file_storage_system_impl import FileStorageSystemImpl
from text_editor_impl import TextEditorImpl
from time_tracking_system_impl import TimeTrackingSystemImpl
from course_system_impl import CourseSystemImpl
from database_impl import DatabaseImpl
from in_memory_db_impl import InMemoryDBImpl


class BankingSystemTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = BankingSystemImpl()

    @timeout(0.4)
    def test_level1_create_deposit_transfer_pay(self):
        self.assertTrue(self.system.create_account(1, "acc1"))
        self.assertFalse(self.system.create_account(2, "acc1"))

        self.assertEqual(self.system.deposit(3, "acc1", 1000), 1000)
        self.assertIsNone(self.system.deposit(4, "missing", 100))
        self.assertIsNone(self.system.deposit(5, "acc1", -1))

        self.assertIsNone(self.system.pay(6, "acc1", 2000))
        self.assertEqual(self.system.pay(7, "acc1", 200), 800)

        self.assertTrue(self.system.create_account(8, "acc2"))
        self.assertIsNone(self.system.transfer(9, "acc1", "acc2", 2000))
        self.assertEqual(self.system.transfer(10, "acc1", "acc2", 300), 500)

    @timeout(0.4)
    def test_level2_top_spenders(self):
        self.system.create_account(1, "a1")
        self.system.create_account(2, "a2")
        self.system.deposit(3, "a1", 1000)
        self.system.deposit(4, "a2", 500)

        self.system.pay(5, "a1", 200)  # spent 200
        self.system.transfer(6, "a1", "a2", 300)  # spent 300
        self.system.pay(7, "a2", 100)  # spent 100

        self.assertEqual(self.system.top_spenders(8, 2), ["a1", "a2"])
        self.assertEqual(self.system.top_spenders(9, 1), ["a1"])

    @timeout(0.4)
    def test_level3_scheduled_payments_and_cancel(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 500)

        payment_id = self.system.schedule_payment(3, "acc", 200, 5)  # exec at 8
        self.assertIsNotNone(payment_id)
        self.assertTrue(self.system.cancel_payment(7, "acc", payment_id))

        # At t=8, canceled payment should not execute
        self.system.deposit(8, "acc", 0)
        self.assertEqual(self.system.deposit(9, "acc", 0), 500)

        # Schedule another payment and let it execute
        payment_id2 = self.system.schedule_payment(10, "acc", 100, 2)  # exec at 12
        self.assertIsNotNone(payment_id2)
        self.system.deposit(12, "acc", 0)
        self.assertEqual(self.system.deposit(13, "acc", 0), 400)

        self.assertEqual(self.system.top_spenders(14, 1), ["acc"])

    @timeout(0.4)
    def test_level4_cancel_after_due(self):
        self.system.create_account(1, "acc")
        self.system.deposit(2, "acc", 300)
        payment_id = self.system.schedule_payment(3, "acc", 100, 0)  # exec at 3

        # Cancellation at the execution timestamp should fail (payment processed first)
        self.assertFalse(self.system.cancel_payment(3, "acc", payment_id))
        self.assertEqual(self.system.deposit(4, "acc", 0), 200)


class FileStorageSystemTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.file_system = FileStorageSystemImpl()

    @timeout(0.4)
    def test_level1_basic_file_ops(self):
        self.assertTrue(self.file_system.add_file("/home/user/file.txt", 100))
        self.assertFalse(self.file_system.add_file("/home/user/file.txt", 200))

        self.assertEqual(self.file_system.get_file_size("/home/user/file.txt"), 100)
        self.assertIsNone(self.file_system.get_file_size("/home/user/missing.txt"))

        self.assertEqual(self.file_system.delete_file("/home/user/file.txt"), 100)
        self.assertIsNone(self.file_system.get_file_size("/home/user/file.txt"))
        self.assertIsNone(self.file_system.delete_file("/home/user/file.txt"))

    @timeout(0.4)
    def test_level2_prefix_ranking(self):
        self.file_system.add_file("/media/photos/cat.jpg", 2048)
        self.file_system.add_file("/media/videos/holiday.mp4", 51200)
        self.file_system.add_file("/media/photos/dog.png", 4096)
        self.file_system.add_file("/other/unrelated.txt", 100)

        result = self.file_system.get_n_files_by_prefix("/media/", 3)
        expected = "/media/videos/holiday.mp4(51200), /media/photos/dog.png(4096), /media/photos/cat.jpg(2048)"
        self.assertEqual(result, expected)

        self.file_system.add_file("/docs/report_z.pdf", 1500)
        self.file_system.add_file("/docs/report_a.pdf", 1500)
        result = self.file_system.get_n_files_by_prefix("/docs/", 2)
        expected = "/docs/report_a.pdf(1500), /docs/report_z.pdf(1500)"
        self.assertEqual(result, expected)

    @timeout(0.4)
    def test_level3_users_and_merge(self):
        self.assertTrue(self.file_system.add_user("u1", 100))
        self.assertTrue(self.file_system.add_user("u2", 50))

        self.assertEqual(self.file_system.add_file_by_user("/u1/a.txt", "u1", 40), 60)
        self.assertIsNone(self.file_system.add_file_by_user("/u1/a.txt", "u1", 10))
        self.assertIsNone(self.file_system.add_file_by_user("/u1/b.txt", "u1", 1000))

        self.assertEqual(self.file_system.add_file_by_user("/u2/x.txt", "u2", 30), 20)

        merged = self.file_system.merge_users("u1", "u2")
        self.assertEqual(merged, 80)
        self.assertIsNone(self.file_system.add_file_by_user("/u2/y.txt", "u2", 10))
        self.assertEqual(self.file_system.get_file_size("/u2/x.txt"), 30)

    @timeout(0.4)
    def test_level4_backup_restore(self):
        self.file_system.add_user("u1", 100)
        self.file_system.add_user("u2", 50)

        self.file_system.add_file_by_user("/u1/f1.txt", "u1", 40)
        self.file_system.add_file_by_user("/u1/f2.txt", "u1", 30)
        self.assertEqual(self.file_system.backup_user("u1"), 2)

        # Move f2 to u2 to create a conflict
        self.file_system.delete_file("/u1/f2.txt")
        self.file_system.add_file_by_user("/u1/f2.txt", "u2", 30)

        restored = self.file_system.restore_user("u1")
        self.assertEqual(restored, 1)
        self.assertEqual(self.file_system.get_file_size("/u1/f1.txt"), 40)
        self.assertEqual(self.file_system.get_file_size("/u1/f2.txt"), 30)

        # No backup: remove all files and return 0
        self.file_system.add_user("u3", 25)
        self.file_system.add_file_by_user("/u3/temp.txt", "u3", 10)
        self.assertEqual(self.file_system.restore_user("u3"), 0)
        self.assertIsNone(self.file_system.get_file_size("/u3/temp.txt"))


class TextEditorTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.editor = TextEditorImpl()

    @timeout(0.4)
    def test_level1_append_move_delete(self):
        self.assertEqual(self.editor.append("Hello"), "Hello")
        self.assertEqual(self.editor.append(", World"), "Hello, World")
        self.assertEqual(self.editor.move(0), "Hello, World")

        self.editor.move(2)
        self.assertEqual(self.editor.delete(), "Helo, World")

    @timeout(0.4)
    def test_level2_select_cut_paste(self):
        self.editor.append("second first")
        self.editor.select(7, 12)
        self.assertEqual(self.editor.cut(), "second ")
        self.editor.move(0)
        self.assertEqual(self.editor.paste(), "firstsecond ")

    @timeout(0.4)
    def test_level3_undo_redo(self):
        self.editor.append("A")
        self.editor.append("B")
        self.assertEqual(self.editor.undo(), "A")
        self.assertEqual(self.editor.redo(), "AB")

    @timeout(0.4)
    def test_level4_multi_document(self):
        self.assertEqual(self.editor.create("doc1"), "")
        self.editor.append("Hello")
        self.assertEqual(self.editor.create("doc2"), "")
        self.editor.append("World")
        self.assertEqual(self.editor.switch("doc1"), "Hello")
        self.assertIsNone(self.editor.switch("missing"))
        self.assertEqual(self.editor.switch("doc2"), "World")


class TimeTrackingSystemTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = TimeTrackingSystemImpl()

    @timeout(0.4)
    def test_level1_register_and_get(self):
        self.assertTrue(self.system.add_worker("w1", "Developer", 100))
        self.assertFalse(self.system.add_worker("w1", "QA", 80))

        self.assertEqual(self.system.register(10, "w1"), "registered")
        self.assertEqual(self.system.register(25, "w1"), "registered")
        self.assertEqual(self.system.get("w1"), 15)

        self.assertIsNone(self.system.get("missing"))

        self.system.register(40, "w1")
        self.assertEqual(self.system.get("w1"), 15)  # completed sessions still count

        self.system.add_worker("w2", "Analyst", 120)
        self.system.register(100, "w2")
        self.assertIsNone(self.system.get("w2"))  # incomplete session only

    @timeout(0.4)
    def test_level2_top_n_workers(self):
        self.system.add_worker("john", "Developer", 150)
        self.system.add_worker("jane", "Developer", 160)

        self.system.register(10, "john")
        self.system.register(60, "john")  # 50
        self.system.register(10, "jane")
        self.system.register(110, "jane")  # 100

        self.assertEqual(self.system.top_n_workers(2, "Developer"), "jane(100), john(50)")
        self.assertEqual(self.system.top_n_workers(1, "QA"), "")

    @timeout(0.4)
    def test_level3_promote_and_salary(self):
        self.system.add_worker("w1", "Junior", 100)
        self.assertEqual(self.system.promote("w1", "Senior", 200, 200), "success")
        self.system.register(200, "w1")  # activation only
        self.assertEqual(self.system.top_n_workers(1, "Senior"), "w1(0)")

        self.system.register(210, "w1")
        self.system.register(230, "w1")
        self.assertEqual(self.system.calc_salary("w1", 200, 240), 4000)

    @timeout(0.4)
    def test_level4_double_paid(self):
        self.system.add_worker("w1", "Developer", 100)
        self.system.register(10, "w1")
        self.system.register(30, "w1")  # 20 * 100 = 2000

        self.system.set_double_paid(15, 25)  # overlap 10
        self.assertEqual(self.system.calc_salary("w1", 10, 30), 3000)


class CourseSystemTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = CourseSystemImpl()

    @timeout(0.4)
    def test_level1_create_and_register(self):
        self.assertTrue(self.system.create_course("CS101", "Intro to CS", 4))
        self.assertFalse(self.system.create_course("CS101", "Advanced CS", 4))
        self.assertFalse(self.system.create_course("CS102", "Intro to CS", 4))

        self.assertEqual(self.system.register_for_course("s1", "CS101"), 20)
        self.assertIsNone(self.system.register_for_course("s1", "CS999"))

    @timeout(0.4)
    def test_level2_get_pairs(self):
        self.system.create_course("CS101", "Intro to CS", 4)
        self.system.create_course("MA101", "Calculus I", 3)

        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.system.register_for_course("Charlie", "MA101")

        self.assertEqual(self.system.get_paired_students(), "[[Alice, Bob]]")

    @timeout(0.4)
    def test_level3_grades_and_gpa(self):
        self.system.create_course_ext("CSE220", "Data Structures", 3, "Standard")
        self.system.create_course_ext("CSE330", "Architecture", 3, "Pass/Fail")

        self.system.register_for_course("stu1", "CSE220")
        self.system.register_for_course("stu1", "CSE330")

        self.system.set_component_grade("stu1", "CSE220", "hw", 25)
        self.system.set_component_grade("stu1", "CSE220", "mid", 25)
        self.system.set_component_grade("stu1", "CSE220", "final", 30)

        self.system.set_component_grade("stu1", "CSE330", "hw", 25)
        self.system.set_component_grade("stu1", "CSE330", "mid", 25)
        self.system.set_component_grade("stu1", "CSE330", "final", 20)

        self.assertEqual(self.system.get_gpa("stu1"), "80, 1, 0")

    @timeout(0.4)
    def test_level4_find_nominee(self):
        self.system.create_course_ext("CSE220", "Data Structures", 3, "Standard")
        self.system.create_course_ext("CSE300", "OS", 4, "Standard")
        self.system.create_course_ext("BIO101", "Biology", 3, "Standard")
        self.system.create_course_ext("BIO201", "Genetics", 3, "Standard")

        self.system.register_for_course("alice", "CSE220")
        self.system.register_for_course("alice", "CSE300")
        self.system.register_for_course("bob", "BIO101")
        self.system.register_for_course("bob", "BIO201")

        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("alice", "CSE220", comp, score)
            self.system.set_component_grade("alice", "CSE300", comp, score)
            self.system.set_component_grade("bob", "BIO101", comp, score)
            self.system.set_component_grade("bob", "BIO201", comp, score)

        result = self.system.find_nominee()
        self.assertEqual(result, "BIO(bob), CSE(alice)")


class DatabaseTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = DatabaseImpl()

    @timeout(0.4)
    def test_level1_set_get_delete(self):
        self.db.set("user:1", "name", "Alice")
        self.assertEqual(self.db.get("user:1", "name"), "Alice")
        self.assertIsNone(self.db.get("user:1", "missing"))
        self.assertTrue(self.db.delete("user:1", "name"))
        self.assertFalse(self.db.delete("user:1", "name"))

    @timeout(0.4)
    def test_level2_scan(self):
        self.db.set("user:1", "name", "Alice")
        self.db.set("user:1", "city", "NY")
        self.db.set("user:1", "age", "30")
        self.assertEqual(self.db.scan("user:1"), "age(30), city(NY), name(Alice)")
        self.assertEqual(self.db.scan("missing"), "")

    @timeout(0.4)
    def test_level3_ttl(self):
        self.db.set_at_with_ttl("cache", "k", "v", 100, 50)
        self.assertEqual(self.db.get_at("cache", "k", 149), "v")
        self.assertIsNone(self.db.get_at("cache", "k", 150))
        self.assertFalse(self.db.delete_at("cache", "k", 150))

    @timeout(0.4)
    def test_level4_backup_restore(self):
        self.db.set_at_with_ttl("a", "x", "1", 10, 10)  # expires at 20
        self.assertEqual(self.db.backup(15), 1)

        self.db.set_at("a", "y", "2", 18)
        self.assertEqual(self.db.backup(19), 1)

        # Restore to snapshot at t=15, then shift to t=25
        self.db.restore(25, 15)
        self.assertEqual(self.db.get_at("a", "x", 25), "1")
        self.assertIsNone(self.db.get_at("a", "x", 35))  # remaining ttl should be 5


class InMemoryDBTests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.db = InMemoryDBImpl()

    @timeout(0.4)
    def test_level1_set_get_delete(self):
        self.assertEqual(self.db.set_or_inc("k1", "f1", 5), 5)
        self.assertEqual(self.db.set_or_inc("k1", "f1", 3), 8)
        self.assertEqual(self.db.get("k1", "f1"), 8)
        self.assertTrue(self.db.delete("k1", "f1"))
        self.assertFalse(self.db.delete("k1", "f1"))

    @timeout(0.4)
    def test_level2_top_n_keys(self):
        self.db.set_or_inc("a", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.db.set_or_inc("b", "f", 1)
        self.assertEqual(self.db.top_n_keys(2), "b(2), a(1)")

    @timeout(0.4)
    def test_level3_locking(self):
        self.db.set_or_inc("k", "f", 1)
        self.assertEqual(self.db.lock("u1", "k"), "acquired")
        self.assertEqual(self.db.lock("u2", "k"), "wait")
        self.assertEqual(self.db.set_or_inc("k", "f", 5), 1)  # locked by u1
        self.assertEqual(self.db.set_or_inc_by_caller("k", "f", 5, "u1"), 6)
        self.assertFalse(self.db.delete_by_caller("k", "f", "u2"))
        self.assertEqual(self.db.unlock("k"), "released")
        self.assertFalse(self.db.delete("k", "f"))  # lock transferred to u2
        self.assertEqual(self.db.unlock("k"), "released")
        self.assertTrue(self.db.delete("k", "f"))
