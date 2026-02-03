import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from file_storage_system_impl import FileStorageSystemImpl


class FileStorageSystemLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.storage = FileStorageSystemImpl()

    @timeout(0.4)
    def test_level2_case_01_basic_prefix_ranking(self):
        self.storage.add_file("/media/photos/cat.jpg", 2048)
        self.storage.add_file("/media/videos/holiday.mp4", 51200)
        self.storage.add_file("/media/photos/dog.png", 4096)
        self.storage.add_file("/other/unrelated.txt", 100)

        result = self.storage.get_n_files_by_prefix("/media/", 3)
        expected = "/media/videos/holiday.mp4(51200), /media/photos/dog.png(4096), /media/photos/cat.jpg(2048)"
        self.assertEqual(result, expected)

    @timeout(0.4)
    def test_level2_case_02_tie_break_by_path(self):
        self.storage.add_file("/docs/report_z.pdf", 1500)
        self.storage.add_file("/docs/report_a.pdf", 1500)
        result = self.storage.get_n_files_by_prefix("/docs/", 2)
        expected = "/docs/report_a.pdf(1500), /docs/report_z.pdf(1500)"
        self.assertEqual(result, expected)

    @timeout(0.4)
    def test_level2_case_03_count_less_than_matches(self):
        self.storage.add_file("/a/one.txt", 10)
        self.storage.add_file("/a/two.txt", 20)
        self.storage.add_file("/a/three.txt", 30)
        result = self.storage.get_n_files_by_prefix("/a/", 1)
        self.assertEqual(result, "/a/three.txt(30)")

    @timeout(0.4)
    def test_level2_case_04_count_more_than_matches(self):
        self.storage.add_file("/b/one.txt", 10)
        self.storage.add_file("/b/two.txt", 20)
        result = self.storage.get_n_files_by_prefix("/b/", 5)
        self.assertEqual(result, "/b/two.txt(20), /b/one.txt(10)")

    @timeout(0.4)
    def test_level2_case_05_prefix_no_matches(self):
        self.storage.add_file("/c/one.txt", 10)
        self.assertEqual(self.storage.get_n_files_by_prefix("/missing/", 3), "")

    @timeout(0.4)
    def test_level2_case_06_prefix_exact_path(self):
        self.storage.add_file("/data/file.txt", 99)
        result = self.storage.get_n_files_by_prefix("/data/file.txt", 3)
        self.assertEqual(result, "/data/file.txt(99)")

    @timeout(0.4)
    def test_level2_case_07_nested_prefix(self):
        self.storage.add_file("/root/a.txt", 5)
        self.storage.add_file("/root/sub/b.txt", 6)
        self.storage.add_file("/root/sub/c.txt", 4)
        result = self.storage.get_n_files_by_prefix("/root/sub/", 5)
        self.assertEqual(result, "/root/sub/b.txt(6), /root/sub/c.txt(4)")

    @timeout(0.4)
    def test_level2_case_08_delete_updates_ranking(self):
        self.storage.add_file("/d/a.txt", 10)
        self.storage.add_file("/d/b.txt", 30)
        self.storage.add_file("/d/c.txt", 20)
        self.assertEqual(self.storage.get_n_files_by_prefix("/d/", 2), "/d/b.txt(30), /d/c.txt(20)")
        self.assertEqual(self.storage.delete_file("/d/b.txt"), 30)
        self.assertEqual(self.storage.get_n_files_by_prefix("/d/", 2), "/d/c.txt(20), /d/a.txt(10)")

    @timeout(0.4)
    def test_level2_case_09_same_size_multiple_paths(self):
        self.storage.add_file("/e/c.txt", 7)
        self.storage.add_file("/e/a.txt", 7)
        self.storage.add_file("/e/b.txt", 7)
        result = self.storage.get_n_files_by_prefix("/e/", 3)
        self.assertEqual(result, "/e/a.txt(7), /e/b.txt(7), /e/c.txt(7)")

    @timeout(0.4)
    def test_level2_case_10_size_priority_over_path(self):
        self.storage.add_file("/f/z.txt", 100)
        self.storage.add_file("/f/a.txt", 200)
        self.storage.add_file("/f/m.txt", 150)
        result = self.storage.get_n_files_by_prefix("/f/", 3)
        self.assertEqual(result, "/f/a.txt(200), /f/m.txt(150), /f/z.txt(100)")
