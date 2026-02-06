import inspect
import os
import signal
import sys

import unittest

try:
    from timeout_decorator import timeout as _timeout
    if hasattr(signal, "SIGALRM"):
        timeout = _timeout
    else:
        raise ModuleNotFoundError
except ModuleNotFoundError:
    def timeout(_seconds):
        def _decorator(func):
            return func
        return _decorator

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from chat_server_level1_impl import hash
from chat_server_level2_impl import HashRingVirtual


class ChatServerLevel2Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.ring = HashRingVirtual()

    @timeout(0.4)
    def test_level2_case_01_add_server_duplicate(self):
        self.assertTrue(self.ring.add_server("s1", 3))
        self.assertFalse(self.ring.add_server("s1", 1))

    @timeout(0.4)
    def test_level2_case_02_invalid_capacity_factor_raises(self):
        with self.assertRaises(AssertionError):
            self.ring.add_server("s1", 0)

    @timeout(0.4)
    def test_level2_case_03_get_server_empty_raises(self):
        with self.assertRaises(ValueError):
            self.ring.get_server("chat")

    @timeout(0.4)
    def test_level2_case_04_virtual_node_count_matches_capacity_sum(self):
        self.ring.add_server("s1", 1)
        self.ring.add_server("s2", 3)
        self.ring.add_server("s3", 2)
        self.assertEqual(len(self.ring._ring), 6)

    @timeout(0.4)
    def test_level2_case_05_remove_server_existing_and_missing(self):
        self.ring.add_server("s1", 2)
        self.ring.add_server("s2", 2)
        self.assertTrue(self.ring.remove_server("s1"))
        self.assertFalse(self.ring.remove_server("s1"))
        self.assertFalse(self.ring.remove_server("missing"))

    @timeout(0.4)
    def test_level2_case_06_removed_server_not_returned(self):
        self.ring.add_server("s1", 4)
        self.ring.add_server("s2", 1)
        self.ring.add_server("s3", 1)
        self.ring.remove_server("s1")

        for i in range(200):
            self.assertIn(self.ring.get_server(f"chat-{i}"), {"s2", "s3"})

    @timeout(0.4)
    def test_level2_case_07_capacity_factor_biases_distribution(self):
        self.ring.add_server("small", 1)
        self.ring.add_server("big", 5)

        counts = {"small": 0, "big": 0}
        for i in range(5000):
            counts[self.ring.get_server(f"chat-{i}")] += 1

        self.assertGreater(counts["big"], counts["small"] * 2)

    @timeout(0.4)
    def test_level2_case_08_mapping_independent_of_add_order(self):
        ring_a = HashRingVirtual()
        ring_b = HashRingVirtual()

        ring_a.add_server("s1", 1)
        ring_a.add_server("s2", 2)
        ring_a.add_server("s3", 3)

        ring_b.add_server("s3", 3)
        ring_b.add_server("s1", 1)
        ring_b.add_server("s2", 2)

        for i in range(200):
            chat_id = f"chat-{i}"
            self.assertEqual(ring_a.get_server(chat_id), ring_b.get_server(chat_id))

    @timeout(0.4)
    def test_level2_case_09_mapping_is_deterministic(self):
        self.ring.add_server("s1", 2)
        self.ring.add_server("s2", 2)

        expected = self.ring.get_server("chat-stable")
        for _ in range(20):
            self.assertEqual(self.ring.get_server("chat-stable"), expected)

    @timeout(0.4)
    def test_level2_case_10_wraparound_with_virtual_ring(self):
        self.ring.add_server("s1", 2)
        self.ring.add_server("s2", 2)

        max_hash = max(entry[0] for entry in self.ring._ring)
        chosen_chat = None
        for i in range(20000):
            chat_id = f"wrap-{i}"
            if hash(chat_id) > max_hash:
                chosen_chat = chat_id
                break

        self.assertIsNotNone(chosen_chat)
        expected_server = min(self.ring._ring)[2]
        self.assertEqual(self.ring.get_server(chosen_chat), expected_server)

    @timeout(0.4)
    def test_level2_case_11_large_repetition_distribution(self):
        self.ring.add_server("s1", 1)
        self.ring.add_server("s2", 2)
        self.ring.add_server("s3", 3)

        counts = {"s1": 0, "s2": 0, "s3": 0}
        for i in range(12000):
            counts[self.ring.get_server(f"heavy-{i}")] += 1

        # Legacy-style repetition check: highest capacity should dominate.
        self.assertGreater(counts["s3"], counts["s2"])
        self.assertGreater(counts["s3"], counts["s1"])

    @timeout(0.4)
    def test_level2_case_12_mixed_remove_and_readd(self):
        self.ring.add_server("s1", 3)
        self.ring.add_server("s2", 1)
        self.ring.add_server("s3", 2)
        before = [self.ring.get_server(f"chat-{i}") for i in range(100)]

        self.assertTrue(self.ring.remove_server("s1"))
        self.assertTrue(self.ring.add_server("s1", 3))
        after = [self.ring.get_server(f"chat-{i}") for i in range(100)]

        # The ring should remain deterministic and valid after mixed operations.
        for server_id in after:
            self.assertIn(server_id, {"s1", "s2", "s3"})
        self.assertEqual(len(before), len(after))

    @timeout(0.4)
    def test_level2_case_13_negative_capacity_factor_raises(self):
        with self.assertRaises(AssertionError):
            self.ring.add_server("s1", -1)
