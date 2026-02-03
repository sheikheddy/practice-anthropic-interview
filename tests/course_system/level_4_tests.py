import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from course_system_impl import CourseSystemImpl


class CourseSystemLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.system = CourseSystemImpl()

    @timeout(0.4)
    def test_level4_case_01_no_courses(self):
        self.assertEqual(self.system.find_nominee(), "")

    @timeout(0.4)
    def test_level4_case_02_no_eligible_students(self):
        self.system.create_course_ext("CSE101", "Intro", 3, "Standard")
        self.system.create_course_ext("CSE102", "Algo", 3, "Standard")
        self.system.register_for_course("alice", "CSE101")
        self.system.register_for_course("bob", "CSE102")
        self.assertEqual(self.system.find_nominee(), "CSE()")

    @timeout(0.4)
    def test_level4_case_03_two_departments_nominees(self):
        self.system.create_course_ext("CSE220", "Data Structures", 3, "Standard")
        self.system.create_course_ext("CSE330", "Architecture", 3, "Standard")
        self.system.create_course_ext("BIO101", "Biology", 3, "Standard")
        self.system.create_course_ext("BIO201", "Genetics", 3, "Standard")
        self.system.register_for_course("alice", "CSE220")
        self.system.register_for_course("alice", "CSE330")
        self.system.register_for_course("bob", "BIO101")
        self.system.register_for_course("bob", "BIO201")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("alice", "CSE220", comp, score)
            self.system.set_component_grade("alice", "CSE330", comp, score)
            self.system.set_component_grade("bob", "BIO101", comp, score)
            self.system.set_component_grade("bob", "BIO201", comp, score)
        self.assertEqual(self.system.find_nominee(), "BIO(bob), CSE(alice)")

    @timeout(0.4)
    def test_level4_case_04_highest_gpa_selected(self):
        self.system.create_course_ext("MAT101", "Calc", 3, "Standard")
        self.system.create_course_ext("MAT102", "Linear", 3, "Standard")
        for student in ["s1", "s2"]:
            self.system.register_for_course(student, "MAT101")
            self.system.register_for_course(student, "MAT102")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("s1", "MAT101", comp, score)
            self.system.set_component_grade("s1", "MAT102", comp, score)
        for comp, score in [("hw", 20), ("mid", 20), ("final", 20)]:
            self.system.set_component_grade("s2", "MAT101", comp, score)
            self.system.set_component_grade("s2", "MAT102", comp, score)
        self.assertEqual(self.system.find_nominee(), "MAT(s1)")

    @timeout(0.4)
    def test_level4_case_05_tie_break_lexicographic(self):
        self.system.create_course_ext("PHY101", "Physics", 3, "Standard")
        self.system.create_course_ext("PHY102", "Physics2", 3, "Standard")
        for student in ["amy", "bob"]:
            self.system.register_for_course(student, "PHY101")
            self.system.register_for_course(student, "PHY102")
            for comp, score in [("hw", 20), ("mid", 20), ("final", 20)]:
                self.system.set_component_grade(student, "PHY101", comp, score)
                self.system.set_component_grade(student, "PHY102", comp, score)
        self.assertEqual(self.system.find_nominee(), "PHY(amy)")

    @timeout(0.4)
    def test_level4_case_06_incomplete_grades_disqualify(self):
        self.system.create_course_ext("HIS101", "History", 3, "Standard")
        self.system.create_course_ext("HIS102", "History2", 3, "Standard")
        self.system.register_for_course("s1", "HIS101")
        self.system.register_for_course("s1", "HIS102")
        self.system.set_component_grade("s1", "HIS101", "hw", 10)
        self.system.set_component_grade("s1", "HIS102", "hw", 10)
        self.assertEqual(self.system.find_nominee(), "HIS()")

    @timeout(0.4)
    def test_level4_case_07_only_students_in_two_courses(self):
        self.system.create_course_ext("ENG101", "English", 3, "Standard")
        self.system.create_course_ext("ENG102", "English2", 3, "Standard")
        self.system.register_for_course("alice", "ENG101")
        self.system.register_for_course("alice", "ENG102")
        self.system.register_for_course("bob", "ENG101")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("alice", "ENG101", comp, score)
            self.system.set_component_grade("alice", "ENG102", comp, score)
            self.system.set_component_grade("bob", "ENG101", comp, score)
        self.assertEqual(self.system.find_nominee(), "ENG(alice)")

    @timeout(0.4)
    def test_level4_case_08_departments_sorted(self):
        self.system.create_course_ext("ART101", "Art", 3, "Standard")
        self.system.create_course_ext("ART102", "Art2", 3, "Standard")
        self.system.create_course_ext("BIO101", "Bio", 3, "Standard")
        self.system.create_course_ext("BIO102", "Bio2", 3, "Standard")
        self.system.create_course_ext("CHE101", "Chem", 3, "Standard")
        self.system.create_course_ext("CHE102", "Chem2", 3, "Standard")
        for student in ["a1", "a2"]:
            self.system.register_for_course(student, "ART101")
            self.system.register_for_course(student, "ART102")
        for student in ["b1", "b2"]:
            self.system.register_for_course(student, "BIO101")
            self.system.register_for_course(student, "BIO102")
        self.system.register_for_course("c1", "CHE101")
        self.system.register_for_course("c2", "CHE102")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("a1", "ART101", comp, score)
            self.system.set_component_grade("a1", "ART102", comp, score)
            self.system.set_component_grade("a2", "ART101", comp, score)
            self.system.set_component_grade("a2", "ART102", comp, score)
            self.system.set_component_grade("b1", "BIO101", comp, score)
            self.system.set_component_grade("b1", "BIO102", comp, score)
            self.system.set_component_grade("b2", "BIO101", comp, score)
            self.system.set_component_grade("b2", "BIO102", comp, score)
        self.assertEqual(self.system.find_nominee(), "ART(a1), BIO(b1), CHE()")

    @timeout(0.4)
    def test_level4_case_09_pass_fail_included_in_gpa(self):
        self.system.create_course_ext("CSE201", "Algo", 3, "Standard")
        self.system.create_course_ext("CSE202", "Proj", 2, "Pass/Fail")
        self.system.register_for_course("s1", "CSE201")
        self.system.register_for_course("s1", "CSE202")
        for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
            self.system.set_component_grade("s1", "CSE201", comp, score)
        for comp, score in [("hw", 20), ("mid", 20), ("final", 30)]:
            self.system.set_component_grade("s1", "CSE202", comp, score)
        self.assertEqual(self.system.find_nominee(), "CSE(s1)")

    @timeout(0.4)
    def test_level4_case_10_more_than_two_courses(self):
        self.system.create_course_ext("LAW101", "Law", 3, "Standard")
        self.system.create_course_ext("LAW102", "Law2", 3, "Standard")
        self.system.create_course_ext("LAW103", "Law3", 3, "Standard")
        for course in ["LAW101", "LAW102", "LAW103"]:
            self.system.register_for_course("s1", course)
        for course in ["LAW101", "LAW102", "LAW103"]:
            for comp, score in [("hw", 30), ("mid", 30), ("final", 30)]:
                self.system.set_component_grade("s1", course, comp, score)
        self.assertEqual(self.system.find_nominee(), "LAW(s1)")
