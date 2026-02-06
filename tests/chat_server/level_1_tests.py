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

from chat_server_level1_impl import HashRing, hash


class ChatServerLevel1Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.ring = HashRing()

    @timeout(0.4)
    def test_level1_case_01_hash_is_deterministic(self):
        self.assertEqual(hash("chat-1"), hash("chat-1"))
        self.assertNotEqual(hash("chat-1"), hash("chat-2"))

    @timeout(0.4)
    def test_level1_case_02_add_server_duplicate(self):
        self.assertTrue(self.ring.add_server("s1"))
        self.assertFalse(self.ring.add_server("s1"))

    @timeout(0.4)
    def test_level1_case_03_remove_server_existing_and_missing(self):
        self.ring.add_server("s1")
        self.assertTrue(self.ring.remove_server("s1"))
        self.assertFalse(self.ring.remove_server("s1"))
        self.assertFalse(self.ring.remove_server("missing"))

    @timeout(0.4)
    def test_level1_case_04_get_server_empty_raises(self):
        with self.assertRaises(ValueError):
            self.ring.get_server("chat-x")

    @timeout(0.4)
    def test_level1_case_05_single_server_always_selected(self):
        self.ring.add_server("only")
        for i in range(20):
            self.assertEqual(self.ring.get_server(f"chat-{i}"), "only")

    @timeout(0.4)
    def test_level1_case_06_wraps_to_start_when_hash_after_last(self):
        self.ring.add_server("sA")
        self.ring.add_server("sB")
        max_server_hash = max(hash("sA"), hash("sB"))

        chosen_chat = None
        for i in range(20000):
            chat_id = f"wrap-{i}"
            if hash(chat_id) > max_server_hash:
                chosen_chat = chat_id
                break

        self.assertIsNotNone(chosen_chat)
        first_server = min(self.ring._ring)[1]
        self.assertEqual(self.ring.get_server(chosen_chat), first_server)

    @timeout(0.4)
    def test_level1_case_07_get_server_matches_manual_ring_lookup(self):
        for server_id in ["s1", "s2", "s3", "s4"]:
            self.ring.add_server(server_id)

        sorted_ring = sorted((hash(s), s) for s in ["s1", "s2", "s3", "s4"])
        chats = ["chat-a", "chat-b", "chat-c", "chat-d", "chat-e"]
        for chat_id in chats:
            chat_hash = hash(chat_id)
            expected = sorted_ring[0][1]
            for server_hash, server_id in sorted_ring:
                if server_hash >= chat_hash:
                    expected = server_id
                    break
            self.assertEqual(self.ring.get_server(chat_id), expected)

    @timeout(0.4)
    def test_level1_case_08_removed_server_is_never_returned(self):
        self.ring.add_server("s1")
        self.ring.add_server("s2")
        self.ring.add_server("s3")
        self.ring.remove_server("s2")

        for i in range(100):
            self.assertIn(self.ring.get_server(f"chat-{i}"), {"s1", "s3"})

    @timeout(0.4)
    def test_level1_case_09_mapping_is_stable_across_repeated_calls(self):
        for server_id in ["s1", "s2", "s3"]:
            self.ring.add_server(server_id)

        expected = self.ring.get_server("chat-stable")
        for _ in range(20):
            self.assertEqual(self.ring.get_server("chat-stable"), expected)

    @timeout(0.4)
    def test_level1_case_10_add_order_does_not_change_mapping(self):
        ring_a = HashRing()
        ring_b = HashRing()
        for server_id in ["s1", "s2", "s3", "s4"]:
            ring_a.add_server(server_id)
        for server_id in ["s3", "s1", "s4", "s2"]:
            ring_b.add_server(server_id)

        for i in range(50):
            chat_id = f"chat-{i}"
            self.assertEqual(ring_a.get_server(chat_id), ring_b.get_server(chat_id))

    @timeout(0.4)
    def test_level1_case_11_mixed_add_remove_sequence(self):
        for server_id in ["s1", "s2", "s3", "s4", "s5"]:
            self.assertTrue(self.ring.add_server(server_id))
        self.assertTrue(self.ring.remove_server("s2"))
        self.assertTrue(self.ring.remove_server("s4"))
        self.assertFalse(self.ring.remove_server("s4"))
        self.assertTrue(self.ring.add_server("s2"))

        for i in range(200):
            self.assertIn(self.ring.get_server(f"mix-{i}"), {"s1", "s2", "s3", "s5"})

    @timeout(0.4)
    def test_level1_case_12_large_ring_stability(self):
        for i in range(60):
            self.ring.add_server(f"s{i}")

        chat_id = "very-stable-chat"
        expected = self.ring.get_server(chat_id)
        for _ in range(50):
            self.assertEqual(self.ring.get_server(chat_id), expected)
