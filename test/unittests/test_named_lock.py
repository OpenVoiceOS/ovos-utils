import multiprocessing
import time
import unittest
from pathlib import Path

from ovos_utils.lock import ComboLock, NamedLock


def _hold(name, seconds, ready):
    with NamedLock(name):
        ready.set()
        time.sleep(seconds)


class TestNamedLock(unittest.TestCase):
    def test_path_is_combo_lock_path(self):
        lock = NamedLock("ovos_pip.lock")
        self.assertEqual(lock.path.name, "b3Zvc19waXAubG9jaw==.lock")
        self.assertEqual(lock.path.parent.name, "combo_locks")

    def test_non_blocking_fails_in_same_process(self):
        lock = NamedLock("test_named_lock_thread")
        self.assertTrue(lock.acquire())
        self.assertFalse(lock.acquire(blocking=False))
        lock.release()
        self.assertTrue(lock.acquire(blocking=False))
        lock.release()

    def test_other_process_excluded(self):
        ready = multiprocessing.Event()
        proc = multiprocessing.Process(target=_hold, args=("test_named_lock_proc", 1.0, ready))
        proc.start()
        ready.wait(5)
        lock = NamedLock("test_named_lock_proc")
        self.assertFalse(lock.acquire(blocking=False))
        proc.join()
        self.assertTrue(lock.acquire(blocking=False))
        lock.release()

    def test_lock_file_recreated(self):
        lock = NamedLock("test_named_lock_deleted")
        lock.path.unlink()
        with lock:
            self.assertTrue(lock.path.exists())

    def test_combo_lock_context(self):
        path = Path(NamedLock("x").path.parent, "test_combo.lock")
        with ComboLock(path) as lock:
            self.assertFalse(lock.acquire(blocking=False))
