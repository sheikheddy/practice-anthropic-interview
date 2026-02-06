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

from chat_server_level4_impl import ChatData, Server


class ChatServerLevel4Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.server = Server(max_vram_chats=2, max_ram_chats=2)

    @timeout(0.4)
    def test_level4_case_01_total_has_and_remove_chat(self):
        self.server.vram_chats["a"] = ChatData("a", 1)
        self.server.ram_chats["b"] = ChatData("b", 2)

        self.assertEqual(self.server.total_chats, 2)
        self.assertTrue(self.server.has_chat("a"))
        self.assertTrue(self.server.has_chat("b"))
        self.assertFalse(self.server.has_chat("c"))

        removed = self.server.remove_chat("a")
        self.assertIsNotNone(removed)
        self.assertEqual(removed.chat_id, "a")
        self.assertIsNone(self.server.remove_chat("missing"))

    @timeout(0.4)
    def test_level4_case_02_cache_miss_creates_vram_chat(self):
        response = self.server.handle_request("c1", 1, "hello")
        self.assertTrue(response.success)
        self.assertIn("c1", self.server.vram_chats)
        self.assertEqual(self.server.num_cache_misses, 1)
        self.assertEqual(self.server.num_cache_hits, 0)

    @timeout(0.4)
    def test_level4_case_03_cache_hit_in_vram_updates_timestamp(self):
        self.server.handle_request("c1", 1, "hello")
        self.server.handle_request("c1", 5, "again")
        self.assertEqual(self.server.vram_chats["c1"].last_timestamp, 5)
        self.assertEqual(self.server.num_cache_hits, 1)
        self.assertEqual(self.server.num_cache_misses, 1)

    @timeout(0.4)
    def test_level4_case_04_new_chat_evicts_oldest_vram_to_ram(self):
        self.server.handle_request("c1", 1, "m1")
        self.server.handle_request("c2", 2, "m2")
        self.server.handle_request("c3", 3, "m3")

        self.assertIn("c1", self.server.ram_chats)
        self.assertIn("c2", self.server.vram_chats)
        self.assertIn("c3", self.server.vram_chats)

    @timeout(0.4)
    def test_level4_case_05_new_chat_when_both_full_drops_oldest_ram(self):
        self.server.handle_request("c1", 1, "m1")
        self.server.handle_request("c2", 2, "m2")
        self.server.handle_request("c3", 3, "m3")
        self.server.handle_request("c4", 4, "m4")
        self.server.handle_request("c5", 5, "m5")

        self.assertNotIn("c1", self.server.vram_chats)
        self.assertNotIn("c1", self.server.ram_chats)
        self.assertIn("c2", self.server.ram_chats)
        self.assertIn("c3", self.server.ram_chats)
        self.assertIn("c4", self.server.vram_chats)
        self.assertIn("c5", self.server.vram_chats)

    @timeout(0.4)
    def test_level4_case_06_ram_chat_promotes_to_vram_when_space_exists(self):
        self.server.handle_request("c1", 1, "m1")
        self.server.handle_request("c2", 2, "m2")
        self.server.handle_request("c3", 3, "m3")
        self.server.remove_chat("c2")

        self.assertIn("c1", self.server.ram_chats)
        self.server.handle_request("c1", 4, "promote")
        self.assertIn("c1", self.server.vram_chats)
        self.assertNotIn("c1", self.server.ram_chats)

    @timeout(0.4)
    def test_level4_case_07_ram_hit_with_full_vram_and_ram_eviction_rules(self):
        self.server.handle_request("c1", 1, "m1")
        self.server.handle_request("c2", 2, "m2")
        self.server.handle_request("c3", 3, "m3")
        self.server.handle_request("c4", 4, "m4")

        self.assertIn("c1", self.server.ram_chats)
        self.assertIn("c2", self.server.ram_chats)

        self.server.handle_request("c1", 5, "promote")
        self.assertIn("c1", self.server.vram_chats)
        self.assertNotIn("c1", self.server.ram_chats)
        self.assertNotIn("c2", self.server.ram_chats)
        self.assertIn("c3", self.server.ram_chats)

    @timeout(0.4)
    def test_level4_case_08_handle_request_offline_fails(self):
        self.server.shutdown()
        response = self.server.handle_request("c1", 1, "msg")
        self.assertFalse(response.success)
        self.assertEqual(self.server.num_cache_hits, 0)
        self.assertEqual(self.server.num_cache_misses, 0)

    @timeout(0.4)
    def test_level4_case_09_shutdown_clears_state_and_double_shutdown_raises(self):
        self.server.handle_request("c1", 1, "msg")
        self.server.handle_request("c2", 2, "msg")
        self.server.shutdown()

        self.assertFalse(self.server.is_online)
        self.assertEqual(self.server.total_chats, 0)
        with self.assertRaises(RuntimeError):
            self.server.shutdown()

    @timeout(0.4)
    def test_level4_case_10_hit_and_miss_counters_track_mixed_requests(self):
        self.server.handle_request("c1", 1, "msg")
        self.server.handle_request("c2", 2, "msg")
        self.server.handle_request("c3", 3, "msg")
        self.server.handle_request("c2", 4, "msg")
        self.server.handle_request("c1", 5, "msg")

        self.assertEqual(self.server.num_cache_misses, 3)
        self.assertEqual(self.server.num_cache_hits, 2)

    @timeout(0.4)
    def test_level4_case_11_stress_mixed_requests_keep_capacity_bounds(self):
        for i in range(1, 20):
            chat_id = f"c{i % 7}"
            self.server.handle_request(chat_id, i, "msg")

        self.assertLessEqual(len(self.server.vram_chats), self.server.max_vram_chats)
        self.assertLessEqual(len(self.server.ram_chats), self.server.max_ram_chats)

        # Legacy-style invariant check: no chat can be in both tiers.
        overlap = set(self.server.vram_chats).intersection(self.server.ram_chats)
        self.assertEqual(overlap, set())

    @timeout(0.4)
    def test_level4_case_12_oldest_tie_breaker_uses_insertion_order(self):
        self.server.handle_request("b", 1, "msg")
        self.server.handle_request("a", 1, "msg")
        self.server.handle_request("c", 2, "msg")

        # With equal oldest timestamps for "a" and "b", insertion-order evicts "b".
        self.assertIn("b", self.server.ram_chats)
        self.assertIn("a", self.server.vram_chats)

    @timeout(0.4)
    def test_level4_case_13_constructor_requires_min_capacity(self):
        with self.assertRaises(AssertionError):
            Server(max_vram_chats=1, max_ram_chats=2)
        with self.assertRaises(AssertionError):
            Server(max_vram_chats=2, max_ram_chats=1)
