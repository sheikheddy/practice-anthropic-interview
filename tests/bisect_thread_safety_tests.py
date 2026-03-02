import bisect as unsafe_bisect
import signal
import threading
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


def _locked_insort_left(lock: threading.RLock, sequence: list, value: int) -> None:
    with lock:
        index = unsafe_bisect.bisect_left(sequence, value)
        list.insert(sequence, index, value)


class _CoordinatedInsertList(list):
    """List with synchronization hooks to force a race in insort_left."""

    def __init__(self, values):
        super().__init__(values)
        self._both_threads_ready = threading.Barrier(2)
        self._smaller_insert_done = threading.Event()

    def insert(self, index, value):
        self._both_threads_ready.wait(timeout=0.8)
        if value == 17:
            self._smaller_insert_done.wait(timeout=0.8)
        super().insert(index, value)
        if value == 15:
            self._smaller_insert_done.set()


class _BlockingReadList(list):
    """List that can pause the first read mid-bisect."""

    def __init__(self, values):
        super().__init__(values)
        self.first_read_started = threading.Event()
        self.resume_first_read = threading.Event()

    def __getitem__(self, index):
        if not self.first_read_started.is_set():
            self.first_read_started.set()
            self.resume_first_read.wait(timeout=0.8)
        return super().__getitem__(index)


class _OrderedReleaseInsertList(list):
    """List that makes all inserts use stale indices, then commits in a fixed order."""

    def __init__(self, values, num_threads: int, release_order: list[int]):
        super().__init__(values)
        self._all_threads_at_insert = threading.Barrier(num_threads)
        self._release_order = release_order
        self._event_by_value = {value: threading.Event() for value in release_order}
        self._position_by_value = {
            value: i for i, value in enumerate(self._release_order)
        }
        if self._release_order:
            self._event_by_value[self._release_order[0]].set()

    def insert(self, index, value):
        self._all_threads_at_insert.wait(timeout=0.8)
        self._event_by_value[value].wait(timeout=0.8)
        super().insert(index, value)

        current_pos = self._position_by_value[value]
        next_pos = current_pos + 1
        if next_pos < len(self._release_order):
            next_value = self._release_order[next_pos]
            self._event_by_value[next_value].set()


class BisectThreadSafetyTests(unittest.TestCase):
    failureException = Exception

    @timeout(1.0)
    def test_insort_left_on_same_sequence_can_break_sort_order(self):
        shared = _CoordinatedInsertList([10, 20])
        errors: list[BaseException] = []

        def worker(value: int) -> None:
            try:
                unsafe_bisect.insort_left(shared, value)
            except BaseException as exc:  # pragma: no cover - safety for test threading
                errors.append(exc)

        t_small = threading.Thread(target=worker, args=(15,))
        t_large = threading.Thread(target=worker, args=(17,))
        t_small.start()
        t_large.start()
        t_small.join(timeout=0.8)
        t_large.join(timeout=0.8)

        self.assertFalse(t_small.is_alive())
        self.assertFalse(t_large.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(shared, [10, 17, 15, 20])
        self.assertNotEqual(shared, sorted(shared))

    @timeout(1.0)
    def test_mutation_from_another_thread_during_bisect_is_undefined(self):
        shared = _BlockingReadList([10, 20, 30, 40])
        result: dict[str, object] = {}

        def bisect_worker() -> None:
            try:
                result["index"] = unsafe_bisect.bisect_left(shared, 25)
            except BaseException as exc:  # pragma: no cover - safety for test threading
                result["error"] = exc

        worker = threading.Thread(target=bisect_worker)
        worker.start()

        self.assertTrue(shared.first_read_started.wait(timeout=0.8))
        shared.clear()
        shared.resume_first_read.set()
        worker.join(timeout=0.8)

        self.assertFalse(worker.is_alive())
        self.assertIn("error", result)
        self.assertIsInstance(result["error"], IndexError)

    @timeout(1.2)
    def test_many_concurrent_insort_left_preserves_sort_order_with_external_lock(self):
        values = list(range(1, 65))
        shared = _OrderedReleaseInsertList(
            [0, 100], num_threads=len(values), release_order=values
        )
        lock = threading.RLock()
        errors: list[BaseException] = []

        def worker(value: int) -> None:
            try:
                _locked_insort_left(lock, shared, value)
            except BaseException as exc:  # pragma: no cover - safety for test threading
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(value,)) for value in values]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=0.8)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(shared, sorted(shared))
