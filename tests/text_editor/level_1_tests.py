import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from text_editor_impl import TextEditorImpl


class TextEditorLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.editor = TextEditorImpl()

    @timeout(0.4)
    def test_level1_case_01_append_basic(self):
        self.assertEqual(self.editor.append("Hello"), "Hello")
        self.assertEqual(self.editor.append("!"), "Hello!")

    @timeout(0.4)
    def test_level1_case_02_move_and_insert(self):
        self.assertEqual(self.editor.append("World"), "World")
        self.assertEqual(self.editor.move(0), "World")
        self.assertEqual(self.editor.append("Hello "), "Hello World")

    @timeout(0.4)
    def test_level1_case_03_move_clamps_and_delete_end(self):
        self.assertEqual(self.editor.append("abc"), "abc")
        self.assertEqual(self.editor.move(10), "abc")
        self.assertEqual(self.editor.delete(), "abc")

    @timeout(0.4)
    def test_level1_case_04_delete_middle(self):
        self.assertEqual(self.editor.append("abcd"), "abcd")
        self.assertEqual(self.editor.move(1), "abcd")
        self.assertEqual(self.editor.delete(), "acd")

    @timeout(0.4)
    def test_level1_case_05_delete_at_end(self):
        self.assertEqual(self.editor.append("abc"), "abc")
        self.assertEqual(self.editor.move(3), "abc")
        self.assertEqual(self.editor.delete(), "abc")

    @timeout(0.4)
    def test_level1_case_06_multiple_deletes(self):
        self.assertEqual(self.editor.append("abc"), "abc")
        self.assertEqual(self.editor.move(0), "abc")
        self.assertEqual(self.editor.delete(), "bc")
        self.assertEqual(self.editor.delete(), "c")

    @timeout(0.4)
    def test_level1_case_07_move_negative(self):
        self.assertEqual(self.editor.append("abc"), "abc")
        self.assertEqual(self.editor.move(-5), "abc")
        self.assertEqual(self.editor.append("Z"), "Zabc")

    @timeout(0.4)
    def test_level1_case_08_append_empty(self):
        self.assertEqual(self.editor.append(""), "")
        self.assertEqual(self.editor.append("x"), "x")

    @timeout(0.4)
    def test_level1_case_09_insert_in_middle(self):
        self.assertEqual(self.editor.append("abc"), "abc")
        self.assertEqual(self.editor.move(2), "abc")
        self.assertEqual(self.editor.append("X"), "abXc")

    @timeout(0.4)
    def test_level1_case_10_delete_on_empty(self):
        self.assertEqual(self.editor.delete(), "")
