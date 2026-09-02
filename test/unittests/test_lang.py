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

"""Unit tests for ovos_utils.lang module."""

import os
import tempfile
import unittest
from unittest.mock import patch

class TestTranslateWord(unittest.TestCase):
    """Tests for translate_word."""

    def test_returns_name_when_no_file(self) -> None:
        """translate_word should return the word name when no translation file exists."""
        from ovos_utils.lang import translate_word
        with patch("ovos_utils.lang.resolve_resource_file", return_value=None):
            result = translate_word("hello", lang="en-US")
        self.assertEqual(result, "hello")

    def test_reads_translation_from_file(self) -> None:
        """translate_word should return the first non-comment line from the word file."""
        from ovos_utils.lang import translate_word

        with tempfile.NamedTemporaryFile(mode="w", suffix=".word", delete=False) as f:
            f.write("# this is a comment\n")
            f.write("hola\n")
            fname = f.name

        try:
            with patch("ovos_utils.lang.resolve_resource_file", return_value=fname):
                result = translate_word("hello", lang="es-ES")
            self.assertEqual(result, "hola")
        finally:
            os.unlink(fname)

    def test_skips_comment_lines(self) -> None:
        """translate_word should skip lines starting with #."""
        from ovos_utils.lang import translate_word

        with tempfile.NamedTemporaryFile(mode="w", suffix=".word", delete=False) as f:
            f.write("# comment\n")
            f.write("# another comment\n")
            f.write("bonjour\n")
            fname = f.name

        try:
            with patch("ovos_utils.lang.resolve_resource_file", return_value=fname):
                result = translate_word("hello", lang="fr-FR")
            self.assertEqual(result, "bonjour")
        finally:
            os.unlink(fname)


class TestPhonemes(unittest.TestCase):
    """Tests for phoneme lookup tables."""

    def test_arpabet_to_ipa_mapping(self) -> None:
        """arpabet2ipa and ipa2arpabet should be inverse mappings."""
        from ovos_utils.lang.phonemes import arpabet2ipa, ipa2arpabet
        for key, val in arpabet2ipa.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)
            self.assertEqual(ipa2arpabet[val], key)


class TestVisemes(unittest.TestCase):
    """Tests for the VISIMES lookup table."""

    def test_visimes_keys_and_values_are_strings(self) -> None:
        """All keys and values in VISIMES should be strings."""
        from ovos_utils.lang.visimes import VISIMES
        for key, val in VISIMES.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)


if __name__ == "__main__":
    unittest.main()
