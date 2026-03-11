# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import unittest
import warnings


class TestExpandParentheses(unittest.TestCase):
    """Tests for the deprecated expand_parentheses function."""

    def test_basic_expansion(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_parentheses
            result = expand_parentheses(["hello", "(", "world", "|", "there", ")"])
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)

    def test_no_parentheses(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_parentheses
            result = expand_parentheses(["hello", "world"])
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], ["hello", "world"])

    def test_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import expand_parentheses
            expand_parentheses(["a"])
            # Check that a DeprecationWarning was issued
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

    def test_returns_list_of_lists(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_parentheses
            result = expand_parentheses(["(", "a", "|", "b", ")"])
            self.assertIsInstance(result, list)
            for item in result:
                self.assertIsInstance(item, list)


class TestExpandOptions(unittest.TestCase):
    """Tests for the deprecated expand_options function."""

    def test_basic_expansion(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_options
            result = expand_options("test (a|b)")
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)
            self.assertIn("test a", result)
            self.assertIn("test b", result)

    def test_no_parentheses(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_options
            result = expand_options("hello world")
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0], "hello world")

    def test_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import expand_options
            expand_options("test (x|y)")
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

    def test_multiple_options(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_options
            result = expand_options("(a|b|c)")
            self.assertEqual(len(result), 3)

    def test_returns_strings(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import expand_options
            result = expand_options("test (x|y)")
            for item in result:
                self.assertIsInstance(item, str)


class TestSentenceTreeParser(unittest.TestCase):
    """Tests for the deprecated SentenceTreeParser class."""

    def _get_parser(self, tokens):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import SentenceTreeParser
            return SentenceTreeParser(tokens)

    def test_instantiation_emits_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import SentenceTreeParser
            SentenceTreeParser(["hello"])
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

    def test_expand_parentheses_simple(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import SentenceTreeParser
            parser = SentenceTreeParser(["hello", "world"])
            result = parser.expand_parentheses()
            self.assertIsInstance(result, list)

    def test_expand_parentheses_with_options(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import SentenceTreeParser
            parser = SentenceTreeParser(["(", "a", "|", "b", ")"])
            result = parser.expand_parentheses()
            self.assertIsInstance(result, list)
            self.assertGreaterEqual(len(result), 2)


class TestDeprecatedClasses(unittest.TestCase):
    """Tests for Fragment, Word, Sentence, Options deprecated classes."""

    def test_fragment_emits_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import Fragment
            Fragment("test")
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

    def test_word_emits_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import Word
            Word("hello")
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

    def test_word_expand(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import Word
            w = Word("hello")
            result = w.expand()
            self.assertIsInstance(result, list)
            self.assertEqual(result, [["hello"]])

    def test_fragment_expand(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ovos_utils.bracket_expansion import Fragment
            f = Fragment("test")
            result = f.expand()
            self.assertEqual(result, [[]])

    def test_sentence_emits_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import Sentence, Word
            w_obj = Word("hello")
            from ovos_utils.bracket_expansion import Sentence
            Sentence([w_obj])
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

    def test_options_emits_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from ovos_utils.bracket_expansion import Options, Word
            w_obj = Word("hello")
            from ovos_utils.bracket_expansion import Options
            Options([w_obj])
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))


if __name__ == "__main__":
    unittest.main()
