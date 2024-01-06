from enum import IntEnum

OCP_ID = "ovos.common_play"


class MatchConfidence(IntEnum):
    EXACT = 95
    VERY_HIGH = 90
    HIGH = 80
    AVERAGE_HIGH = 70
    AVERAGE = 50
    AVERAGE_LOW = 30
    LOW = 15
    VERY_LOW = 1


class TrackState(IntEnum):
    DISAMBIGUATION = 1  # media result, not queued for playback

    PLAYING_SKILL = 20  # Skill is handling playback internally
    PLAYING_AUDIO = 21  # Skill forwarded playback to audio service
    PLAYING_VIDEO = 22  # Skill forwarded playback to video service
    PLAYING_MPRIS = 24  # External media player is handling playback
    PLAYING_WEBVIEW = 25  # Media playback handled in browser (eg. javascript)

    QUEUED_SKILL = 30  # Waiting playback to be handled inside skill
    QUEUED_AUDIO = 31  # Waiting playback in audio service
    QUEUED_VIDEO = 32  # Waiting playback in video service
    QUEUED_WEBVIEW = 34  # Waiting playback in browser service


class MediaState(IntEnum):
    # https://doc.qt.io/qt-5/qmediaplayer.html#MediaStatus-enum
    # The status of the media cannot be determined.
    UNKNOWN = 0
    # There is no current media. PlayerState == STOPPED
    NO_MEDIA = 1
    # The current media is being loaded. The player may be in any state.
    LOADING_MEDIA = 2
    # The current media has been loaded. PlayerState== STOPPED
    LOADED_MEDIA = 3
    # Playback of the current media has stalled due to
    # insufficient buffering or some other temporary interruption.
    # PlayerState != STOPPED
    STALLED_MEDIA = 4
    # The player is buffering data but has enough data buffered
    # for playback to continue for the immediate future.
    # PlayerState != STOPPED
    BUFFERING_MEDIA = 5
    # The player has fully buffered the current media. PlayerState != STOPPED
    BUFFERED_MEDIA = 6
    # Playback has reached the end of the current media. PlayerState == STOPPED
    END_OF_MEDIA = 7
    # The current media cannot be played. PlayerState == STOPPED
    INVALID_MEDIA = 8


class PlayerState(IntEnum):
    # https://doc.qt.io/qt-5/qmediaplayer.html#State-enum
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class LoopState(IntEnum):
    NONE = 0
    REPEAT = 1
    REPEAT_TRACK = 2


class PlaybackType(IntEnum):
    SKILL = 0  # skills handle playback whatever way they see fit,
    # eg spotify / mycroft common play
    VIDEO = 1  # Video results
    AUDIO = 2  # Results should be played audio only
    MPRIS = 4  # External MPRIS compliant player
    WEBVIEW = 5  # webview, render a url instead of media player
    UNDEFINED = 100  # data not available, hopefully status will be updated soon..


class PlaybackMode(IntEnum):
    AUTO = 0  # play each entry as considered appropriate,
    # ie, make it happen the best way possible
    AUDIO_ONLY = 10  # only consider audio entries
    VIDEO_ONLY = 20  # only consider video entries
    FORCE_AUDIO = 30  # cast video to audio unconditionally
    EVENTS_ONLY = 50  # only emit ocp events, do not display or play anything.
    # allows integration with external interfaces


class MediaType(IntEnum):
    GENERIC = 0  # nothing else matches
    AUDIO = 1  # things like ambient noises
    MUSIC = 2
    VIDEO = 3  # eg, youtube videos
    AUDIOBOOK = 4
    GAME = 5  # because it shares the verb "play", mostly for disambguation
    PODCAST = 6
    RADIO = 7  # live radio
    NEWS = 8  # news reports
    TV = 9  # live tv stream
    MOVIE = 10
    TRAILER = 11
    AUDIO_DESCRIPTION = 12  # narrated movie for the blind
    VISUAL_STORY = 13  # things like animated comic books
    BEHIND_THE_SCENES = 14
    DOCUMENTARY = 15
    RADIO_THEATRE = 16
    SHORT_FILM = 17  # typically movies under 45 min
    SILENT_MOVIE = 18
    VIDEO_EPISODES = 19  # tv series etc
    BLACK_WHITE_MOVIE = 20
    CARTOON = 21
    ANIME = 22
    ASMR = 23

    ADULT = 69  # for content filtering
    HENTAI = 70  # for content filtering
    ADULT_AUDIO = 71  # for content filtering


def available_extractors():
    from ovos_plugin_common_play.ocp.utils import available_extractors as _real
    return _real()  # TODO
