import json
import os.path
import unittest

from ovos_utils.bracket_expansion import expand_template, expand_slots


class TestTemplateExpansion(unittest.TestCase):

    def test_expand_slots(self):
        # Test for expanding slots
        template = "change [the ]brightness to {brightness_level} and color to {color_name}"
        slots = {
            "brightness_level": ["low", "medium", "high"],
            "color_name": ["red", "green", "blue"]
        }

        expanded_sentences = expand_slots(template, slots)

        expected_sentences = ['change brightness to low and color to red',
                              'change brightness to low and color to green',
                              'change brightness to low and color to blue',
                              'change brightness to medium and color to red',
                              'change brightness to medium and color to green',
                              'change brightness to medium and color to blue',
                              'change brightness to high and color to red',
                              'change brightness to high and color to green',
                              'change brightness to high and color to blue',
                              'change the brightness to low and color to red',
                              'change the brightness to low and color to green',
                              'change the brightness to low and color to blue',
                              'change the brightness to medium and color to red',
                              'change the brightness to medium and color to green',
                              'change the brightness to medium and color to blue',
                              'change the brightness to high and color to red',
                              'change the brightness to high and color to green',
                              'change the brightness to high and color to blue']
        self.assertEqual(expanded_sentences, expected_sentences)

    def test_expand_template(self):
        expected_outputs = {
            "[hello,] (call me|my name is) {name}": [
                "call me {name}",
                "hello, call me {name}",
                "hello, my name is {name}",
                "my name is {name}"
            ],
            "Expand (alternative|choices) into a list of choices.": [
                "Expand alternative into a list of choices.",
                "Expand choices into a list of choices."
            ],
            "sentences have [optional] words ": [
                "sentences have  words",
                "sentences have optional words"
            ],
            "alternative words can be (used|written)": [
                "alternative words can be used",
                "alternative words can be written"
            ],
            "sentence[s] can have (pre|suf)fixes mid word too": [
                "sentence can have prefixes mid word too",
                "sentence can have suffixes mid word too",
                "sentences can have prefixes mid word too",
                "sentences can have suffixes mid word too"
            ],
            "do( the | )thing(s|) (old|with) style and( no | )spaces": [
                "do the thing old style and no spaces",
                "do the thing old style and spaces",
                "do the thing with style and no spaces",
                "do the thing with style and spaces",
                "do the things old style and no spaces",
                "do the things old style and spaces",
                "do the things with style and no spaces",
                "do the things with style and spaces",
                "do thing old style and no spaces",
                "do thing old style and spaces",
                "do thing with style and no spaces",
                "do thing with style and spaces",
                "do things old style and no spaces",
                "do things old style and spaces",
                "do things with style and no spaces",
                "do things with style and spaces"
            ],
            "[(this|that) is optional]": [
                '',
                'that is optional',
                'this is optional'],
            "tell me a [{joke_type}] joke": [
                "tell me a  joke",
                "tell me a {joke_type} joke"
            ],
            "play {query} [in ({device_name}|{skill_name}|{zone_name})]": [
                "play {query}",
                "play {query} in {device_name}",
                "play {query} in {skill_name}",
                "play {query} in {zone_name}"
            ]
        }

        for template, expected_sentences in expected_outputs.items():
            with self.subTest(template=template):
                expanded_sentences = expand_template(template)
                self.assertEqual(expanded_sentences, expected_sentences)

    def test_long(self):
        # problematic examples taken from https://github.com/OpenVoiceOS/ovos-padatious-pipeline-plugin/issues/9
        with open(os.path.join(os.path.dirname(__file__), "test_de_expansion.json")) as f:
            expected_outputs = json.load(f)

        for template, expected_sentences in expected_outputs.items():
            with self.subTest(template=template):
                expanded_sentences = expand_template(template)
                self.assertEqual(expanded_sentences, expected_sentences)


if __name__ == '__main__':
    unittest.main()
