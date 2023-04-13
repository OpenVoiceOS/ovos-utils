import unittest


class TestLang(unittest.TestCase):
    def test_get_language_dir(self):
        from ovos_utils.lang import get_language_dir
        # TODO

    def test_translate_word(self):
        from ovos_utils.lang import translate_word
        # TODO

    def test_phonemes(self):
        from ovos_utils.lang.phonemes import arpabet2ipa, ipa2arpabet
        for key, val in arpabet2ipa.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)
            self.assertEqual(ipa2arpabet[val], key)

    def test_visemes(self):
        from ovos_utils.lang.visimes import VISIMES
        for key, val in VISIMES.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, str)