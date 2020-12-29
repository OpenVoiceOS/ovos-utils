import unittest
from ovos_utils import rotate_list, camel_case_split, camelize, \
    transliterate, titleize, parameterize, ordinalize, get_handler_name


class TestHelpers(unittest.TestCase):

    def test_inflection_utils(self):
        # just imports from inflection package
        # https://inflection.readthedocs.io/en/latest/
        self.assertEqual(camelize("device_type"), "DeviceType")
        self.assertEqual(titleize("MyAwesome_Skill"), "My Awesome Skill")
        self.assertEqual(transliterate('Ærøskøbing'), 'rskbing')
        self.assertEqual(parameterize("Donald E. Knuth"), 'donald-e-knuth')
        self.assertEqual(ordinalize(5), '5th')
        self.assertEqual(ordinalize(2), '2nd')

    def test_utils(self):
        def some_function():
            return

        self.assertEqual(get_handler_name(some_function), "some_function")
        self.assertEqual(get_handler_name(self.test_utils), "test_utils")

        self.assertEqual(camel_case_split("MyAwesomeSkill"),
                         "My Awesome Skill")

        self.assertEqual(rotate_list([1, 2, 3]), [2, 3, 1])
        self.assertEqual(rotate_list([1, 2, 3], 2), [3, 1, 2])
        self.assertEqual(rotate_list([1, 2, 3], 3), [1, 2, 3])

        self.assertEqual(rotate_list([1, 2, 3], -1), [3, 1, 2])
        self.assertEqual(rotate_list([1, 2, 3], -2), [2, 3, 1])
        self.assertEqual(rotate_list([1, 2, 3], -3), [1, 2, 3])
