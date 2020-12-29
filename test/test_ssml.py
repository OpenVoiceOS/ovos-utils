import unittest
from ovos_utils.ssml import SSMLBuilder


class TestSSMLhelpers(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.base_utterance = "this is a test of Open Voice OS SSML utils"
        self.base_utterance2 = "creating ssml for usage with text to speech"

    def test_init_flags(self):
        self.assertEqual(
            SSMLBuilder().say(self.base_utterance).build(),
            "<prosody rate='1'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder(speak_tag=True).say(self.base_utterance).build(),
            "<speak>\n<prosody rate='1'>" + self.base_utterance + "</prosody>\n</speak>"
        )
        self.assertEqual(
            SSMLBuilder(ssml_tag=True).say(self.base_utterance).build(),
            "<ssml>\n<prosody rate='1'>" + self.base_utterance + "</prosody>\n</ssml>"
        )
        self.assertEqual(
            SSMLBuilder(speak_tag=True, ssml_tag=True).say(self.base_utterance).build(),
            "<ssml>\n<speak>\n<prosody rate='1'>" + self.base_utterance + "</prosody>\n</speak>\n</ssml>"
        )

    def test_speak_tags(self):
        self.assertEqual(
            SSMLBuilder().say(self.base_utterance).build(),
            "<prosody rate='1'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().say_loud(self.base_utterance).build(),
            "<prosody volume='1.6'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().say_slow(self.base_utterance).build(),
            "<prosody rate='0.4'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().say_fast(self.base_utterance).build(),
            "<prosody rate='1.6'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().say_low_pitch(self.base_utterance).build(),
            "<prosody pitch='-10%'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().say_high_pitch(self.base_utterance).build(),
            "<prosody pitch='+10%'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().say_emphasis(self.base_utterance).build(),
            "<emphasis level='strong'>" + self.base_utterance + "</emphasis>"
        )
        self.assertEqual(
            SSMLBuilder().say_whispered(self.base_utterance).build(),
            "<whispered>" + self.base_utterance + "</whispered>"
        )
        self.assertEqual(
            SSMLBuilder().whisper(self.base_utterance).build(),
            "<whispered>" + self.base_utterance + "</whispered>"
        )
        self.assertEqual(
            SSMLBuilder().sentence(self.base_utterance).build(),
            "<s>" + self.base_utterance + "</s>"
        )
        self.assertEqual(
            SSMLBuilder().paragraph(self.base_utterance).build(),
            "<p>" + self.base_utterance + "</p>"
        )

    def test_amazon_tags(self):
        self.assertEqual(
            SSMLBuilder().say_strong(self.base_utterance).build(),
            "<amazon:effect vocal-tract-length=\"+20%\">" +
            self.base_utterance + "</amazon:effect>"
        )
        self.assertEqual(
            SSMLBuilder().say_weak(self.base_utterance).build(),
            "<amazon:effect vocal-tract-length=\"-20%\">" +
            self.base_utterance + "</amazon:effect>"
        )
        self.assertEqual(
            SSMLBuilder().say_softly(self.base_utterance).build(),
            "<amazon:effect phonation=\"soft\">" +
            self.base_utterance + "</amazon:effect>"
        )
        self.assertEqual(
            SSMLBuilder().say_auto_breaths(self.base_utterance).build(),
            "<amazon:auto-breaths>" +
            self.base_utterance + "</amazon:auto-breaths>"
        )

    def test_value_tags(self):
        self.assertEqual(
            SSMLBuilder().prosody("XXX", self.base_utterance).build(),
            "<prosody XXX>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().pitch("XXX", self.base_utterance).build(),
            "<prosody pitch='XXX'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().volume("XXX", self.base_utterance).build(),
            "<prosody volume='XXX'>" + self.base_utterance + "</prosody>"
        )
        self.assertEqual(
            SSMLBuilder().volume("XXX", self.base_utterance).build(),
            "<prosody volume='XXX'>" + self.base_utterance + "</prosody>"
        )

        self.assertEqual(
            SSMLBuilder().emphasis("strong", self.base_utterance).build(),
            "<emphasis level='strong'>" + self.base_utterance + "</emphasis>"
        )

    def test_pause(self):
        self.assertEqual(
            SSMLBuilder().pause().build(),
            "<break />"
        )
        self.assertEqual(
            SSMLBuilder().pause(120).build(),
            "<break time=120ms/>"
        )
        self.assertEqual(
            SSMLBuilder().pause(120, "ms").build(),
            "<break time=120ms/>"
        )
        self.assertEqual(
            SSMLBuilder().pause(1, "s").build(),
            "<break time=1s/>"
        )
        self.assertEqual(
            SSMLBuilder().pause_by_strength("XXX").build(),
            "<break strength=xxx/>"
        )

    def test_other(self):
        self.assertEqual(
            SSMLBuilder().audio("XXX", self.base_utterance).build(),
            "<audio src=XXX>" + self.base_utterance + "</audio>"
        )
        # TODO parts_of_speech
        # TODO sub
        # TODO phoneme
        # TODO voice

    def test_multiple(self):
        ssml = SSMLBuilder() \
            .say(self.base_utterance).pause().say_fast(self.base_utterance2) \
            .build()
        self.assertEqual(
            ssml,
            "<prosody rate='1'>" + self.base_utterance +
            "</prosody> <break /> <prosody rate='1.6'>" +
            self.base_utterance2 + "</prosody>"
        )

    def test_tag_parsing(self):
        ssml = SSMLBuilder() \
            .say(self.base_utterance).pause().say_fast(self.base_utterance2) \
            .build()
        self.assertEqual(
            SSMLBuilder.remove_ssml(ssml),
            self.base_utterance + " " + self.base_utterance2
        )
        self.assertEqual(
            SSMLBuilder.extract_ssml_tags(ssml),
            ["<prosody rate='1'>", '</prosody>', '<break />',
             "<prosody rate='1.6'>", '</prosody>']
        )