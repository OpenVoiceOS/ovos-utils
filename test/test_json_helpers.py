import unittest
from copy import deepcopy
from ovos_utils.json_helper import merge_dict


class TestJsonHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.base_dict = {"one": 1, "two": 2, "three": 3,
                          "four": ["foo", "bar", "baz"], "five": 50}
        self.delta_dict = {"two": 2, "three": 30,
                           "four": [4, 5, 6, "foo"], "five": None}

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
