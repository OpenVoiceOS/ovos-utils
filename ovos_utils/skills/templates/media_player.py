from ovos_utils.waiting_for_mycroft.common_play import CommonPlaySkill, \
    CPSMatchLevel, CPSTrackStatus, CPSMatchType
from ovos_utils import create_daemon
from os.path import join, dirname, basename
from ovos_utils import get_mycroft_root, resolve_ovos_resource_file
from ovos_utils.log import LOG
import random

try:
    from mycroft.skills.core import intent_file_handler
except ImportError:
    import sys

    MYCROFT_ROOT_PATH = get_mycroft_root()
    if MYCROFT_ROOT_PATH is not None:
        sys.path.append(MYCROFT_ROOT_PATH)
        from mycroft.skills.core import intent_file_handler
    else:
        LOG.error("Could not find mycroft root path")
        raise ImportError

try:
    import pyvod
except ImportError:
    pyvod = None


class MediaSkill(CommonPlaySkill):
    """
    common play skills can be made by just returning the
    expected data in CPS_match_query_phrase

       return (phrase, match,
                {"image": self.default_image, # optional
                 "background": self.default_bg, # optional
                 "stream": random.choice(self.bootstrap_list)})

    depending on skill settings
    - will handle bootstrapping media (download on startup)
        - set self.bootstrap_list to a list of urls in __init__
    - will handle audio only VS video
    - will handle conversion to mp3 (compatibility with simple audio backend)

    CPS_start should not be overrided
    - supports direct urls
    - supports youtube urls
    - supports every website youtube-dl supports
    - will handle setting initial track status
    - will fallback to audio only if GUI not connected
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "download_audio" not in self.settings:
            self.settings["download_audio"] = False
        if "download_video" not in self.settings:
            self.settings["download_video"] = False
        if "audio_only" not in self.settings:
            self.settings["audio_only"] = False
        if "audio_with_video_stream" not in self.settings:
            self.settings["audio_with_video_stream"] = False
        if "mp3_audio" not in self.settings:
            self.settings["mp3_audio"] = True
        if "preferred_audio_backend" not in self.settings:
            self.settings["preferred_audio_backend"] = None
        self.message_namespace = basename(dirname(__file__)) + ".ovos_utils"
        self.default_bg = "https://github.com/OpenVoiceOS/ovos_assets/raw/master/Logo/ovos-logo-512.png"
        self.default_image = resolve_ovos_resource_file(
            "ui/images/moviesandfilms.png")
        self.bootstrap_list = []
        if pyvod is None:
            LOG.error("py_VOD not installed!")
            LOG.info("pip install py_VOD>=0.4.0")
            raise ImportError

    def initialize(self):
        self.add_event(
            '{msg_base}.home'.format(msg_base=self.message_namespace),
            self.handle_homescreen)
        create_daemon(self.handle_bootstrap)

    def handle_bootstrap(self):
        # bootstrap, so data is cached
        for url in self.bootstrap_list:
            try:
                if self.settings["download_audio"]:
                    pyvod.utils.get_audio_stream(url, download=True,
                                                 to_mp3=self.settings[
                                                     "mp3_audio"])
                if self.settings["download_video"]:
                    pyvod.utils.get_video_stream(url, download=True)
            except:
                pass

    # homescreen
    def handle_homescreen(self, message):
        # users are supposed to override this
        self.CPS_start(self.name,
                       {"image": self.default_image,
                        "background": self.default_bg,
                        "stream": random.choice(self.bootstrap_list)})

    def CPS_match_query_phrase(self, phrase, media_type):
        # users are supposed to override this
        original = phrase
        match = None

        if match is not None:
            return (phrase, match,
                    {"media_type": media_type, "query": original,
                     "image": self.default_image,
                     "background": self.default_bg,
                     "stream": random.choice(self.bootstrap_list)})
        return None

    def CPS_start(self, phrase, data):
        self.play_media(data)

    def play_media(self, data):
        bg = data.get("background") or self.default_bg
        image = data.get("image") or self.default_image
        url = data["stream"]
        if self.gui.connected and not self.settings["audio_only"]:
            url = pyvod.utils.get_video_stream(
                url, download=self.settings["download_video"])
            self.CPS_send_status(uri=url,
                                 image=image,
                                 background_image=bg,
                                 playlist_position=0,
                                 status=CPSTrackStatus.PLAYING_GUI)
            self.gui.play_video(url, self.name)
        else:
            utt = self.settings["preferred_audio_backend"] or self.play_service_string
            if self.settings["audio_with_video_stream"]:
                # This might look stupid, but for youtube live streams it's
                # needed, mycroft-core/pull/2791 should also be in for this
                # to work properly
                url = pyvod.utils.get_video_stream(url)
            else:
                url = pyvod.utils.get_audio_stream(
                    url, download=self.settings["download_audio"],
                    to_mp3=self.settings["mp3_audio"])
            self.audioservice.play(url, utterance=utt)
            self.CPS_send_status(uri=url,
                                 image=image,
                                 background_image=bg,
                                 playlist_position=0,
                                 status=CPSTrackStatus.PLAYING_AUDIOSERVICE)

    def stop(self):
        self.gui.release()
