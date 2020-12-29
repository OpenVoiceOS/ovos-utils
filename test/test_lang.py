import unittest
from ovos_utils.lang.detect import detect_lang, detect_lang_google, \
    detect_lang_naive, detect_lang_neural, code_to_name
from ovos_utils.lang.phonemes import get_phonemes
from ovos_utils.lang.translate import translate_apertium, translate_google, translate_text


class TestLangHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.en = "you are using the open voice os utilities package"
        cls.pt = "olá eu chamo-me joaquim"
        cls.en_bg = "This piece of text is in English. Този текст е на Български."
        cls.fr_en = """\
    France is the largest country in Western Europe and the third-largest in Europe as a whole.
    A accès aux chiens et aux frontaux qui lui ont été il peut consulter et modifier ses collections
    et exporter Cet article concerne le pays européen aujourd’hui appelé République française.
    Pour d’autres usages du nom France, Pour une aide rapide et effective, veuiller trouver votre aide
    dans le menu ci-dessus.
    Motoring events began soon after the construction of the first successful gasoline-fueled automobiles.
    The quick brown fox jumped over the lazy dog."""

    def test_langcode(self):
        # 2 letter lang code
        self.assertEqual(code_to_name("en"), "English")
        self.assertEqual(code_to_name("es"), "Spanish")
        self.assertEqual(code_to_name("pt"), "Portuguese")
        # 4 letter lang code
        self.assertEqual(code_to_name("ca-es"), "Catalan")
        self.assertEqual(code_to_name("en-us"), "English")
        self.assertEqual(code_to_name("pt-pt"), "Portuguese")
        self.assertEqual(code_to_name("pt-br"), "Portuguese")

    def test_detect_lang(self):
        # lang detectors
        self.assertEqual(detect_lang(self.en), "en")
        self.assertEqual(detect_lang_google(self.en), "en")
        self.assertEqual(detect_lang_naive(self.en), "en")
        self.assertEqual(detect_lang_neural(self.en), "en")
        self.assertEqual(detect_lang(self.pt), "pt")

        # mixed lang   cld2
        self.assertEqual(detect_lang_naive(self.fr_en), "fr")
        self.assertEqual(detect_lang_naive(self.en_bg), "bg")
        self.assertEqual(
            detect_lang_naive(self.fr_en, return_multiple=True),
            ['fr', 'en'])
        self.assertEqual(
            detect_lang_naive(self.fr_en, return_dict=True),
            {'lang': 'French', 'lang_code': 'fr', 'conf': 0.58})
        self.assertEqual(
            detect_lang_naive(self.fr_en, hint_language="en",
                              return_dict=True),
            {'lang': 'English', 'lang_code': 'en', 'conf': 0.6})
        self.assertEqual(
            detect_lang_naive(self.fr_en, return_dict=True,
                              return_multiple=True)[1]["conf"],
            0.41)

        # mixed lang cld3
        self.assertEqual(detect_lang_neural(self.en_bg), "en")
        self.assertEqual(
            detect_lang_neural(self.fr_en, return_dict=True),
            {'lang_code': 'fr', 'lang': 'French', 'conf': 0.9675191640853882})
        self.assertEqual(
            detect_lang_neural(self.en_bg, return_dict=True,
                               hint_language="bg"),
            {'lang_code': 'bg', 'lang': 'Bulgarian',
             'conf': 0.9173873066902161})
        self.assertEqual(
            detect_lang_neural(self.en_bg, return_dict=True,
                               return_multiple=True), [
                {'lang_code': 'en', 'lang': 'English',
                 'conf': 0.9999790191650391},
                {'lang_code': 'bg', 'lang': 'Bulgarian',
                 'conf': 0.9173873066902161}
            ])

        # failure cases
        self.assertEqual(detect_lang_neural("hello world"), "ky")

    def test_phonemes(self):
        self.assertEqual(get_phonemes("hey mycroft"),
                         "HH EH Y . M Y K R OW F T")
        self.assertEqual(get_phonemes("hey chatterbox"),
                         "HH EH Y . CH AE T EH R B OW K S")
        self.assertEqual(get_phonemes("alexa"), "AE L EH K S AE")
        self.assertEqual(get_phonemes("siri"), "S IH R IH")
        self.assertEqual(get_phonemes("cortana"), "K OW R T AE N AE")

    def test_translate_apertium(self):
        self.assertEqual(translate_apertium("hello world", "es", "en"),
                         "hola Mundo")
        # apertium by default
        self.assertEqual(translate_text("hola Mundo", "en", "es"),
                         "hello World")

    def test_translate_google(self):
        # source lang optional
        self.assertEqual(translate_google("hello world", "pt"), "Olá Mundo")
        # fallback to google if lang pair not available in apertium
        self.assertEqual(translate_text("hello world", "pt", "en"), "Olá Mundo")
        # fallback to google if no source lang specified
        self.assertEqual(translate_text("hello world", "es"), "Hola Mundo")


