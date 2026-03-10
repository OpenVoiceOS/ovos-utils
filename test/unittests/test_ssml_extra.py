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

from ovos_utils.ssml import SSMLBuilder


class TestSSMLBuilderExtra(unittest.TestCase):
    """Additional SSMLBuilder tests covering uncovered methods."""

    TEXT = "hello world"

    def test_sub(self) -> None:
        result = SSMLBuilder().sub(alias="World", word="W").build()
        self.assertIn("<sub", result)
        self.assertIn("alias='World'", result)

    def test_sub_none_alias_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().sub(word="W")

    def test_sub_none_word_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().sub(alias="A")

    def test_sub_empty_word_raises(self) -> None:
        with self.assertRaises(ValueError):
            SSMLBuilder().sub(alias="A", word="  ")

    def test_emphasis(self) -> None:
        result = SSMLBuilder().emphasis(level="moderate", word=self.TEXT).build()
        self.assertIn("<emphasis level='moderate'>", result)

    def test_emphasis_none_level_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().emphasis(word=self.TEXT)

    def test_emphasis_none_word_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().emphasis(level="moderate")

    def test_emphasis_empty_word_raises(self) -> None:
        with self.assertRaises(ValueError):
            SSMLBuilder().emphasis(level="moderate", word="  ")

    def test_parts_of_speech(self) -> None:
        result = SSMLBuilder().parts_of_speech(word="bass", role="amazon:VB").build()
        self.assertIn("<w role='amazon:VB'>bass</w>", result)

    def test_parts_of_speech_none_word_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().parts_of_speech(role="amazon:VB")

    def test_parts_of_speech_none_role_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().parts_of_speech(word="bass")

    def test_pause_by_strength(self) -> None:
        result = SSMLBuilder().pause_by_strength(strength="Medium").build()
        self.assertIn("<break strength=medium/>", result)

    def test_pause_by_strength_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().pause_by_strength()

    def test_pause_by_strength_non_string_raises(self) -> None:
        with self.assertRaises(AttributeError):
            SSMLBuilder().pause_by_strength(strength=42)

    def test_audio(self) -> None:
        result = SSMLBuilder().audio(audio_file="sound.mp3", text=self.TEXT).build()
        self.assertIn("<audio src=sound.mp3>", result)
        self.assertIn(self.TEXT, result)

    def test_audio_none_file_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().audio(text=self.TEXT)

    def test_audio_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().audio(audio_file="f.mp3")

    def test_pause_with_time(self) -> None:
        result = SSMLBuilder().pause(time=500, unit="ms").build()
        self.assertIn("<break time=500ms/>", result)

    def test_pause_zero(self) -> None:
        result = SSMLBuilder().pause().build()
        self.assertIn("<break />", result)

    def test_pause_invalid_unit_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().pause(time=1, unit="min")

    def test_pause_seconds(self) -> None:
        result = SSMLBuilder().pause(time=2, unit="s").build()
        self.assertIn("<break time=2s/>", result)

    def test_prosody(self) -> None:
        result = SSMLBuilder().prosody(attribute="rate='slow'", text=self.TEXT).build()
        self.assertIn("<prosody rate='slow'>", result)

    def test_prosody_none_attribute_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().prosody(text=self.TEXT)

    def test_prosody_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().prosody(attribute="x='y'")

    def test_pitch(self) -> None:
        result = SSMLBuilder().pitch(pitch="+20%", text=self.TEXT).build()
        self.assertIn("<prosody pitch='+20%'>", result)

    def test_pitch_none_pitch_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().pitch(text=self.TEXT)

    def test_pitch_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().pitch(pitch="+20%")

    def test_volume(self) -> None:
        result = SSMLBuilder().volume(volume="loud", text=self.TEXT).build()
        self.assertIn("<prosody volume='loud'>", result)

    def test_volume_none_volume_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().volume(text=self.TEXT)

    def test_volume_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().volume(volume="loud")

    def test_rate(self) -> None:
        result = SSMLBuilder().rate(rate="fast", text=self.TEXT).build()
        self.assertIn("<prosody rate='fast'>", result)

    def test_rate_none_rate_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().rate(text=self.TEXT)

    def test_rate_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().rate(rate="fast")

    def test_phoneme(self) -> None:
        result = SSMLBuilder().phoneme(ph="t EH s t", text=self.TEXT).build()
        self.assertIn("<phoneme ph=t EH s t>", result)

    def test_phoneme_none_ph_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().phoneme(text=self.TEXT)

    def test_phoneme_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().phoneme(ph="t EH s t")

    def test_voice(self) -> None:
        result = SSMLBuilder().voice(voice="Joanna", text=self.TEXT).build()
        self.assertIn("<voice name=Joanna>", result)

    def test_voice_none_voice_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().voice(text=self.TEXT)

    def test_voice_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().voice(voice="Joanna")

    def test_whisper(self) -> None:
        result = SSMLBuilder().whisper(text=self.TEXT).build()
        self.assertIn("<whispered>", result)

    def test_whisper_none_text_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().whisper()

    def test_remove_ssml(self) -> None:
        text = "<speak>hello <prosody rate='fast'>world</prosody></speak>"
        result = SSMLBuilder.remove_ssml(text)
        self.assertNotIn("<", result)
        self.assertIn("hello", result)
        self.assertIn("world", result)

    def test_extract_ssml_tags(self) -> None:
        text = "<speak>hello <b>world</b></speak>"
        tags = SSMLBuilder.extract_ssml_tags(text)
        self.assertIn("<speak>", tags)
        self.assertIn("<b>", tags)
        self.assertIn("</b>", tags)

    def test_chaining_produces_space_separator(self) -> None:
        result = SSMLBuilder().sentence("first").sentence("second").build()
        self.assertIn("<s>first</s>", result)
        self.assertIn("<s>second</s>", result)

    def test_say_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say(None)

    def test_say_loud_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_loud(None)

    def test_say_slow_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_slow(None)

    def test_say_fast_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_fast(None)

    def test_say_low_pitch_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_low_pitch(None)

    def test_say_high_pitch_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_high_pitch(None)

    def test_say_strong_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_strong(None)

    def test_say_weak_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_weak(None)

    def test_say_softly_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_softly(None)

    def test_say_auto_breaths_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_auto_breaths(None)

    def test_sentence_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().sentence(None)

    def test_paragraph_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().paragraph(None)

    def test_say_whispered_none_raises(self) -> None:
        with self.assertRaises(TypeError):
            SSMLBuilder().say_whispered(None)


if __name__ == "__main__":
    unittest.main()
