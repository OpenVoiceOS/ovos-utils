# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import time
import unittest
from threading import Thread


class TestCreateDaemon(unittest.TestCase):
    def test_returns_thread(self):
        from ovos_utils.thread_utils import create_daemon
        result = []
        t = create_daemon(target=lambda: result.append(1))
        t.join(timeout=2.0)
        self.assertIsInstance(t, Thread)
        self.assertEqual(result, [1])

    def test_is_daemon(self):
        from ovos_utils.thread_utils import create_daemon
        t = create_daemon(target=lambda: None)
        self.assertTrue(t.daemon)

    def test_autostart_true(self):
        from ovos_utils.thread_utils import create_daemon
        started = []
        t = create_daemon(target=lambda: started.append(True), autostart=True)
        t.join(timeout=2.0)
        self.assertEqual(started, [True])

    def test_autostart_false(self):
        from ovos_utils.thread_utils import create_daemon
        t = create_daemon(target=lambda: None, autostart=False)
        self.assertFalse(t.is_alive())

    def test_args_passed(self):
        from ovos_utils.thread_utils import create_daemon
        result = []
        t = create_daemon(target=lambda x, y: result.append(x + y), args=(3, 4))
        t.join(timeout=2.0)
        self.assertEqual(result, [7])

    def test_kwargs_passed(self):
        from ovos_utils.thread_utils import create_daemon
        result = {}

        def fn(key, value):
            result[key] = value

        t = create_daemon(target=fn, kwargs={"key": "k", "value": "v"})
        t.join(timeout=2.0)
        self.assertEqual(result, {"k": "v"})


class TestCreateKillableDaemon(unittest.TestCase):
    def test_returns_kthread(self):
        import kthread
        from ovos_utils.thread_utils import create_killable_daemon
        t = create_killable_daemon(target=lambda: None)
        t.join(timeout=2.0)
        self.assertIsInstance(t, kthread.KThread)

    def test_is_daemon(self):
        from ovos_utils.thread_utils import create_killable_daemon
        t = create_killable_daemon(target=lambda: None)
        self.assertTrue(t.daemon)

    def test_autostart_false(self):
        from ovos_utils.thread_utils import create_killable_daemon
        t = create_killable_daemon(target=lambda: None, autostart=False)
        self.assertFalse(t.is_alive())

    def test_runs_target(self):
        from ovos_utils.thread_utils import create_killable_daemon
        result = []
        t = create_killable_daemon(target=lambda: result.append(42))
        t.join(timeout=2.0)
        self.assertEqual(result, [42])

    def test_args_passed(self):
        from ovos_utils.thread_utils import create_killable_daemon
        result = []
        t = create_killable_daemon(target=lambda x: result.append(x), args=(99,))
        t.join(timeout=2.0)
        self.assertEqual(result, [99])


class TestThreadedTimeout(unittest.TestCase):
    def test_function_completes_within_timeout(self):
        from ovos_utils.thread_utils import threaded_timeout

        @threaded_timeout(timeout=5)
        def fast_func():
            return 42

        result = fast_func()
        self.assertEqual(result, 42)

    def test_timeout_raises_exception(self):
        from ovos_utils.thread_utils import threaded_timeout

        @threaded_timeout(timeout=1)
        def slow_func():
            time.sleep(10)

        with self.assertRaises(Exception):
            slow_func()

    def test_exception_in_func_is_reraised(self):
        from ovos_utils.thread_utils import threaded_timeout

        @threaded_timeout(timeout=5)
        def failing_func():
            raise ValueError("test error")

        with self.assertRaises(ValueError):
            failing_func()

    def test_preserves_function_name(self):
        from ovos_utils.thread_utils import threaded_timeout

        @threaded_timeout(timeout=5)
        def my_named_function():
            return "ok"

        self.assertEqual(my_named_function.__name__, "my_named_function")

    def test_args_and_kwargs(self):
        from ovos_utils.thread_utils import threaded_timeout

        @threaded_timeout(timeout=5)
        def add(a, b=0):
            return a + b

        result = add(3, b=4)
        self.assertEqual(result, 7)

    def test_default_timeout(self):
        from ovos_utils.thread_utils import threaded_timeout

        @threaded_timeout()
        def quick():
            return "done"

        self.assertEqual(quick(), "done")


if __name__ == "__main__":
    unittest.main()
