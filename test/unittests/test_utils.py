import signal
import unittest
from os.path import join, dirname
from sys import executable
from subprocess import Popen, TimeoutExpired


class TestHelpers(unittest.TestCase):

    def test_classproperty(self):
        # TODO
        pass

    def test_timed_lru_cache(self):
        # TODO
        pass

    def test_create_killable_daemon(self):
        # TODO
        pass

    def test_create_daemon(self):
        # TODO
        pass

    def test_create_loop(self):
        # TODO
        pass

    def test_wait_for_exit_signal(self):
        test_file = join(dirname(__file__), "scripts", "wait_for_exit.py")
        wait_thread = Popen([executable, test_file])

        # No return
        with self.assertRaises(TimeoutExpired):
            wait_thread.communicate(timeout=1)
        with self.assertRaises(TimeoutExpired):
            wait_thread.communicate(timeout=1)

        # Send interrupt and get returncode 0
        wait_thread.send_signal(signal.SIGINT)
        self.assertEqual(wait_thread.wait(1), 0)

    def test_get_handler_name(self):
        from ovos_utils import get_handler_name

        def some_function():
            return

        self.assertEqual(get_handler_name(some_function), "some_function")

    def test_camel_case_split(self):
        from ovos_utils import camel_case_split
        self.assertEqual(camel_case_split("MyAwesomeSkill"),
                         "My Awesome Skill")

    def test_rotate_list(self):
        from ovos_utils import rotate_list
        self.assertEqual(rotate_list([1, 2, 3]), [2, 3, 1])
        self.assertEqual(rotate_list([1, 2, 3], 2), [3, 1, 2])
        self.assertEqual(rotate_list([1, 2, 3], 3), [1, 2, 3])

        self.assertEqual(rotate_list([1, 2, 3], -1), [3, 1, 2])
        self.assertEqual(rotate_list([1, 2, 3], -2), [2, 3, 1])
        self.assertEqual(rotate_list([1, 2, 3], -3), [1, 2, 3])

    def test_flatten_list(self):
        from ovos_utils import flatten_list
        self.assertEqual(
            flatten_list([["A", "B"], ["C"]]), ["A", "B", "C"]
        )
        self.assertEqual(
            flatten_list([("A", "B")]), ["A", "B"]
        )
        self.assertEqual(
            flatten_list([("A", "B"), ["C"], [["D", ["E", ["F"]]]]]),
            ["A", "B", "C", "D", "E", "F"]
        )

    def test_datestr2ts(self):
        # TODO
        pass
