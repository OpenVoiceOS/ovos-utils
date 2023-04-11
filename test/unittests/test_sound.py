import unittest
from time import sleep


class TestSound(unittest.TestCase):
    # TODO: Some tests already implemented in `test_sound`
    def test_get_pulse_environment(self):
        from ovos_utils.sound import _get_pulse_environment
        # TODO

    def test_play_acknowledge_sound(self):
        from ovos_utils.sound import play_acknowledge_sound
        # TODO

    def test_play_listening_sound(self):
        from ovos_utils.sound import play_listening_sound
        # TODO

    def test_play_end_listening_sound(self):
        from ovos_utils.sound import play_end_listening_sound
        # TODO

    def test_play_error_sound(self):
        from ovos_utils.sound import play_error_sound
        # TODO

    def test_find_player(self):
        from ovos_utils.sound import _find_player
        # TODO

    def test_play_audio(self):
        from ovos_utils.sound import play_audio
        # TODO

    def test_play_wav(self):
        from ovos_utils.sound import play_wav
        # TODO

    def test_play_mp3(self):
        from ovos_utils.sound import play_wav
        # TODO

    def test_play_ogg(self):
        from ovos_utils.sound import play_ogg
        # TODO

    def test_record(self):
        from ovos_utils.sound import record
        # TODO

    def test_is_speaking(self):
        from ovos_utils.sound import is_speaking
        # TODO

    def test_wait_while_speaking(self):
        from ovos_utils.sound import wait_while_speaking
        # TODO


@unittest.skip("Skip ALSA tests")
class TestAlsaControl(unittest.TestCase):
    try:
        from ovos_utils.sound.alsa import AlsaControl
        controller = AlsaControl()
    except:
        pass

    def test_set_get_volume(self):
        self.controller.set_volume(100)
        sleep(2)
        self.assertFalse(self.controller.is_muted())
        self.assertEqual(self.controller.get_volume(), 100)

    def test_mute_unmute(self):
        self.controller.mute()
        sleep(2)
        self.assertTrue(self.controller.is_muted())
        self.controller.unmute()
        sleep(2)
        self.assertFalse(self.controller.is_muted())

    # TODO: Test other methods


@unittest.skip("Skip Pulse Audio tests")
class TestPulseAudio(unittest.TestCase):
    try:
        from ovos_utils.sound.pulse import PulseAudio
        controller = PulseAudio()
    except:
        pass

    def test_list_sources(self):
        self.assertIsInstance(self.controller.list_sources(), list)

    # TODO: Test other methods
