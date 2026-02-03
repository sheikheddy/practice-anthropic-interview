import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from course_system_impl import CourseSystemImpl


class CourseSystemLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = CourseSystemImpl()

    @timeout(0.4)
    def test_level1_case_01_create_course_duplicate_id(self):
        self.assertTrue(self.system.create_course("CS101", "Intro", 4))
        self.assertFalse(self.system.create_course("CS101", "Intro 2", 4))

    @timeout(0.4)
    def test_level1_case_02_create_course_duplicate_name(self):
        self.assertTrue(self.system.create_course("CS101", "Intro", 4))
        self.assertFalse(self.system.create_course("CS102", "Intro", 4))

    @timeout(0.4)
    def test_level1_case_03_register_basic(self):
        self.system.create_course("CS101", "Intro", 4)
        self.assertEqual(self.system.register_for_course("s1", "CS101"), 20)

    @timeout(0.4)
    def test_level1_case_04_register_missing_course(self):
        self.assertIsNone(self.system.register_for_course("s1", "MISSING"))

    @timeout(0.4)
    def test_level1_case_05_register_duplicate(self):
        self.system.create_course("CS101", "Intro", 4)
        self.assertEqual(self.system.register_for_course("s1", "CS101"), 20)
        self.assertIsNone(self.system.register_for_course("s1", "CS101"))

    @timeout(0.4)
    def test_level1_case_06_register_insufficient_credits(self):
        self.system.create_course("CS101", "Intro", 20)
        self.system.create_course("CS102", "Algo", 10)
        self.assertEqual(self.system.register_for_course("s1", "CS101"), 4)
        self.assertIsNone(self.system.register_for_course("s1", "CS102"))

    @timeout(0.4)
    def test_level1_case_07_register_exact_zero_remaining(self):
        self.system.create_course("CS101", "Intro", 12)
        self.system.create_course("CS102", "Algo", 12)
        self.assertEqual(self.system.register_for_course("s1", "CS101"), 12)
        self.assertEqual(self.system.register_for_course("s1", "CS102"), 0)

    @timeout(0.4)
    def test_level1_case_08_multiple_students_independent(self):
        self.system.create_course("CS101", "Intro", 4)
        self.assertEqual(self.system.register_for_course("s1", "CS101"), 20)
        self.assertEqual(self.system.register_for_course("s2", "CS101"), 20)

    @timeout(0.4)
    def test_level1_case_09_register_multiple_courses(self):
        self.system.create_course("CS101", "Intro", 3)
        self.system.create_course("CS102", "Algo", 5)
        self.system.create_course("CS103", "DB", 4)
        self.assertEqual(self.system.register_for_course("s1", "CS101"), 21)
        self.assertEqual(self.system.register_for_course("s1", "CS102"), 16)
        self.assertEqual(self.system.register_for_course("s1", "CS103"), 12)

    @timeout(0.4)
    def test_level1_case_10_create_course_many(self):
        self.assertTrue(self.system.create_course("MA101", "Calculus", 3))
        self.assertTrue(self.system.create_course("PH101", "Physics", 4))
        self.assertTrue(self.system.create_course("CH101", "Chemistry", 4))
