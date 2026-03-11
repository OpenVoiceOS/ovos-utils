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

"""Unit tests for ovos_utils.sound module."""

import os
import sys
import tempfile
import types
import unittest
import wave
from unittest.mock import MagicMock, patch, mock_open

# distutils was removed in Python 3.12+; provide a minimal stub so sound.py can import
if "distutils" not in sys.modules:
    distutils_stub = types.ModuleType("distutils")
    spawn_stub = types.ModuleType("distutils.spawn")
    spawn_stub.find_executable = lambda x: None
    distutils_stub.spawn = spawn_stub
    sys.modules["distutils"] = distutils_stub
    sys.modules["distutils.spawn"] = spawn_stub


class TestGetPulseEnvironment(unittest.TestCase):
    """Tests for _get_pulse_environment helper."""

    def test_pulse_duck_enabled(self) -> None:
        """Should return _ENVIRONMENT when pulse_duck is True in tts config."""
        from ovos_utils.sound import _get_pulse_environment, _ENVIRONMENT
        config = {"tts": {"pulse_duck": True}}
        result = _get_pulse_environment(config)
        self.assertIs(result, _ENVIRONMENT)

    def test_pulse_duck_disabled(self) -> None:
        """Should return os.environ when pulse_duck is False."""
        import os
        from ovos_utils.sound import _get_pulse_environment
        config = {"tts": {"pulse_duck": False}}
        result = _get_pulse_environment(config)
        self.assertIs(result, os.environ)

    def test_no_tts_config(self) -> None:
        """Should return os.environ when tts config is absent."""
        import os
        from ovos_utils.sound import _get_pulse_environment
        config = {}
        result = _get_pulse_environment(config)
        self.assertIs(result, os.environ)


class TestFindPlayer(unittest.TestCase):
    """Tests for _find_player helper."""

    @patch("ovos_utils.sound.find_executable")
    def test_sox_play_found(self, mock_find: MagicMock) -> None:
        """Should prefer sox play when available."""
        mock_find.side_effect = lambda x: "/usr/bin/play" if x == "play" else None
        from ovos_utils.sound import _find_player
        result = _find_player("test.mp3")
        self.assertIsNotNone(result)
        self.assertIn("play", result)

    @patch("ovos_utils.sound.find_executable")
    def test_ogg_player_preferred_for_ogg(self, mock_find: MagicMock) -> None:
        """Should prefer ogg123 for .ogg files when sox is unavailable."""
        def side_effect(x: str) -> str | None:
            if x == "play":
                return None
            if x == "ogg123":
                return "/usr/bin/ogg123"
            return None
        mock_find.side_effect = side_effect
        from ovos_utils.sound import _find_player
        result = _find_player("test.ogg")
        self.assertIsNotNone(result)
        self.assertIn("ogg123", result)

    @patch("ovos_utils.sound.find_executable")
    def test_pw_play_fallback(self, mock_find: MagicMock) -> None:
        """Should use pw-play when sox is unavailable and file is not ogg."""
        def side_effect(x: str) -> str | None:
            if x == "pw-play":
                return "/usr/bin/pw-play"
            return None
        mock_find.side_effect = side_effect
        from ovos_utils.sound import _find_player
        result = _find_player("test.mp3")
        self.assertIsNotNone(result)
        self.assertIn("pw-play", result)

    @patch("ovos_utils.sound.find_executable")
    def test_paplay_for_wav(self, mock_find: MagicMock) -> None:
        """Should use paplay for .wav when pw-play and sox unavailable."""
        def side_effect(x: str) -> str | None:
            if x == "paplay":
                return "/usr/bin/paplay"
            return None
        mock_find.side_effect = side_effect
        from ovos_utils.sound import _find_player
        result = _find_player("test.wav")
        self.assertIsNotNone(result)
        self.assertIn("paplay", result)

    @patch("ovos_utils.sound.find_executable")
    def test_aplay_for_wav_when_paplay_missing(self, mock_find: MagicMock) -> None:
        """Should fall back to aplay for .wav when paplay is unavailable."""
        def side_effect(x: str) -> str | None:
            if x == "aplay":
                return "/usr/bin/aplay"
            return None
        mock_find.side_effect = side_effect
        from ovos_utils.sound import _find_player
        result = _find_player("test.wav")
        self.assertIsNotNone(result)
        self.assertIn("aplay", result)

    @patch("ovos_utils.sound.find_executable")
    def test_mpg123_for_mp3(self, mock_find: MagicMock) -> None:
        """Should use mpg123 for mp3 when no other player found."""
        def side_effect(x: str) -> str | None:
            if x == "mpg123":
                return "/usr/bin/mpg123"
            return None
        mock_find.side_effect = side_effect
        from ovos_utils.sound import _find_player
        result = _find_player("test.mp3")
        self.assertIsNotNone(result)
        self.assertIn("mpg123", result)

    @patch("ovos_utils.sound.find_executable", return_value=None)
    def test_returns_none_when_no_player(self, _mock_find: MagicMock) -> None:
        """Should return None when no suitable player is found."""
        from ovos_utils.sound import _find_player
        result = _find_player("test.xyz")
        self.assertIsNone(result)


class TestPlayAudio(unittest.TestCase):
    """Tests for play_audio function."""

    @patch("ovos_utils.sound.read_mycroft_config", return_value={})
    @patch("ovos_utils.sound._find_player", return_value="/usr/bin/play --type mp3 %1")
    @patch("subprocess.Popen")
    def test_play_audio_basic(self, mock_popen: MagicMock,
                               mock_finder: MagicMock,
                               mock_config: MagicMock) -> None:
        """play_audio should call Popen with the resolved command."""
        mock_popen.return_value = MagicMock()
        from ovos_utils.sound import play_audio
        result = play_audio("test.mp3")
        self.assertIsNotNone(result)
        mock_popen.assert_called_once()

    @patch("ovos_utils.sound.read_mycroft_config", return_value={})
    @patch("ovos_utils.sound._find_player", return_value=None)
    def test_play_audio_no_player(self, mock_finder: MagicMock,
                                   mock_config: MagicMock) -> None:
        """play_audio should return None when no player is found."""
        from ovos_utils.sound import play_audio
        result = play_audio("test.mp3")
        self.assertIsNone(result)

    @patch("ovos_utils.sound.read_mycroft_config",
           return_value={"play_ogg_cmdline": "ogg123 %1"})
    @patch("subprocess.Popen")
    def test_play_audio_uses_config_ogg_cmd(self, mock_popen: MagicMock,
                                             mock_config: MagicMock) -> None:
        """play_audio should use configured ogg command for .ogg files."""
        mock_popen.return_value = MagicMock()
        from ovos_utils.sound import play_audio
        result = play_audio("file:///path/to/test.ogg")
        self.assertIsNotNone(result)
        cmd_args = mock_popen.call_args[0][0]
        self.assertIn("ogg123", cmd_args)

    @patch("ovos_utils.sound.read_mycroft_config",
           return_value={"play_wav_cmdline": "aplay %1"})
    @patch("subprocess.Popen")
    def test_play_audio_uses_config_wav_cmd(self, mock_popen: MagicMock,
                                             mock_config: MagicMock) -> None:
        """play_audio should use configured wav command for .wav files."""
        mock_popen.return_value = MagicMock()
        from ovos_utils.sound import play_audio
        result = play_audio("test.wav")
        self.assertIsNotNone(result)

    @patch("ovos_utils.sound.read_mycroft_config",
           return_value={"play_mp3_cmdline": "mpg123 %1"})
    @patch("subprocess.Popen")
    def test_play_audio_uses_config_mp3_cmd(self, mock_popen: MagicMock,
                                             mock_config: MagicMock) -> None:
        """play_audio should use configured mp3 command for .mp3 files."""
        mock_popen.return_value = MagicMock()
        from ovos_utils.sound import play_audio
        result = play_audio("song.mp3")
        self.assertIsNotNone(result)

    @patch("ovos_utils.sound.read_mycroft_config", return_value={})
    @patch("ovos_utils.sound._find_player", return_value="broken %1")
    @patch("subprocess.Popen", side_effect=OSError("no such file"))
    def test_play_audio_popen_exception(self, mock_popen: MagicMock,
                                        mock_finder: MagicMock,
                                        mock_config: MagicMock) -> None:
        """play_audio should return None when Popen raises an exception."""
        from ovos_utils.sound import play_audio
        result = play_audio("test.mp3")
        self.assertIsNone(result)

    @patch("ovos_utils.sound.read_mycroft_config", return_value={})
    @patch("ovos_utils.sound._find_player", return_value="player %1")
    @patch("subprocess.Popen")
    def test_play_audio_strips_query_string(self, mock_popen: MagicMock,
                                             mock_finder: MagicMock,
                                             mock_config: MagicMock) -> None:
        """play_audio should strip query strings from URIs before processing."""
        mock_popen.return_value = MagicMock()
        from ovos_utils.sound import play_audio
        play_audio("http://example.com/stream?quality=high")
        cmd_args = mock_popen.call_args[0][0]
        # URI with no extension; query stripped
        self.assertNotIn("?", " ".join(cmd_args))

    @patch("ovos_utils.sound.read_mycroft_config", return_value={})
    @patch("ovos_utils.sound._find_player", return_value="player %1")
    @patch("subprocess.Popen")
    def test_play_audio_custom_play_cmd(self, mock_popen: MagicMock,
                                        mock_finder: MagicMock,
                                        mock_config: MagicMock) -> None:
        """play_audio should use a caller-provided play_cmd if given."""
        mock_popen.return_value = MagicMock()
        from ovos_utils.sound import play_audio
        result = play_audio("test.wav", play_cmd="custom_player %1")
        self.assertIsNotNone(result)
        cmd_args = mock_popen.call_args[0][0]
        self.assertIn("custom_player", cmd_args)


class TestGetSoundDuration(unittest.TestCase):
    """Tests for get_sound_duration function."""

    def test_wav_file_duration(self) -> None:
        """get_sound_duration should return duration for a valid .wav file."""
        # Create a minimal valid wave file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            fname = f.name
        try:
            with wave.open(fname, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00" * 32000)  # 1 second of silence
            from ovos_utils.sound import get_sound_duration
            duration = get_sound_duration(fname)
            self.assertAlmostEqual(duration, 1.0, places=1)
        finally:
            os.unlink(fname)

    def test_file_not_found(self) -> None:
        """get_sound_duration should raise FileNotFoundError for missing files."""
        from ovos_utils.sound import get_sound_duration
        with self.assertRaises(FileNotFoundError):
            get_sound_duration("/nonexistent/path/audio.wav")

    def test_snd_prefix_resolved(self) -> None:
        """get_sound_duration should resolve snd/-prefixed paths using base_dir."""
        with tempfile.TemporaryDirectory() as base_dir:
            snd_dir = os.path.join(base_dir, "snd")
            os.makedirs(snd_dir)
            wav_path = os.path.join(snd_dir, "test.wav")
            with wave.open(wav_path, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(8000)
                wf.writeframes(b"\x00" * 8000)
            from ovos_utils.sound import get_sound_duration
            duration = get_sound_duration("snd/test.wav", base_dir=base_dir)
            self.assertGreater(duration, 0)

    @patch("ovos_utils.sound.find_executable")
    @patch("subprocess.Popen")
    def test_ffprobe_fallback(self, mock_popen: MagicMock,
                               mock_find: MagicMock) -> None:
        """get_sound_duration should use ffprobe for non-wav files when available."""
        # Create a temp file with non-wav extension
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"\x00" * 100)
            fname = f.name
        try:
            def find_side_effect(x: str) -> str | None:
                return "/usr/bin/ffprobe" if x == "ffprobe" else None
            mock_find.side_effect = find_side_effect

            mock_proc = MagicMock()
            mock_proc.stdout.read.return_value = b"[FORMAT]\nduration=3.5\n[/FORMAT]\n"
            mock_popen.return_value = mock_proc

            from ovos_utils.sound import get_sound_duration
            duration = get_sound_duration(fname)
            self.assertAlmostEqual(duration, 3.5, places=1)
        finally:
            os.unlink(fname)

    @patch("ovos_utils.sound.find_executable")
    @patch("subprocess.Popen")
    def test_mediainfo_fallback(self, mock_popen: MagicMock,
                                 mock_find: MagicMock) -> None:
        """get_sound_duration should use mediainfo when ffprobe is unavailable."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"\x00" * 100)
            fname = f.name
        try:
            def find_side_effect(x: str) -> str | None:
                return "/usr/bin/mediainfo" if x == "mediainfo" else None
            mock_find.side_effect = find_side_effect

            mock_proc = MagicMock()
            # Simulate mediainfo output with "Duration" field
            mock_proc.stdout.read.return_value = (
                b"General\nDuration: 2 s 500 ms\n"
            )
            mock_popen.return_value = mock_proc

            from ovos_utils.sound import get_sound_duration
            duration = get_sound_duration(fname)
            self.assertGreaterEqual(duration, 0)
        finally:
            os.unlink(fname)

    @patch("ovos_utils.sound.find_executable", return_value=None)
    def test_no_tool_raises_runtime_error(self, _mock_find: MagicMock) -> None:
        """get_sound_duration should raise RuntimeError when no tool is available."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"\x00" * 100)
            fname = f.name
        try:
            from ovos_utils.sound import get_sound_duration
            with self.assertRaises(RuntimeError):
                get_sound_duration(fname)
        finally:
            os.unlink(fname)


if __name__ == "__main__":
    unittest.main()
