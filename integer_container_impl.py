from bisect import bisect_left, insort
import threading

from integer_container import IntegerContainer


class IntegerContainerImpl(IntegerContainer):
    """
    Concrete implementation of IntegerContainer using a sorted list.
    """

    def __init__(self):
        self._values = []
        self._lock = threading.RLock()

    def add(self, value: int) -> int:
        v = int(value)
        with self._lock:
            insort(self._values, v)
            return len(self._values)

    def delete(self, value: int) -> bool:
        v = int(value)
        with self._lock:
            idx = bisect_left(self._values, v)
            if idx < len(self._values) and self._values[idx] == v:
                del self._values[idx]
                return True
            return False

    def get_median(self) -> int | None:
        with self._lock:
            if not self._values:
                return None
            mid = (len(self._values) - 1) // 2
            return self._values[mid]
