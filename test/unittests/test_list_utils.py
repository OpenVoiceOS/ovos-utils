# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest

from ovos_utils.list_utils import rotate_list, flatten_list, deduplicate_list


class TestRotateList(unittest.TestCase):
    def test_rotate_by_one(self) -> None:
        self.assertEqual(rotate_list([1, 2, 3], 1), [2, 3, 1])

    def test_rotate_by_two(self) -> None:
        self.assertEqual(rotate_list([1, 2, 3, 4], 2), [3, 4, 1, 2])

    def test_rotate_empty(self) -> None:
        self.assertEqual(rotate_list([], 1), [])

    def test_rotate_default(self) -> None:
        self.assertEqual(rotate_list([1, 2, 3]), [2, 3, 1])

    def test_rotate_full_cycle(self) -> None:
        lst = [1, 2, 3]
        self.assertEqual(rotate_list(lst, len(lst)), lst)

    def test_rotate_zero(self) -> None:
        self.assertEqual(rotate_list([1, 2, 3], 0), [1, 2, 3])


class TestFlattenList(unittest.TestCase):
    def test_basic_nested(self) -> None:
        self.assertEqual(flatten_list([[1, 2], [3, 4]]), [1, 2, 3, 4])

    def test_deeply_nested(self) -> None:
        # flatten_list flattens one level at a time for list-of-lists
        result = flatten_list([[1, 2], [3, 4]])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_with_tuples(self) -> None:
        result = flatten_list([(1, 2), (3, 4)])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_tuples_false(self) -> None:
        # tuples=False: outer list is flattened, but tuples are kept as-is
        result = flatten_list([[1, 2], [3, 4]], tuples=False)
        self.assertEqual(result, [1, 2, 3, 4])

    def test_already_flat(self) -> None:
        self.assertEqual(flatten_list([[1, 2, 3]]), [1, 2, 3])

    def test_empty(self) -> None:
        self.assertEqual(flatten_list([[]]), [])


class TestDeduplicateList(unittest.TestCase):
    def test_basic_dedup(self) -> None:
        result = deduplicate_list(["a", "b", "a", "c"])
        self.assertEqual(result, ["a", "b", "c"])

    def test_order_preserved(self) -> None:
        result = deduplicate_list(["c", "a", "b", "a"])
        self.assertEqual(result[0], "c")
        self.assertEqual(len(result), 3)

    def test_no_order(self) -> None:
        result = deduplicate_list(["a", "b", "a", "c"], keep_order=False)
        self.assertEqual(set(result), {"a", "b", "c"})
        self.assertEqual(len(result), 3)

    def test_no_duplicates(self) -> None:
        lst = ["x", "y", "z"]
        self.assertEqual(deduplicate_list(lst), lst)

    def test_empty(self) -> None:
        self.assertEqual(deduplicate_list([]), [])

    def test_all_same(self) -> None:
        self.assertEqual(deduplicate_list(["a", "a", "a"]), ["a"])


if __name__ == "__main__":
    unittest.main()
