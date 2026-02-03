import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from text_editor_impl import TextEditorImpl


class TextEditorLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.editor = TextEditorImpl()

    @timeout(0.4)
    def test_level3_case_01_undo_redo_append(self):
        self.editor.append("A")
        self.editor.append("B")
        self.assertEqual(self.editor.undo(), "A")
        self.assertEqual(self.editor.redo(), "AB")

    @timeout(0.4)
    def test_level3_case_02_undo_after_delete(self):
        self.editor.append("ABC")
        self.editor.move(1)
        self.editor.delete()
        self.assertEqual(self.editor.undo(), "ABC")

    @timeout(0.4)
    def test_level3_case_03_undo_at_start_noop(self):
        self.assertEqual(self.editor.undo(), "")
        self.assertEqual(self.editor.redo(), "")

    @timeout(0.4)
    def test_level3_case_04_redo_cleared_after_new_action(self):
        self.editor.append("a")
        self.editor.append("b")
        self.assertEqual(self.editor.undo(), "a")
        self.editor.append("c")
        self.assertEqual(self.editor.redo(), "ac")

    @timeout(0.4)
    def test_level3_case_05_multiple_undos(self):
        self.editor.append("a")
        self.editor.append("b")
        self.editor.append("c")
        self.assertEqual(self.editor.undo(), "ab")
        self.assertEqual(self.editor.undo(), "a")
        self.assertEqual(self.editor.undo(), "")
        self.assertEqual(self.editor.undo(), "")

    @timeout(0.4)
    def test_level3_case_06_undo_after_move(self):
        self.editor.append("abc")
        self.editor.move(1)
        self.assertEqual(self.editor.undo(), "abc")

    @timeout(0.4)
    def test_level3_case_07_undo_redo_with_selection_replace(self):
        self.editor.append("HelloWorld")
        self.editor.select(5, 10)
        self.assertEqual(self.editor.append("!"), "Hello!")
        self.assertEqual(self.editor.undo(), "HelloWorld")
        self.assertEqual(self.editor.redo(), "Hello!")

    @timeout(0.4)
    def test_level3_case_08_redo_without_undo_noop(self):
        self.editor.append("X")
        self.assertEqual(self.editor.redo(), "X")

    @timeout(0.4)
    def test_level3_case_09_undo_after_cut(self):
        self.editor.append("abc")
        self.editor.select(0, 1)
        self.editor.cut()
        self.assertEqual(self.editor.undo(), "abc")

    @timeout(0.4)
    def test_level3_case_10_undo_redo_with_paste(self):
        self.editor.append("abc")
        self.editor.select(0, 1)
        self.editor.cut()
        self.editor.paste()
        self.assertEqual(self.editor.undo(), "bc")
        self.assertEqual(self.editor.redo(), "abc")
