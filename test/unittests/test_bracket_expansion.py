import unittest

from ovos_utils.bracket_expansion import expand_slots


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




if __name__ == '__main__':
    unittest.main()
