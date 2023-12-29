import os
import subprocess
from copy import deepcopy
from distutils.spawn import find_executable

from ovos_utils.log import LOG

try:
    from ovos_config.config import read_mycroft_config
except ImportError:
    LOG.warning("Config not provided and ovos_config not available")


    def read_mycroft_config():
        return dict()

# Create a custom environment to use that can let duck a music role.
# This is kept separate from the normal os.environ to ensure that
# any thirdparty software launched through
# a ovos process can select if they wish to honor this.
_ENVIRONMENT = deepcopy(os.environ)
_ENVIRONMENT['PULSE_PROP'] = 'media.role=phone'


def _get_pulse_environment(config):
    """Return environment for pulse audio depeding on ducking config."""
    tts_config = config.get('tts', {})
    if tts_config and tts_config.get('pulse_duck'):
        return _ENVIRONMENT
    else:
        return os.environ


def _find_player(uri):
    _, ext = os.path.splitext(uri)

    # scan installed executables that can handle playback
    sox_play = find_executable("play")
    # sox should handle almost every format, but fails in some urls
    if sox_play:
        return sox_play + f" --type {ext} %1"
    # determine best available player
    ogg123_play = find_executable("ogg123")
    if "ogg" in ext and ogg123_play:
        return ogg123_play + " -q %1"
    pw_play = find_executable("pw-play")
    # pw_play handles both wav and mp3
    if pw_play:
        return pw_play + " %1"
    # wav file
    if 'wav' in ext:
        pulse_play = find_executable("paplay")
        if pulse_play:
            return pulse_play + " %1"
        alsa_play = find_executable("aplay")
        if alsa_play:
            return alsa_play + " %1"
    # guess mp3
    mpg123_play = find_executable("mpg123")
    if mpg123_play:
        return mpg123_play + " %1"
    LOG.error("Can't find player for: %s", uri)
    return None


def play_audio(uri, play_cmd=None, environment=None):
    """Play an audio file.

    This wraps the other play_* functions, choosing the correct one based on
    the file extension. The function will return directly and play the file
    in the background.

    Args:
        uri:    uri to play
        environment (dict): optional environment for the subprocess call

    Returns: subprocess.Popen object. None if the format is not supported or
             an error occurs playing the file.
    """
    config = read_mycroft_config()
    environment = environment or _get_pulse_environment(config)

    # NOTE: some urls like youtube streams will cause extension detection to fail
    # let's handle it explicitly
    uri = uri.split("?")[0]
    # Replace file:// uri's with normal paths
    uri = uri.replace('file://', '')

    _, ext = os.path.splitext(uri)

    if not play_cmd:
        if "ogg" in ext:
            play_cmd = config.get("play_ogg_cmdline")
        elif "wav" in ext:
            play_cmd = config.get("play_wav_cmdline")
        elif "mp3" in ext:
            play_cmd = config.get("play_mp3_cmdline")

    if not play_cmd:
        play_cmd = _find_player(uri)

    if not play_cmd:
        LOG.error(f"Failed to play: No playback functionality available")
        return None

    play_cmd = play_cmd.split(" ")

    for index, cmd in enumerate(play_cmd):
        if cmd == "%1":
            play_cmd[index] = uri

    try:
        return subprocess.Popen(play_cmd, env=environment)
    except Exception as e:
        LOG.error(f"Failed to play: {play_cmd}")
        LOG.exception(e)
        return None
