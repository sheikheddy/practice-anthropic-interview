import bisect
import inspect
import os
import random
import signal
import sys
from dataclasses import dataclass
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

from chat_server_level1_impl import HashRing, hash
from chat_server_level2_impl import HashRingVirtual
from chat_server_level3_impl import ChatClient, ChatResponse
from chat_server_level4_impl import ChatData, Server
import chat_server_impl as compat


class ChatServerAdversarialTests(unittest.TestCase):
    failureException = Exception

    @timeout(1.0)
    def test_adv_01_level1_randomized_churn_matches_reference(self):
        rng = random.Random(1337)
        ring = HashRing()

        ref_servers = set()
        ref_ring = []
        all_server_ids = [f"s{i}" for i in range(25)]

        def ref_add(server_id: str) -> bool:
            if server_id in ref_servers:
                return False
            ref_servers.add(server_id)
            bisect.insort(ref_ring, (hash(server_id), server_id))
            return True

        def ref_remove(server_id: str) -> bool:
            if server_id not in ref_servers:
                return False
            ref_servers.remove(server_id)
            ref_ring.remove((hash(server_id), server_id))
            return True

        def ref_get(chat_id: str) -> str:
            chat_hash = hash(chat_id)
            idx = bisect.bisect_left(ref_ring, (chat_hash, ""))
            if idx == len(ref_ring):
                idx = 0
            return ref_ring[idx][1]

        for _ in range(400):
            sid = rng.choice(all_server_ids)
            if rng.random() < 0.58:
                self.assertEqual(ring.add_server(sid), ref_add(sid))
            else:
                self.assertEqual(ring.remove_server(sid), ref_remove(sid))

            self.assertEqual(len(ring._ring), len(ref_ring))
            if not ref_ring:
                with self.assertRaises(ValueError):
                    ring.get_server("probe")
            else:
                for _ in range(5):
                    chat_id = f"chat-{rng.randint(0, 9999)}"
                    self.assertEqual(ring.get_server(chat_id), ref_get(chat_id))

    @timeout(1.0)
    def test_adv_02_level1_large_lookup_smoke(self):
        ring = HashRing()
        for i in range(1200):
            ring.add_server(f"s{i}")

        # Hidden tests often include heavy lookup loops.
        first_pass = [ring.get_server(f"chat-{i}") for i in range(5000)]
        second_pass = [ring.get_server(f"chat-{i}") for i in range(5000)]
        self.assertEqual(first_pass, second_pass)

    @timeout(1.0)
    def test_adv_03_level2_virtual_lookup_matches_reference(self):
        ring = HashRingVirtual()
        capacities = {"a": 1, "b": 3, "c": 5, "d": 2}
        for sid, cap in capacities.items():
            ring.add_server(sid, cap)

        ref_ring = []
        for sid, cap in capacities.items():
            for i in range(cap):
                virtual_id = f"{sid}:{i}"
                bisect.insort(ref_ring, (hash(virtual_id), virtual_id, sid))

        for i in range(2000):
            chat_id = f"chat-{i}"
            chat_hash = hash(chat_id)
            idx = bisect.bisect_left(ref_ring, (chat_hash, "", ""))
            if idx == len(ref_ring):
                idx = 0
            self.assertEqual(ring.get_server(chat_id), ref_ring[idx][2])

    @timeout(1.0)
    def test_adv_04_level2_randomized_churn_node_accounting(self):
        rng = random.Random(9001)
        ring = HashRingVirtual()
        capacities: dict[str, int] = {}
        pool = [f"s{i}" for i in range(18)]

        for _ in range(350):
            sid = rng.choice(pool)
            if rng.random() < 0.55:
                cap = rng.randint(1, 6)
                expected = sid not in capacities
                self.assertEqual(ring.add_server(sid, cap), expected)
                if expected:
                    capacities[sid] = cap
            else:
                expected = sid in capacities
                self.assertEqual(ring.remove_server(sid), expected)
                if expected:
                    del capacities[sid]

            expected_nodes = sum(capacities.values())
            self.assertEqual(len(ring._ring), expected_nodes)
            self.assertTrue(all(entry[2] in capacities for entry in ring._ring))

    @timeout(1.0)
    def test_adv_05_level3_failover_tries_each_server_once(self):
        client = ChatClient()
        client.add_server("s1", 7)
        client.add_server("s2", 3)
        client.add_server("s3", 9)

        expected_order = list(client._iter_ring_servers("chat-fail"))
        calls = []

        def fake_post(server_id: str, _chat_id: str, _message: str):
            calls.append(server_id)
            return ChatResponse(False, "")

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            with self.assertRaises(RuntimeError):
                client.send_chat_message("chat-fail", "m")

        self.assertEqual(calls, expected_order)
        self.assertEqual(len(calls), len(client.servers))

    @timeout(1.0)
    def test_adv_06_level3_randomized_mixed_ops_affinity_invariants(self):
        rng = random.Random(42)
        client = ChatClient()
        live_ids = [f"s{i}" for i in range(10)]

        # Ensure non-empty ring for send operations.
        client.add_server("s0", 2)

        def fake_post(server_id: str, _chat_id: str, _message: str):
            return ChatResponse(server_id in client.servers, server_id)

        with patch("chat_server_level3_impl.post_fn", side_effect=fake_post):
            for step in range(450):
                roll = rng.random()
                if roll < 0.18:
                    sid = rng.choice(live_ids)
                    client.add_server(sid, rng.randint(1, 4))
                elif roll < 0.33 and len(client.servers) > 1:
                    sid = rng.choice(list(client.servers))
                    client.remove_server(sid)
                else:
                    chat_id = f"chat-{rng.randint(0, 25)}"
                    reply = client.send_chat_message(chat_id, f"m-{step}")
                    self.assertIn(reply, client.servers)

                for affinity_server in client.chat_to_server.values():
                    self.assertIn(affinity_server, client.servers)

    @timeout(1.2)
    def test_adv_07_level4_randomized_sequence_matches_reference(self):
        @dataclass
        class RefChat:
            chat_id: str
            last_timestamp: int

        class RefServer:
            def __init__(self, max_vram: int, max_ram: int):
                self.max_vram_chats = max_vram
                self.max_ram_chats = max_ram
                self.vram_chats: dict[str, RefChat] = {}
                self.ram_chats: dict[str, RefChat] = {}
                self.num_cache_hits = 0
                self.num_cache_misses = 0
                self.is_online = True

            @staticmethod
            def oldest(chats: dict[str, RefChat], exclude: str | None = None):
                candidates = [v for k, v in chats.items() if k != exclude]
                if not candidates:
                    return None
                return min(candidates, key=lambda c: c.last_timestamp)

            def evict_vram(self):
                victim = self.oldest(self.vram_chats)
                if victim is None:
                    return
                del self.vram_chats[victim.chat_id]
                self.ram_chats[victim.chat_id] = victim

            def handle(self, chat_id: str, ts: int):
                if not self.is_online:
                    return False
                if chat_id in self.vram_chats:
                    self.num_cache_hits += 1
                    self.vram_chats[chat_id].last_timestamp = ts
                    return True
                if chat_id in self.ram_chats:
                    self.num_cache_hits += 1
                    chat = self.ram_chats[chat_id]
                    chat.last_timestamp = ts
                    if len(self.vram_chats) >= self.max_vram_chats:
                        if len(self.ram_chats) >= self.max_ram_chats:
                            victim_ram = self.oldest(self.ram_chats, exclude=chat_id)
                            if victim_ram is not None:
                                del self.ram_chats[victim_ram.chat_id]
                        self.evict_vram()
                    del self.ram_chats[chat_id]
                    self.vram_chats[chat_id] = chat
                    return True

                self.num_cache_misses += 1
                chat = RefChat(chat_id, ts)
                if len(self.vram_chats) >= self.max_vram_chats:
                    if len(self.ram_chats) >= self.max_ram_chats:
                        victim_ram = self.oldest(self.ram_chats)
                        if victim_ram is not None:
                            del self.ram_chats[victim_ram.chat_id]
                    self.evict_vram()
                self.vram_chats[chat_id] = chat
                return True

        rng = random.Random(12345)
        real = Server(max_vram_chats=3, max_ram_chats=4)
        ref = RefServer(max_vram=3, max_ram=4)

        for t in range(1, 700):
            chat_id = f"c{rng.randint(0, 12)}"
            real_resp = real.handle_request(chat_id, t, "m")
            ref_ok = ref.handle(chat_id, t)

            self.assertEqual(real_resp.success, ref_ok)
            self.assertEqual(real.num_cache_hits, ref.num_cache_hits)
            self.assertEqual(real.num_cache_misses, ref.num_cache_misses)
            self.assertEqual(
                {k: v.last_timestamp for k, v in real.vram_chats.items()},
                {k: v.last_timestamp for k, v in ref.vram_chats.items()},
            )
            self.assertEqual(
                {k: v.last_timestamp for k, v in real.ram_chats.items()},
                {k: v.last_timestamp for k, v in ref.ram_chats.items()},
            )
            self.assertLessEqual(len(real.vram_chats), real.max_vram_chats)
            self.assertLessEqual(len(real.ram_chats), real.max_ram_chats)
            self.assertEqual(set(real.vram_chats).intersection(real.ram_chats), set())

    @timeout(1.0)
    def test_adv_08_level4_shutdown_is_state_stable_after_many_requests(self):
        server = Server(max_vram_chats=2, max_ram_chats=3)
        for i in range(8):
            server.handle_request(f"c{i}", i + 1, "msg")
        server.shutdown()

        before_hits = server.num_cache_hits
        before_misses = server.num_cache_misses
        for i in range(20):
            resp = server.handle_request(f"x{i}", 100 + i, "msg")
            self.assertFalse(resp.success)

        self.assertFalse(server.is_online)
        self.assertEqual(server.vram_chats, {})
        self.assertEqual(server.ram_chats, {})
        self.assertEqual(server.num_cache_hits, before_hits)
        self.assertEqual(server.num_cache_misses, before_misses)

    @timeout(1.0)
    def test_adv_09_level4_tie_heavy_eviction_deterministic(self):
        server = Server(max_vram_chats=2, max_ram_chats=2)

        server.handle_request("b", 1, "m")
        server.handle_request("a", 1, "m")
        server.handle_request("d", 2, "m")
        server.handle_request("c", 2, "m")
        server.handle_request("a", 3, "m")

        self.assertEqual(set(server.vram_chats), {"a", "c"})
        self.assertEqual(set(server.ram_chats), {"d"})

    @timeout(1.0)
    def test_adv_10_level4_remove_chat_under_random_state(self):
        rng = random.Random(777)
        server = Server(max_vram_chats=4, max_ram_chats=5)
        for t in range(1, 80):
            server.handle_request(f"c{rng.randint(0, 15)}", t, "m")

        initial_total = server.total_chats
        existing_ids = list(set(server.vram_chats).union(server.ram_chats))
        self.assertGreater(len(existing_ids), 0)
        victim = rng.choice(existing_ids)
        removed = server.remove_chat(victim)

        self.assertIsNotNone(removed)
        self.assertEqual(removed.chat_id, victim)
        self.assertEqual(server.total_chats, initial_total - 1)
        self.assertNotIn(victim, server.vram_chats)
        self.assertNotIn(victim, server.ram_chats)
        self.assertIsNone(server.remove_chat("definitely-missing"))

    @timeout(1.0)
    def test_adv_11_level3_compat_post_fn_patch_is_honored(self):
        client = compat.ChatClient()
        client.add_server("s1", 1)
        client.add_server("s2", 1)

        def compat_post(server_id: str, _chat_id: str, _message: str):
            if server_id == "s1":
                return compat.ChatResponse(False, "")
            return compat.ChatResponse(True, "compat-ok")

        original = compat.post_fn
        compat.post_fn = compat_post
        try:
            reply = client.send_chat_message("chat-compat", "hello")
            self.assertEqual(reply, "compat-ok")
            self.assertEqual(client.chat_to_server["chat-compat"], "s2")
        finally:
            compat.post_fn = original

    @timeout(1.0)
    def test_adv_12_level1_add_server_only_moves_chats_to_new_server(self):
        ring = HashRing()
        for server_id in ["s1", "s2", "s3", "s4"]:
            ring.add_server(server_id)

        chat_ids = [f"chat-{i}" for i in range(6000)]
        before = {chat_id: ring.get_server(chat_id) for chat_id in chat_ids}

        ring.add_server("s-new")
        after = {chat_id: ring.get_server(chat_id) for chat_id in chat_ids}

        moved = [chat_id for chat_id in chat_ids if before[chat_id] != after[chat_id]]
        self.assertGreater(len(moved), 0)
        self.assertTrue(all(after[chat_id] == "s-new" for chat_id in moved))

    @timeout(1.0)
    def test_adv_13_level1_remove_server_only_moves_its_previous_chats(self):
        ring = HashRing()
        servers = ["s1", "s2", "s3", "s4", "s5"]
        for server_id in servers:
            ring.add_server(server_id)

        removed_server = "s3"
        chat_ids = [f"chat-{i}" for i in range(6000)]
        before = {chat_id: ring.get_server(chat_id) for chat_id in chat_ids}

        ring.remove_server(removed_server)
        after = {chat_id: ring.get_server(chat_id) for chat_id in chat_ids}

        for chat_id in chat_ids:
            if before[chat_id] == removed_server:
                self.assertNotEqual(after[chat_id], removed_server)
            else:
                self.assertEqual(after[chat_id], before[chat_id])

    @timeout(1.0)
    def test_adv_14_level2_add_server_only_moves_chats_to_new_server(self):
        ring = HashRingVirtual()
        ring.add_server("a", 2)
        ring.add_server("b", 2)
        ring.add_server("c", 2)

        chat_ids = [f"chat-{i}" for i in range(6000)]
        before = {chat_id: ring.get_server(chat_id) for chat_id in chat_ids}

        ring.add_server("new", 3)
        after = {chat_id: ring.get_server(chat_id) for chat_id in chat_ids}

        moved = [chat_id for chat_id in chat_ids if before[chat_id] != after[chat_id]]
        self.assertGreater(len(moved), 0)
        self.assertTrue(all(after[chat_id] == "new" for chat_id in moved))

    @timeout(1.0)
    def test_adv_15_level3_iter_servers_preserves_wrapped_first_occurrence_order(self):
        client = ChatClient()
        with client._lock:
            client._servers = {"a": 2, "b": 2, "c": 1}
            client._ring = [
                (10, "a:0", "a"),
                (20, "b:0", "b"),
                (30, "a:1", "a"),
                (40, "c:0", "c"),
                (50, "b:1", "b"),
            ]

        original_hash = client._hash
        try:
            # Start from hash=25 -> wrapped stream: a, c, b, a, b -> unique: a, c, b
            client._hash = lambda _chat_id: 25
            self.assertEqual(list(client._iter_ring_servers("x")), ["a", "c", "b"])

            # Start from hash beyond max -> wrapped stream: a, b, a, c, b -> unique: a, b, c
            client._hash = lambda _chat_id: 99
            self.assertEqual(list(client._iter_ring_servers("x")), ["a", "b", "c"])
        finally:
            client._hash = original_hash

    @timeout(1.0)
    def test_adv_16_level4_ram_promotion_excludes_target_from_ram_eviction(self):
        server = Server(max_vram_chats=2, max_ram_chats=2)
        server.handle_request("v1", 1, "m")
        server.handle_request("v2", 2, "m")
        server.handle_request("r1", 3, "m")
        server.handle_request("r2", 4, "m")

        # Promote v1 from RAM when both tiers are full.
        server.handle_request("v1", 5, "m")

        self.assertIn("v1", server.vram_chats)
        self.assertNotIn("v1", server.ram_chats)
        self.assertNotIn("v2", server.ram_chats)
        self.assertIn("r1", server.ram_chats)

    @timeout(1.0)
    def test_adv_17_level4_ram_tie_eviction_uses_insertion_order(self):
        server = Server(max_vram_chats=2, max_ram_chats=2)
        server.handle_request("a", 1, "m")
        server.handle_request("b", 1, "m")
        server.handle_request("c", 2, "m")
        server.handle_request("d", 2, "m")

        # Both RAM entries share oldest timestamp; insertion order should evict "a".
        server.handle_request("e", 3, "m")
        self.assertNotIn("a", server.ram_chats)
        self.assertIn("b", server.ram_chats)

    @timeout(1.2)
    def test_adv_18_level3_iter_servers_matches_reference_across_random_rings(self):
        rng = random.Random(20260302)
        client = ChatClient()

        def expected_order(ring_snapshot, chat_hash: int):
            if not ring_snapshot:
                return []
            start = bisect.bisect_left(ring_snapshot, chat_hash, key=lambda e: e[0])
            if start == len(ring_snapshot):
                start = 0

            seen: set[str] = set()
            ordered: list[str] = []
            for offset in range(len(ring_snapshot)):
                idx = (start + offset) % len(ring_snapshot)
                sid = ring_snapshot[idx][2]
                if sid in seen:
                    continue
                seen.add(sid)
                ordered.append(sid)
            return ordered

        original_hash = client._hash
        try:
            for _ in range(140):
                num_servers = rng.randint(1, 7)
                server_ids = [f"s{i}" for i in range(num_servers)]
                ring_snapshot = []
                server_caps = {}
                for sid in server_ids:
                    cap = rng.randint(1, 5)
                    server_caps[sid] = cap
                    for i in range(cap):
                        point = rng.randint(0, 2_000_000)
                        ring_snapshot.append((point, f"{sid}:{i}", sid))
                ring_snapshot.sort()

                with client._lock:
                    client._servers = dict(server_caps)
                    client._ring = list(ring_snapshot)

                # Probe around boundaries and in random interiors.
                probe_hashes = [0, 2_000_001]
                probe_hashes.extend(point for point, _, _ in ring_snapshot[:6])
                probe_hashes.extend(rng.randint(0, 2_000_001) for _ in range(8))

                for probe in probe_hashes:
                    client._hash = lambda _chat_id, hv=probe: hv
                    actual = list(client._iter_ring_servers("probe"))
                    expected = expected_order(ring_snapshot, probe)
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual, list(dict.fromkeys(actual)))
                    self.assertTrue(set(actual).issubset(set(server_ids)))
        finally:
            client._hash = original_hash

    @timeout(1.3)
    def test_adv_19_level4_tie_heavy_randomized_matches_reference(self):
        @dataclass
        class RefChat:
            chat_id: str
            last_timestamp: int

        class RefServer:
            def __init__(self, max_vram: int, max_ram: int):
                self.max_vram_chats = max_vram
                self.max_ram_chats = max_ram
                self.vram_chats: dict[str, RefChat] = {}
                self.ram_chats: dict[str, RefChat] = {}
                self.num_cache_hits = 0
                self.num_cache_misses = 0
                self.is_online = True

            @staticmethod
            def oldest(chats: dict[str, RefChat], exclude: str | None = None):
                candidates = [v for k, v in chats.items() if k != exclude]
                if not candidates:
                    return None
                return min(candidates, key=lambda c: c.last_timestamp)

            def evict_vram(self):
                victim = self.oldest(self.vram_chats)
                if victim is None:
                    return
                del self.vram_chats[victim.chat_id]
                self.ram_chats[victim.chat_id] = victim

            def ensure_vram_slot(self, exclude_chat_id: str | None = None):
                if len(self.vram_chats) < self.max_vram_chats:
                    return
                if len(self.ram_chats) >= self.max_ram_chats:
                    victim_ram = self.oldest(self.ram_chats, exclude=exclude_chat_id)
                    if victim_ram is not None:
                        del self.ram_chats[victim_ram.chat_id]
                self.evict_vram()

            def handle(self, chat_id: str, ts: int):
                if not self.is_online:
                    return False
                if chat_id in self.vram_chats:
                    self.num_cache_hits += 1
                    self.vram_chats[chat_id].last_timestamp = ts
                    return True
                if chat_id in self.ram_chats:
                    self.num_cache_hits += 1
                    chat = self.ram_chats[chat_id]
                    chat.last_timestamp = ts
                    self.ensure_vram_slot(exclude_chat_id=chat_id)
                    del self.ram_chats[chat_id]
                    self.vram_chats[chat_id] = chat
                    return True

                self.num_cache_misses += 1
                chat = RefChat(chat_id, ts)
                self.ensure_vram_slot()
                self.vram_chats[chat_id] = chat
                return True

            def remove(self, chat_id: str) -> RefChat | None:
                if (chat := self.vram_chats.pop(chat_id, None)) is not None:
                    return chat
                return self.ram_chats.pop(chat_id, None)

        rng = random.Random(314159)
        real = Server(max_vram_chats=3, max_ram_chats=3)
        ref = RefServer(max_vram=3, max_ram=3)

        for _ in range(900):
            if rng.random() < 0.16:
                victim = f"c{rng.randint(0, 14)}"
                real_removed = real.remove_chat(victim)
                ref_removed = ref.remove(victim)
                self.assertEqual(real_removed is not None, ref_removed is not None)
                if real_removed is not None and ref_removed is not None:
                    self.assertEqual(real_removed.chat_id, ref_removed.chat_id)
            else:
                chat_id = f"c{rng.randint(0, 14)}"
                # Tight timestamp range creates many ties and tie-break scenarios.
                timestamp = rng.randint(1, 7)
                real_resp = real.handle_request(chat_id, timestamp, "m")
                ref_ok = ref.handle(chat_id, timestamp)
                self.assertEqual(real_resp.success, ref_ok)

            self.assertEqual(real.num_cache_hits, ref.num_cache_hits)
            self.assertEqual(real.num_cache_misses, ref.num_cache_misses)
            self.assertEqual(
                [k for k in real.vram_chats],
                [k for k in ref.vram_chats],
            )
            self.assertEqual(
                [k for k in real.ram_chats],
                [k for k in ref.ram_chats],
            )
            self.assertEqual(
                {k: v.last_timestamp for k, v in real.vram_chats.items()},
                {k: v.last_timestamp for k, v in ref.vram_chats.items()},
            )
            self.assertEqual(
                {k: v.last_timestamp for k, v in real.ram_chats.items()},
                {k: v.last_timestamp for k, v in ref.ram_chats.items()},
            )
            self.assertLessEqual(len(real.vram_chats), real.max_vram_chats)
            self.assertLessEqual(len(real.ram_chats), real.max_ram_chats)
            self.assertEqual(set(real.vram_chats).intersection(real.ram_chats), set())
