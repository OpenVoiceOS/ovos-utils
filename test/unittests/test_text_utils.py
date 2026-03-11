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

from ovos_utils.text_utils import (
    camel_case_split,
    collapse_whitespaces,
    rm_parentheses,
    remove_accents_and_punct,
)


class TestCamelCaseSplit(unittest.TestCase):
    def test_simple(self) -> None:
        self.assertEqual(camel_case_split("HelloWorld"), "Hello World")

    def test_all_lower(self) -> None:
        self.assertEqual(camel_case_split("hello"), "hello")

    def test_acronym(self) -> None:
        result = camel_case_split("parseHTMLString")
        self.assertIn("HTML", result)

    def test_single_word(self) -> None:
        self.assertEqual(camel_case_split("Word"), "Word")

    def test_multiple_words(self) -> None:
        result = camel_case_split("getFirstName")
        self.assertIn("get", result)
        self.assertIn("First", result)
        self.assertIn("Name", result)


class TestCollapseWhitespaces(unittest.TestCase):
    def test_multiple_spaces(self) -> None:
        self.assertEqual(collapse_whitespaces("hello   world"), "hello world")

    def test_tabs_and_newlines(self) -> None:
        self.assertEqual(collapse_whitespaces("a\t\nb"), "a b")

    def test_leading_trailing(self) -> None:
        self.assertEqual(collapse_whitespaces("  hi  "), " hi ")

    def test_no_change(self) -> None:
        self.assertEqual(collapse_whitespaces("hello world"), "hello world")

    def test_empty(self) -> None:
        self.assertEqual(collapse_whitespaces(""), "")


class TestRmParentheses(unittest.TestCase):
    def test_basic(self) -> None:
        result = rm_parentheses("hello (world)")
        self.assertNotIn("(", result)
        self.assertNotIn("world", result)

    def test_no_parens(self) -> None:
        self.assertEqual(rm_parentheses("hello").strip(), "hello")

    def test_multiple(self) -> None:
        result = rm_parentheses("a (b) c (d)")
        self.assertNotIn("b", result)
        self.assertNotIn("d", result)

    def test_empty_parens(self) -> None:
        result = rm_parentheses("hello () world")
        self.assertNotIn("(", result)


class TestRemoveAccentsAndPunct(unittest.TestCase):
    def test_removes_accents(self) -> None:
        result = remove_accents_and_punct("héllo")
        self.assertNotIn("é", result)
        self.assertIn("h", result)

    def test_removes_punctuation(self) -> None:
        result = remove_accents_and_punct("hello, world!")
        self.assertNotIn(",", result)
        self.assertNotIn("!", result)

    def test_preserves_braces(self) -> None:
        result = remove_accents_and_punct("{slot}")
        self.assertIn("{", result)
        self.assertIn("}", result)

    def test_plain_text_unchanged(self) -> None:
        result = remove_accents_and_punct("hello world")
        self.assertIn("hello", result)
        self.assertIn("world", result)


if __name__ == "__main__":
    unittest.main()
