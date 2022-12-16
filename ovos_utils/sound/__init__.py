import os
import subprocess
import time
from copy import deepcopy
from distutils.spawn import find_executable

from ovos_config import Configuration

from ovos_utils.file_utils import resolve_resource_file
from ovos_utils.log import LOG
from ovos_utils.signal import check_for_signal

# Create a custom environment to use that can be ducked by a phone role.
# This is kept separate from the normal os.environ to ensure that the TTS
# role isn't affected and that any thirdparty software launched through
# a mycroft process can select if they wish to honor this.
_ENVIRONMENT = deepcopy(os.environ)
_ENVIRONMENT['PULSE_PROP'] = 'media.role=music'


def _get_pulse_environment(config):
    """Return environment for pulse audio depeding on ducking config."""
    tts_config = config.get('tts', {})
    if tts_config and tts_config.get('pulse_duck'):
        return _ENVIRONMENT
    else:
        return os.environ


def play_acknowledge_sound():
    """Acknowledge a successful request.

    This method plays a sound to acknowledge a request that does not
    require a verbal response. This is intended to provide simple feedback
    to the user that their request was handled successfully.
    """
    audio_file = resolve_resource_file(
        Configuration().get('sounds', {}).get('acknowledge'))

    if not audio_file:
        LOG.warning("Could not find 'acknowledge' audio file!")
        return

    process = play_audio(audio_file)
    if not process:
        LOG.warning("Unable to play 'acknowledge' audio file!")
    return process


def play_listening_sound():
    """Audibly indicate speech recording started."""
    audio_file = resolve_resource_file(
        Configuration().get('sounds', {}).get('start_listening'))

    if not audio_file:
        LOG.warning("Could not find 'start_listening' audio file!")
        return

    process = play_audio(audio_file)
    if not process:
        LOG.warning("Unable to play 'start_listening' audio file!")
    return process


def play_end_listening_sound():
    """Audibly indicate speech recording is no longer happening."""
    audio_file = resolve_resource_file(
        Configuration().get('sounds', {}).get('end_listening'))

    if not audio_file:
        LOG.debug("Could not find 'end_listening' audio file!")
        return

    process = play_audio(audio_file)
    if not process:
        LOG.warning("Unable to play 'end_listening' audio file!")
    return process


def play_error_sound():
    """Audibly indicate a failed request.

    This method plays a error sound to signal an error that does not
    require a verbal response. This is intended to provide simple feedback
    to the user that their request was NOT handled successfully.
    """
    audio_file = resolve_resource_file(
        Configuration().get('sounds', {}).get('error'))

    if not audio_file:
        LOG.warning("Could not find 'error' audio file!")
        return

    process = play_audio(audio_file)
    if not process:
        LOG.warning("Unable to play 'error' audio file!")
    return process


def _find_player(uri):
    _, ext = os.path.splitext(uri)

    # scan installed executables that can handle playback
    sox_play = find_executable("play")
    pulse_play = find_executable("paplay")
    alsa_play = find_executable("aplay")
    mpg123_play = find_executable("mpg123")
    ogg123_play = find_executable("ogg123")

    player = None
    # sox should handle almost every format, but fails in some urls
    if sox_play:
        player = sox_play + f" --type {ext} %1"
    # determine best available player
    else:
        if "ogg" in ext and ogg123_play:
            player = ogg123_play + " -q %1"
        # wav file
        if 'wav' in ext:
            if pulse_play:
                player = pulse_play + " %1"
            elif alsa_play:
                player = alsa_play + " %1"
        # guess mp3
        elif mpg123_play:
            player = mpg123_play + " %1"
    return player


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
    config = Configuration()
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


def play_wav(uri, play_cmd=None, environment=None):
    """ Play a wav-file.

        Returns: subprocess.Popen object
    """
    config = Configuration()
    environment = environment or _get_pulse_environment(config)
    play_cmd = play_cmd or config.get("play_wav_cmdline") or "paplay %1"
    play_wav_cmd = str(play_cmd).split(" ")
    for index, cmd in enumerate(play_wav_cmd):
        if cmd == "%1":
            play_wav_cmd[index] = uri
    try:
        return subprocess.Popen(play_wav_cmd, env=environment)
    except Exception as e:
        LOG.error("Failed to launch WAV: {}".format(play_wav_cmd))
        LOG.debug("Error: {}".format(repr(e)), exc_info=True)
        return None


def play_mp3(uri, play_cmd=None, environment=None):
    """ Play a mp3-file.

        Returns: subprocess.Popen object
    """
    config = Configuration()
    environment = environment or _get_pulse_environment(config)
    play_cmd = play_cmd or config.get("play_mp3_cmdline") or "mpg123 %1"
    play_mp3_cmd = str(play_cmd).split(" ")
    for index, cmd in enumerate(play_mp3_cmd):
        if cmd == "%1":
            play_mp3_cmd[index] = uri
    try:
        return subprocess.Popen(play_mp3_cmd, env=environment)
    except Exception as e:
        LOG.error("Failed to launch MP3: {}".format(play_mp3_cmd))
        LOG.debug("Error: {}".format(repr(e)), exc_info=True)
        return None


def play_ogg(uri, play_cmd=None, environment=None):
    """ Play a ogg-file.

        Returns: subprocess.Popen object
    """
    config = Configuration()
    environment = environment or _get_pulse_environment(config)
    play_cmd = play_cmd or config.get("play_ogg_cmdline") or "ogg123 -q %1"
    play_ogg_cmd = str(play_cmd).split(" ")
    for index, cmd in enumerate(play_ogg_cmd):
        if cmd == "%1":
            play_ogg_cmd[index] = uri
    try:
        return subprocess.Popen(play_ogg_cmd, env=environment)
    except Exception as e:
        LOG.error("Failed to launch OGG: {}".format(play_ogg_cmd))
        LOG.debug("Error: {}".format(repr(e)), exc_info=True)
        return None


def record(file_path, duration, rate, channels):
    """Simple function to record from the default mic.

    The recording is done in the background by the arecord commandline
    application.

    Args:
        file_path: where to store the recorded data
        duration: how long to record
        rate: sample rate
        channels: number of channels

    Returns:
        process for performing the recording.
    """
    command = ['arecord', '-r', str(rate), '-c', str(channels)]
    command += ['-d', str(duration)] if duration > 0 else []
    command += [file_path]
    return subprocess.Popen(command)


def is_speaking():
    """Determine if Text to Speech is occurring

    Returns:
        bool: True while still speaking
    """
    return check_for_signal("isSpeaking", -1)


def wait_while_speaking():
    """Pause as long as Text to Speech is still happening

    Pause while Text to Speech is still happening.  This always pauses
    briefly to ensure that any preceeding request to speak has time to
    begin.
    """
    time.sleep(0.3)  # Wait briefly in for any queued speech to begin
    while is_speaking():
        time.sleep(0.1)
