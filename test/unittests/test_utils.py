import unittest

from ovos_utils import rotate_list, camel_case_split, get_handler_name, flatten_list


class TestHelpers(unittest.TestCase):

    def test_utils(self):
        def some_function():
            return

        self.assertEqual(get_handler_name(some_function), "some_function")
        self.assertEqual(get_handler_name(self.test_utils), "test_utils")

        self.assertEqual(camel_case_split("MyAwesomeSkill"),
                         "My Awesome Skill")

    def test_list_utils(self):
        self.assertEqual(rotate_list([1, 2, 3]), [2, 3, 1])
        self.assertEqual(rotate_list([1, 2, 3], 2), [3, 1, 2])
        self.assertEqual(rotate_list([1, 2, 3], 3), [1, 2, 3])

        self.assertEqual(rotate_list([1, 2, 3], -1), [3, 1, 2])
        self.assertEqual(rotate_list([1, 2, 3], -2), [2, 3, 1])
        self.assertEqual(rotate_list([1, 2, 3], -3), [1, 2, 3])

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
