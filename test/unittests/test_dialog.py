# Copyright 2024, OpenVoiceOS
#
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

"""Unit tests for ovos_utils.dialog module."""

import unittest
from unittest.mock import patch, MagicMock


class TestJoinList(unittest.TestCase):
    """Tests for join_list function."""

    def test_empty_list(self) -> None:
        """join_list with empty list should return empty string."""
        from ovos_utils.dialog import join_list
        result = join_list([], "and")
        self.assertEqual(result, "")

    def test_single_item(self) -> None:
        """join_list with one item should return that item as string."""
        from ovos_utils.dialog import join_list
        result = join_list(["apple"], "and")
        self.assertEqual(result, "apple")

    @patch("ovos_utils.dialog.translate_word", return_value="and")
    def test_multiple_items(self, mock_translate: MagicMock) -> None:
        """join_list with multiple items should join with comma and connector."""
        from ovos_utils.dialog import join_list
        result = join_list(["a", "b", "c"], "and", lang="en-us")
        self.assertEqual(result, "a, b and c")
        mock_translate.assert_called_once_with("and", "en-us")

    @patch("ovos_utils.dialog.translate_word", return_value="or")
    def test_custom_separator(self, mock_translate: MagicMock) -> None:
        """join_list with custom sep should use it between items."""
        from ovos_utils.dialog import join_list
        result = join_list(["a", "b", "c"], "or", sep=";", lang="en-us")
        self.assertEqual(result, "a; b or c")


if __name__ == "__main__":
    unittest.main()
