import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from course_system_impl import CourseSystemImpl


class CourseSystemLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = CourseSystemImpl()

    @timeout(0.4)
    def test_level3_case_01_set_grade_invalid_student(self):
        self.system.create_course_ext("CS101", "Intro", 4, "Standard")
        self.assertEqual(self.system.set_component_grade("s1", "CS101", "hw", 10), "invalid")

    @timeout(0.4)
    def test_level3_case_02_set_grade_invalid_course(self):
        self.system.create_course_ext("CS101", "Intro", 4, "Standard")
        self.system.register_for_course("s1", "CS101")
        self.assertEqual(self.system.set_component_grade("s1", "CS999", "hw", 10), "invalid")

    @timeout(0.4)
    def test_level3_case_03_set_grade_not_registered(self):
        self.system.create_course_ext("CS101", "Intro", 4, "Standard")
        self.system.create_course_ext("CS102", "Algo", 4, "Standard")
        self.system.register_for_course("s1", "CS101")
        self.assertEqual(self.system.set_component_grade("s1", "CS102", "hw", 10), "invalid")

    @timeout(0.4)
    def test_level3_case_04_set_and_update_grade(self):
        self.system.create_course_ext("CS101", "Intro", 4, "Standard")
        self.system.register_for_course("s1", "CS101")
        self.assertEqual(self.system.set_component_grade("s1", "CS101", "hw", 10), "set")
        self.assertEqual(self.system.set_component_grade("s1", "CS101", "hw", 15), "updated")

    @timeout(0.4)
    def test_level3_case_05_get_gpa_missing_student(self):
        self.assertIsNone(self.system.get_gpa("missing"))

    @timeout(0.4)
    def test_level3_case_06_get_gpa_missing_components(self):
        self.system.create_course_ext("CS101", "Intro", 4, "Standard")
        self.system.register_for_course("s1", "CS101")
        self.system.set_component_grade("s1", "CS101", "hw", 30)
        self.system.set_component_grade("s1", "CS101", "mid", 30)
        self.assertIsNone(self.system.get_gpa("s1"))

    @timeout(0.4)
    def test_level3_case_07_get_gpa_standard_and_passfail(self):
        self.system.create_course_ext("CS101", "Intro", 3, "Standard")
        self.system.create_course_ext("PF101", "PassFail", 2, "Pass/Fail")
        self.system.register_for_course("s1", "CS101")
        self.system.register_for_course("s1", "PF101")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("s1", "CS101", comp, score)
        for comp, score in [("hw", 20), ("mid", 20), ("final", 30)]:
            self.system.set_component_grade("s1", "PF101", comp, score)
        self.assertEqual(self.system.get_gpa("s1"), "90, 1, 0")

    @timeout(0.4)
    def test_level3_case_08_get_gpa_pass_fail_fail(self):
        self.system.create_course_ext("PF101", "PassFail", 2, "Pass/Fail")
        self.system.register_for_course("s1", "PF101")
        for comp, score in [("hw", 20), ("mid", 20), ("final", 20)]:
            self.system.set_component_grade("s1", "PF101", comp, score)
        self.assertEqual(self.system.get_gpa("s1"), "0, 0, 1")

    @timeout(0.4)
    def test_level3_case_09_weighted_average_multiple_standard(self):
        self.system.create_course_ext("CS101", "Intro", 3, "Standard")
        self.system.create_course_ext("CS102", "Algo", 4, "Standard")
        self.system.register_for_course("s1", "CS101")
        self.system.register_for_course("s1", "CS102")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("s1", "CS101", comp, score)
        for comp, score in [("hw", 25), ("mid", 25), ("final", 30)]:
            self.system.set_component_grade("s1", "CS102", comp, score)
        self.assertEqual(self.system.get_gpa("s1"), "84, 0, 0")

    @timeout(0.4)
    def test_level3_case_10_only_pass_fail_courses(self):
        self.system.create_course_ext("PF101", "PassFail", 2, "Pass/Fail")
        self.system.create_course_ext("PF102", "PassFail2", 2, "Pass/Fail")
        self.system.register_for_course("s1", "PF101")
        self.system.register_for_course("s1", "PF102")
        for comp, score in [("hw", 20), ("mid", 20), ("final", 30)]:
            self.system.set_component_grade("s1", "PF101", comp, score)
        for comp, score in [("hw", 10), ("mid", 10), ("final", 20)]:
            self.system.set_component_grade("s1", "PF102", comp, score)
        self.assertEqual(self.system.get_gpa("s1"), "0, 1, 1")
