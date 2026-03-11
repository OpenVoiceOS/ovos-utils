# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import unittest
from ovos_utils.parse import (
    MatchStrategy,
    fuzzy_match,
    match_one,
    match_all,
    remove_parentheses,
    _validate_matching_strategy,
)


class TestMatchStrategy(unittest.TestCase):
    def test_enum_values(self):
        self.assertIsInstance(MatchStrategy.SIMPLE_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.PARTIAL_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.TOKEN_SORT_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.TOKEN_SET_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.PARTIAL_TOKEN_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.PARTIAL_TOKEN_SORT_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.PARTIAL_TOKEN_SET_RATIO, MatchStrategy)
        self.assertIsInstance(MatchStrategy.DAMERAU_LEVENSHTEIN_SIMILARITY, MatchStrategy)

    def test_enum_is_int(self):
        self.assertIsInstance(MatchStrategy.SIMPLE_RATIO, int)


class TestValidateMatchingStrategy(unittest.TestCase):
    def test_simple_ratio_always_valid(self):
        result = _validate_matching_strategy(MatchStrategy.SIMPLE_RATIO)
        self.assertEqual(result, MatchStrategy.SIMPLE_RATIO)

    def test_falls_back_without_rapidfuzz(self):
        import ovos_utils.parse as parse_module
        original = parse_module.rapidfuzz
        parse_module.rapidfuzz = None
        try:
            result = _validate_matching_strategy(MatchStrategy.RATIO)
            self.assertEqual(result, MatchStrategy.SIMPLE_RATIO)
        finally:
            parse_module.rapidfuzz = original


class TestFuzzyMatch(unittest.TestCase):
    def test_identical_strings(self):
        score = fuzzy_match("hello", "hello")
        self.assertAlmostEqual(score, 1.0)

    def test_empty_strings(self):
        score = fuzzy_match("", "")
        self.assertAlmostEqual(score, 1.0)

    def test_completely_different(self):
        score = fuzzy_match("abc", "xyz")
        self.assertLess(score, 0.5)

    def test_partial_match(self):
        score = fuzzy_match("hello world", "hello")
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_returns_float(self):
        score = fuzzy_match("test", "test")
        self.assertIsInstance(score, float)

    def test_simple_ratio_default(self):
        score = fuzzy_match("cat", "cat", strategy=MatchStrategy.SIMPLE_RATIO)
        self.assertAlmostEqual(score, 1.0)

    def test_score_range(self):
        score = fuzzy_match("hello", "world")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestMatchAll(unittest.TestCase):
    def test_list_choices(self):
        results = match_all("apple", ["apple", "banana", "apricot"])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
        # Best match should be "apple"
        self.assertEqual(results[0][0], "apple")

    def test_dict_choices(self):
        choices = {"apple": "fruit_a", "banana": "fruit_b", "cherry": "fruit_c"}
        results = match_all("apple", choices)
        self.assertIsInstance(results, list)
        # Returns values not keys
        self.assertEqual(results[0][0], "fruit_a")

    def test_sorted_descending(self):
        results = match_all("hello", ["hello", "world", "hell"])
        scores = [r[1] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_invalid_choices_type(self):
        with self.assertRaises((ValueError, TypeError)):
            match_all("hello", "not_a_list_or_dict")

    def test_ignore_case(self):
        results = match_all("HELLO", ["hello", "world"], ignore_case=True)
        self.assertGreater(results[0][1], results[1][1])

    def test_custom_match_func(self):
        def always_one(a, b, strategy=None):
            return 1.0

        results = match_all("anything", ["x", "y", "z"], match_func=always_one)
        for _, score in results:
            self.assertAlmostEqual(score, 1.0)

    def test_tuples_returned(self):
        results = match_all("test", ["test", "other"])
        for item in results:
            self.assertEqual(len(item), 2)


class TestMatchOne(unittest.TestCase):
    def test_exact_match(self):
        best, score = match_one("apple", ["apple", "banana", "cherry"])
        self.assertEqual(best, "apple")
        self.assertAlmostEqual(score, 1.0)

    def test_best_from_list(self):
        best, score = match_one("cat", ["dog", "cat", "bird"])
        self.assertEqual(best, "cat")

    def test_dict_input(self):
        choices = {"apple": 1, "banana": 2}
        best, score = match_one("apple", choices)
        self.assertEqual(best, 1)

    def test_ignore_case(self):
        best, score = match_one("APPLE", ["apple", "banana"], ignore_case=True)
        self.assertEqual(best, "apple")


class TestRemoveParentheses(unittest.TestCase):
    def test_square_brackets(self):
        result = remove_parentheses("hello [world]")
        self.assertEqual(result, "hello")

    def test_round_brackets(self):
        result = remove_parentheses("hello (world)")
        self.assertEqual(result, "hello")

    def test_curly_brackets(self):
        result = remove_parentheses("hello {world}")
        self.assertEqual(result, "hello")

    def test_no_brackets(self):
        result = remove_parentheses("hello world")
        self.assertEqual(result, "hello world")

    def test_only_brackets_returns_none(self):
        result = remove_parentheses("[everything]")
        self.assertIsNone(result)

    def test_empty_string_returns_none(self):
        result = remove_parentheses("")
        self.assertIsNone(result)

    def test_mixed_brackets(self):
        result = remove_parentheses("hi [a] (b) {c}")
        self.assertEqual(result, "hi")

    def test_extra_spaces_collapsed(self):
        result = remove_parentheses("hello   world")
        self.assertEqual(result, "hello world")

    def test_unclosed_paren_stripped(self):
        result = remove_parentheses("hello (world")
        self.assertEqual(result, "hello world")


if __name__ == "__main__":
    unittest.main()
