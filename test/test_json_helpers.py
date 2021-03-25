import unittest
from copy import deepcopy
from ovos_utils.json_helper import merge_dict, is_compatible_dict, delete_key_from_dict


class TestJsonHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.base_dict = {"one": 1, "two": 2, "three": 3,
                          "four": ["foo", "bar", "baz"], "five": 50}
        self.delta_dict = {"two": 2, "three": 30,
                           "four": [4, 5, 6, "foo"], "five": None}

    def test_delete_key_from_dict(self):
        dct = {'a': 1, 'b': {'c': 1, 'd': 2}}
        self.assertEqual(delete_key_from_dict("b", dct), {'a': 1})
        self.assertEqual(delete_key_from_dict("a", dct),
                         {'b': {'c': 1, 'd': 2}})
        self.assertEqual(delete_key_from_dict("b.c", dct),
                         {'a': 1, 'b': {'d': 2}})
        self.assertEqual(delete_key_from_dict("b.d", dct),
                         {'a': 1, 'b': {'c': 1}})

    def test_compatible_dict(self):
        d0 = {"k2": 2, "k3": [0, 0], "k4": {"not": "yeah"}}
        d1 = {"k": "val", "k2": 1, "k3": [], "k5": None}
        d2 = {"k4": {"a": 0}}
        d3 = {"k2": "2", "k4": {"a": ["type_changed"]}}

        self.assertEqual(is_compatible_dict(d0, d1), True)
        self.assertEqual(is_compatible_dict(d0, d2), True)
        self.assertEqual(is_compatible_dict(d1, d2), True)
        self.assertEqual(is_compatible_dict(d0, d3), False) # k2 type changed
        self.assertEqual(is_compatible_dict(d1, d3), False) # k4 type changed
        self.assertEqual(is_compatible_dict(d2, d3), False) # k4 dicts incompatible

    def test_merge_dict(self):
        self.assertEqual(
            merge_dict(deepcopy(self.base_dict), deepcopy(self.delta_dict)),
            {"one": 1, "two": 2, "three": 30, "four": [
                4, 5, 6, "foo"], "five": None}
        )

    def test_merge_dict_lists(self):

        self.assertEqual(
            merge_dict(deepcopy(self.base_dict), deepcopy(self.delta_dict),
                       merge_lists=True, no_dupes=False),
            {"one": 1, "two": 2, "three": 30, "four": [
                "foo", "bar", "baz", 4, 5, 6, "foo"], "five": None}
        )

    def test_merge_dict_skip_empty(self):

        self.assertEqual(
            merge_dict(deepcopy(self.base_dict), deepcopy(self.delta_dict),
                       merge_lists=True, skip_empty=True, no_dupes=False),
            {"one": 1, "two": 2, "three": 30, "four": [
                "foo", "bar", "baz", 4, 5, 6, "foo"], "five": 50}
        )

        # NOT merging empty string / list / None
        self.assertEqual(
            merge_dict(deepcopy(self.base_dict),
                       {"val": None,  "val2": "",  "val3": []},
                       skip_empty=True), self.base_dict
        )

        # merging False and 0 and " "
        self.assertEqual(
            merge_dict(deepcopy(self.base_dict),
                       {"one": False, "two": 0, "four": " "},
                       skip_empty=True),
            {"one": False, "two": 0, "three": 3, "four": " ", "five": 50}
        )


    # Difficult to test because order is not currently guaranteed.

    def test_merge_dict_no_dupes(self):

        self.assertEqual(
            merge_dict(deepcopy(self.base_dict), deepcopy(self.delta_dict), merge_lists=True,
                       skip_empty=True, no_dupes=True),
            {"one": 1, "two": 2, "three": 30, "four": [
                "foo", "bar", "baz", 4, 5, 6], "five": 50}
        )
