import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from course_system_impl import CourseSystemImpl


class CourseSystemLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = CourseSystemImpl()

    @timeout(0.4)
    def test_level2_case_01_no_pairs(self):
        self.system.create_course("CS101", "Intro", 4)
        self.system.register_for_course("Alice", "CS101")
        self.assertEqual(self.system.get_paired_students(), "")

    @timeout(0.4)
    def test_level2_case_02_single_pair(self):
        self.system.create_course("CS101", "Intro", 4)
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.assertEqual(self.system.get_paired_students(), "[[Alice, Bob]]")

    @timeout(0.4)
    def test_level2_case_03_three_students(self):
        self.system.create_course("CS101", "Intro", 4)
        for name in ["Charlie", "Alice", "Bob"]:
            self.system.register_for_course(name, "CS101")
        expected = "[[Alice, Bob], [Alice, Charlie], [Bob, Charlie]]"
        self.assertEqual(self.system.get_paired_students(), expected)

    @timeout(0.4)
    def test_level2_case_04_two_courses_pairs(self):
        self.system.create_course("CS101", "Intro", 4)
        self.system.create_course("CS102", "Algo", 4)
        self.system.register_for_course("Ann", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.system.register_for_course("Dan", "CS102")
        self.system.register_for_course("Eve", "CS102")
        expected = "[[Ann, Bob]], [[Dan, Eve]]"
        self.assertEqual(self.system.get_paired_students(), expected)

    @timeout(0.4)
    def test_level2_case_05_ignore_pass_fail_courses(self):
        self.system.create_course("CS101", "Intro", 4)
        self.system.create_course_ext("PF101", "PassFail", 3, "Pass/Fail")
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.system.register_for_course("X", "PF101")
        self.system.register_for_course("Y", "PF101")
        self.assertEqual(self.system.get_paired_students(), "[[Alice, Bob]]")

    @timeout(0.4)
    def test_level2_case_06_four_students(self):
        self.system.create_course("CS101", "Intro", 4)
        for name in ["D", "B", "A", "C"]:
            self.system.register_for_course(name, "CS101")
        expected = "[[A, B], [A, C], [A, D], [B, C], [B, D], [C, D]]"
        self.assertEqual(self.system.get_paired_students(), expected)

    @timeout(0.4)
    def test_level2_case_07_same_student_multiple_courses(self):
        self.system.create_course("CS101", "Intro", 4)
        self.system.create_course("CS102", "Algo", 4)
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.system.register_for_course("Alice", "CS102")
        self.system.register_for_course("Carol", "CS102")
        expected = "[[Alice, Bob]], [[Alice, Carol]]"
        self.assertEqual(self.system.get_paired_students(), expected)

    @timeout(0.4)
    def test_level2_case_08_registration_order_irrelevant(self):
        self.system.create_course("CS101", "Intro", 4)
        for name in ["Zoe", "Amy", "Mike"]:
            self.system.register_for_course(name, "CS101")
        expected = "[[Amy, Mike], [Amy, Zoe], [Mike, Zoe]]"
        self.assertEqual(self.system.get_paired_students(), expected)

    @timeout(0.4)
    def test_level2_case_09_only_standard_courses(self):
        self.system.create_course_ext("PF101", "PassFail", 3, "Pass/Fail")
        self.system.register_for_course("A", "PF101")
        self.system.register_for_course("B", "PF101")
        self.assertEqual(self.system.get_paired_students(), "")

    @timeout(0.4)
    def test_level2_case_10_ignore_courses_without_pairs(self):
        self.system.create_course("CS101", "Intro", 4)
        self.system.create_course("CS102", "Algo", 4)
        self.system.register_for_course("Alice", "CS101")
        self.system.register_for_course("Bob", "CS101")
        self.system.register_for_course("Solo", "CS102")
        self.assertEqual(self.system.get_paired_students(), "[[Alice, Bob]]")
