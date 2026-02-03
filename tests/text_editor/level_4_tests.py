import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from text_editor_impl import TextEditorImpl


class TextEditorLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.editor = TextEditorImpl()

    @timeout(0.4)
    def test_level4_case_01_create_and_switch(self):
        self.assertEqual(self.editor.create("doc1"), "")
        self.editor.append("Hello")
        self.assertEqual(self.editor.create("doc2"), "")
        self.editor.append("World")
        self.assertEqual(self.editor.switch("doc1"), "Hello")
        self.assertEqual(self.editor.switch("doc2"), "World")

    @timeout(0.4)
    def test_level4_case_02_switch_missing(self):
        self.assertEqual(self.editor.create("doc1"), "")
        self.assertIsNone(self.editor.switch("missing"))

    @timeout(0.4)
    def test_level4_case_03_documents_independent(self):
        self.editor.create("doc1")
        self.editor.append("Hello")
        self.editor.create("doc2")
        self.editor.append("World")
        self.editor.switch("doc1")
        self.editor.append("!")
        self.assertEqual(self.editor.switch("doc2"), "World")
        self.assertEqual(self.editor.switch("doc1"), "Hello!")

    @timeout(0.4)
    def test_level4_case_04_undo_per_document(self):
        self.editor.create("doc1")
        self.editor.append("A")
        self.editor.create("doc2")
        self.editor.append("B")
        self.assertEqual(self.editor.undo(), "")
        self.assertEqual(self.editor.switch("doc1"), "A")

    @timeout(0.4)
    def test_level4_case_05_redo_per_document(self):
        self.editor.create("doc1")
        self.editor.append("A")
        self.editor.undo()
        self.assertEqual(self.editor.redo(), "A")
        self.editor.create("doc2")
        self.editor.append("B")
        self.editor.undo()
        self.assertEqual(self.editor.redo(), "B")

    @timeout(0.4)
    def test_level4_case_06_create_existing_doc(self):
        self.editor.create("doc1")
        self.editor.append("X")
        self.assertEqual(self.editor.create("doc1"), "X")

    @timeout(0.4)
    def test_level4_case_07_empty_doc_persists(self):
        self.editor.create("doc1")
        self.editor.create("doc2")
        self.assertEqual(self.editor.switch("doc1"), "")

    @timeout(0.4)
    def test_level4_case_08_history_isolated(self):
        self.editor.create("doc1")
        self.editor.append("a")
        self.editor.create("doc2")
        self.editor.append("b")
        self.editor.switch("doc1")
        self.editor.undo()
        self.assertEqual(self.editor.switch("doc2"), "b")

    @timeout(0.4)
    def test_level4_case_09_switch_preserves_state(self):
        self.editor.create("doc1")
        self.editor.append("123")
        self.editor.create("doc2")
        self.editor.append("abc")
        self.assertEqual(self.editor.switch("doc1"), "123")
        self.assertEqual(self.editor.switch("doc2"), "abc")

    @timeout(0.4)
    def test_level4_case_10_undo_after_switch(self):
        self.editor.create("doc1")
        self.editor.append("hi")
        self.editor.create("doc2")
        self.editor.append("bye")
        self.editor.switch("doc1")
        self.assertEqual(self.editor.undo(), "")
        self.assertEqual(self.editor.switch("doc2"), "bye")
