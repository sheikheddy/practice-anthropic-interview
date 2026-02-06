import inspect
import os
import signal
import sys
from unittest.mock import patch

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

from chat_server_level3_impl import ChatClient, ChatResponse


class ChatServerLevel3Tests(unittest.TestCase):
    failureException = Exception

    def setUp(self):
        self.client = ChatClient()

    @timeout(0.4)
    def test_level3_case_01_add_and_remove_server(self):
        self.assertTrue(self.client.add_server("s1", 2))
        self.assertFalse(self.client.add_server("s1", 1))
        self.assertTrue(self.client.remove_server("s1"))
        self.assertFalse(self.client.remove_server("s1"))

    @timeout(0.4)
    def test_level3_case_02_get_current_server_without_affinity_uses_ring(self):
        self.client.add_server("s1", 1)
        self.client.add_server("s2", 1)
        self.assertEqual(
            self.client.get_current_server("chat-a"),
            self.client.ring.get_server("chat-a"),
        )

    @timeout(0.4)
    def test_level3_case_03_send_message_sets_affinity_on_success(self):
        self.client.add_server("s1", 1)
        with patch("chat_server_level3_impl.post_fn") as mock_post:
            mock_post.return_value = ChatResponse(True, "ok")
            reply = self.client.send_chat_message("chat-a", "hello")
        self.assertEqual(reply, "ok")
        self.assertEqual(self.client.chat_to_server["chat-a"], "s1")

    @timeout(0.4)
    def test_level3_case_04_affinity_server_tried_first_then_failover(self):
        self.client.add_server("s1", 1)
        self.client.add_server("s2", 1)
        self.client.chat_to_server["chat-a"] = "s1"

        calls = []

        def fake_post(server_id: str, chat_id: str, message: str):
            calls.append(server_id)
            if server_id == "s1":
                return ChatResponse(False, "")
            return ChatResponse(True, "recovered")

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            reply = self.client.send_chat_message("chat-a", "hello")

        self.assertEqual(calls[0], "s1")
        self.assertEqual(reply, "recovered")
        self.assertEqual(self.client.chat_to_server["chat-a"], "s2")

    @timeout(0.4)
    def test_level3_case_05_failover_skips_duplicate_virtual_nodes(self):
        self.client.add_server("s1", 4)
        self.client.add_server("s2", 1)
        self.client.chat_to_server["chat-a"] = "s1"

        calls = []

        def fake_post(server_id: str, chat_id: str, message: str):
            calls.append(server_id)
            if server_id == "s1":
                return ChatResponse(False, "")
            return ChatResponse(True, "ok")

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            self.assertEqual(self.client.send_chat_message("chat-a", "hello"), "ok")

        self.assertEqual(calls.count("s1"), 1)
        self.assertEqual(calls.count("s2"), 1)

    @timeout(0.4)
    def test_level3_case_06_all_servers_failing_raises_runtime_error(self):
        self.client.add_server("s1", 2)
        self.client.add_server("s2", 2)
        self.client.chat_to_server["chat-a"] = "s1"

        with patch("chat_server_level3_impl.post_fn", return_value=ChatResponse(False, "")):
            with self.assertRaises(RuntimeError):
                self.client.send_chat_message("chat-a", "hello")

        self.assertNotIn("chat-a", self.client.chat_to_server)

    @timeout(0.4)
    def test_level3_case_07_remove_server_clears_affinity(self):
        self.client.add_server("s1", 1)
        self.client.add_server("s2", 1)
        self.client.chat_to_server["chat-a"] = "s1"
        self.client.chat_to_server["chat-b"] = "s2"

        self.client.remove_server("s1")
        self.assertNotIn("chat-a", self.client.chat_to_server)
        self.assertIn("chat-b", self.client.chat_to_server)

    @timeout(0.4)
    def test_level3_case_08_get_current_server_no_servers_raises(self):
        with self.assertRaises(ValueError):
            self.client.get_current_server("chat-a")

    @timeout(0.4)
    def test_level3_case_09_send_with_no_servers_raises(self):
        with self.assertRaises(RuntimeError):
            self.client.send_chat_message("chat-a", "hello")

    @timeout(0.4)
    def test_level3_case_10_failover_walks_ring_in_hash_order(self):
        self.client.add_server("s1", 2)
        self.client.add_server("s2", 1)
        self.client.add_server("s3", 1)
        chat_id = "chat-order"

        expected_order = list(self.client._iter_ring_servers(chat_id))
        actual_order = []

        def fake_post(server_id: str, _chat_id: str, _message: str):
            actual_order.append(server_id)
            return ChatResponse(False, "")

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            with self.assertRaises(RuntimeError):
                self.client.send_chat_message(chat_id, "hello")

        self.assertEqual(actual_order, expected_order)

    @timeout(0.4)
    def test_level3_case_11_affinity_persists_after_successful_failover(self):
        self.client.add_server("s1", 1)
        self.client.add_server("s2", 1)
        self.client.chat_to_server["chat-a"] = "s1"

        calls = []

        def fake_post(server_id: str, _chat_id: str, _message: str):
            calls.append(server_id)
            if len(calls) == 1 and server_id == "s1":
                return ChatResponse(False, "")
            return ChatResponse(True, f"ok-{server_id}")

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            first = self.client.send_chat_message("chat-a", "m1")
            second = self.client.send_chat_message("chat-a", "m2")

        self.assertEqual(first, "ok-s2")
        self.assertEqual(second, "ok-s2")
        self.assertEqual(calls[1], "s2")

    @timeout(0.4)
    def test_level3_case_12_multiple_chats_keep_independent_affinity(self):
        self.client.add_server("s1", 1)
        self.client.add_server("s2", 1)

        outcomes = {
            ("s1", "chat-a"): ChatResponse(True, "a"),
            ("s2", "chat-a"): ChatResponse(False, ""),
            ("s1", "chat-b"): ChatResponse(False, ""),
            ("s2", "chat-b"): ChatResponse(True, "b"),
        }

        def fake_post(server_id: str, chat_id: str, _message: str):
            return outcomes.get((server_id, chat_id), ChatResponse(True, "default"))

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            self.assertEqual(self.client.send_chat_message("chat-a", "hello"), "a")
            self.assertEqual(self.client.send_chat_message("chat-b", "hello"), "b")

        self.assertEqual(self.client.chat_to_server["chat-a"], "s1")
        self.assertEqual(self.client.chat_to_server["chat-b"], "s2")
