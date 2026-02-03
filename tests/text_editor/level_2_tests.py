import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from text_editor_impl import TextEditorImpl


class TextEditorLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.editor = TextEditorImpl()

    @timeout(0.4)
    def test_level2_case_01_select_cut_paste(self):
        self.editor.append("Hello World")
        self.editor.select(0, 5)
        self.assertEqual(self.editor.cut(), " World")
        self.editor.move(0)
        self.assertEqual(self.editor.paste(), "Hello World")

    @timeout(0.4)
    def test_level2_case_02_cut_no_selection(self):
        self.editor.append("abc")
        self.assertEqual(self.editor.cut(), "abc")

    @timeout(0.4)
    def test_level2_case_03_paste_empty_clipboard(self):
        self.assertEqual(self.editor.paste(), "")

    @timeout(0.4)
    def test_level2_case_04_select_append_replaces(self):
        self.editor.append("HelloWorld")
        self.editor.select(5, 10)
        self.assertEqual(self.editor.append(" "), "Hello ")

    @timeout(0.4)
    def test_level2_case_05_select_delete(self):
        self.editor.append("abcdef")
        self.editor.select(2, 4)
        self.assertEqual(self.editor.delete(), "abef")

    @timeout(0.4)
    def test_level2_case_06_cut_then_paste_elsewhere(self):
        self.editor.append("abcdef")
        self.editor.select(2, 4)
        self.assertEqual(self.editor.cut(), "abef")
        self.editor.move(0)
        self.assertEqual(self.editor.paste(), "cdabef")

    @timeout(0.4)
    def test_level2_case_07_cut_all_then_paste(self):
        self.editor.append("abc")
        self.editor.select(0, 3)
        self.assertEqual(self.editor.cut(), "")
        self.assertEqual(self.editor.paste(), "abc")

    @timeout(0.4)
    def test_level2_case_08_paste_multiple_times(self):
        self.editor.append("abc")
        self.editor.select(0, 1)
        self.assertEqual(self.editor.cut(), "bc")
        self.assertEqual(self.editor.paste(), "abc")
        self.assertEqual(self.editor.paste(), "aabc")

    @timeout(0.4)
    def test_level2_case_09_cut_and_insert(self):
        self.editor.append("12345")
        self.editor.select(1, 4)
        self.assertEqual(self.editor.cut(), "15")
        self.editor.move(1)
        self.assertEqual(self.editor.paste(), "12345")

    @timeout(0.4)
    def test_level2_case_10_select_then_move_and_paste(self):
        self.editor.append("hello")
        self.editor.select(0, 2)
        self.editor.cut()
        self.editor.move(3)
        self.assertEqual(self.editor.paste(), "llohe")
