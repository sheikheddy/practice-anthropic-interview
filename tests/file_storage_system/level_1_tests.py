import inspect
import os
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from timeout_decorator import timeout
import unittest
from file_storage_system_impl import FileStorageSystemImpl


class FileStorageSystemLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.storage = FileStorageSystemImpl()

    @timeout(0.4)
    def test_level1_case_01_add_and_get(self):
        self.assertTrue(self.storage.add_file("/home/a.txt", 10))
        self.assertEqual(self.storage.get_file_size("/home/a.txt"), 10)

    @timeout(0.4)
    def test_level1_case_02_add_duplicate_fails(self):
        self.assertTrue(self.storage.add_file("/home/a.txt", 10))
        self.assertFalse(self.storage.add_file("/home/a.txt", 20))

    @timeout(0.4)
    def test_level1_case_03_get_missing(self):
        self.assertIsNone(self.storage.get_file_size("/missing.txt"))

    @timeout(0.4)
    def test_level1_case_04_delete_success(self):
        self.storage.add_file("/home/a.txt", 10)
        self.assertEqual(self.storage.delete_file("/home/a.txt"), 10)
        self.assertIsNone(self.storage.get_file_size("/home/a.txt"))

    @timeout(0.4)
    def test_level1_case_05_delete_missing(self):
        self.assertIsNone(self.storage.delete_file("/missing.txt"))

    @timeout(0.4)
    def test_level1_case_06_add_multiple_delete_one(self):
        self.storage.add_file("/home/a.txt", 10)
        self.storage.add_file("/home/b.txt", 20)
        self.assertEqual(self.storage.delete_file("/home/a.txt"), 10)
        self.assertEqual(self.storage.get_file_size("/home/b.txt"), 20)

    @timeout(0.4)
    def test_level1_case_07_readd_after_delete(self):
        self.storage.add_file("/home/a.txt", 10)
        self.assertEqual(self.storage.delete_file("/home/a.txt"), 10)
        self.assertTrue(self.storage.add_file("/home/a.txt", 15))
        self.assertEqual(self.storage.get_file_size("/home/a.txt"), 15)

    @timeout(0.4)
    def test_level1_case_08_nested_paths(self):
        self.storage.add_file("/var/log/sys.log", 5)
        self.storage.add_file("/var/log/app.log", 7)
        self.assertEqual(self.storage.get_file_size("/var/log/sys.log"), 5)
        self.assertEqual(self.storage.get_file_size("/var/log/app.log"), 7)

    @timeout(0.4)
    def test_level1_case_09_delete_returns_size(self):
        self.storage.add_file("/tmp/file.bin", 99)
        self.assertEqual(self.storage.delete_file("/tmp/file.bin"), 99)

    @timeout(0.4)
    def test_level1_case_10_add_many_files(self):
        for i in range(5):
            self.assertTrue(self.storage.add_file(f"/data/f{i}.txt", i + 1))
        self.assertEqual(self.storage.get_file_size("/data/f4.txt"), 5)
