import mimetypes
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Tuple, List, Union

import orjson

from ovos_utils.log import LOG, deprecated

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


@deprecated("import ovos_utils.available_extractors from ovos_plugin_manager.ocp instead", "0.1.0")
def available_extractors():
    # TODO - delete me, still imported in ovos-bus-client, but never made it into a non-alpha
    try:
        from ovos_plugin_manager.ocp import available_extractors as _ax
    except ImportError:
        try:
            # before move to OPM
            from ovos_plugin_common_play.ocp.utils import available_extractors as _ax
        except ImportError:
            LOG.error("please install/update ovos_plugin_manager")
            raise
    return _ax()


def find_mime(uri):
    """ Determine mime type. """
    mime = mimetypes.guess_type(uri)
    if mime:
        return mime
    else:
        return None


@dataclass
class MediaEntry:
    uri: str = ""
    title: str = ""
    artist: str = ""
    match_confidence: int = 0  # 0 - 100
    skill_id: str = OCP_ID
    playback: PlaybackType = PlaybackType.UNDEFINED
    status: TrackState = TrackState.DISAMBIGUATION
    media_type: MediaType = MediaType.GENERIC
    length: int = 0  # in seconds
    image: str = ""
    skill_icon: str = ""
    javascript: str = ""  # to execute once webview is loaded

    def update(self, entry: dict, skipkeys: list = None, newonly: bool = False):
        """
        Update this MediaEntry object with keys from the provided entry
        @param entry: dict or MediaEntry object to update this object with
        @param skipkeys: list of keys to not change
        @param newonly: if True, only adds new keys; existing keys are unchanged
        """
        skipkeys = skipkeys or []
        if isinstance(entry, MediaEntry):
            entry = entry.as_dict
        entry = entry or {}
        for k, v in entry.items():
            if k not in skipkeys and hasattr(self, k):
                if newonly and self.__getattribute__(k):
                    # skip, do not replace existing values
                    continue
                self.__setattr__(k, v)

    @property
    def infocard(self) -> dict:
        """
        Return dict data used for a UI display
        """
        return {
            "duration": self.length,
            "track": self.title,
            "image": self.image,
            "album": self.skill_id,
            "source": self.skill_icon,
            "uri": self.uri
        }

    @property
    def mpris_metadata(self) -> dict:
        """
        Return dict data used by MPRIS
        """
        from dbus_next.service import Variant
        meta = {"xesam:url": Variant('s', self.uri)}
        if self.artist:
            meta['xesam:artist'] = Variant('as', [self.artist])
        if self.title:
            meta['xesam:title'] = Variant('s', self.title)
        if self.image:
            meta['mpris:artUrl'] = Variant('s', self.image)
        if self.length:
            meta['mpris:length'] = Variant('d', self.length)
        return meta

    @property
    def as_dict(self) -> dict:
        """
        Return a dict representation of this MediaEntry
        """
        # orjson handles dataclasses directly
        return orjson.loads(orjson.dumps(self).decode("utf-8"))

    @property
    def mimetype(self) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """
        Get the detected mimetype tuple (type, encoding) if it can be determined
        """
        if self.uri:
            return find_mime(self.uri)

    def __eq__(self, other):
        if isinstance(other, MediaEntry):
            other = other.infocard
        # dict comparison
        return other == self.infocard


@dataclass
class Playlist(list):
    title: str = ""
    position: int = 0
    length: int = 0  # in seconds
    image: str = ""
    match_confidence: int = 0  # 0 - 100
    skill_id: str = OCP_ID
    skill_icon: str = ""

    @property
    def infocard(self) -> dict:
        """
        Return dict data used for a UI display
        (model shared with MediaEntry)
        """
        return {
            "duration": self.length,
            "track": self.title,
            "image": self.image,
            "album": self.skill_id,
            "source": self.skill_icon,
            "uri": ""
        }

    @property
    def as_dict(self) -> dict:
        """
        Return a dict representation of this MediaEntry
        """
        # orjson handles dataclasses directly
        return orjson.loads(orjson.dumps(self).decode("utf-8"))

    @property
    def entries(self) -> List[MediaEntry]:
        """
        Return a list of MediaEntry objects in the playlist
        """
        entries = []
        for e in self:
            if isinstance(e, dict):
                e = MediaEntry(**e)
            if isinstance(e, MediaEntry):
                entries.append(e)
        return entries

    @property
    def current_track(self) -> Optional[MediaEntry]:
        """
        Return the current MediaEntry or None if the playlist is empty
        """
        if len(self) == 0:
            return None
        self._validate_position()
        track = self[self.position]
        if isinstance(track, dict):
            track = MediaEntry(**track)
        return track

    @property
    def is_first_track(self) -> bool:
        """
        Return `True` if the current position is the first track or if the
        playlist is empty
        """
        if len(self) == 0:
            return True
        return self.position == 0

    @property
    def is_last_track(self) -> bool:
        """
        Return `True` if the current position is the last track of if the
        playlist is empty
        """
        if len(self) == 0:
            return True
        return self.position == len(self) - 1

    def goto_start(self) -> None:
        """
        Move to the first entry in the playlist
        """
        self.position = 0

    def clear(self) -> None:
        """
        Remove all entries from the Playlist and reset the position
        """
        super().clear()
        self.position = 0

    def sort_by_conf(self):
        """
        Sort the Playlist by `match_confidence` with high confidence first
        """
        self.sort(
            key=lambda k: k.match_confidence if isinstance(k, MediaEntry)
            else k.get("match_confidence", 0), reverse=True)

    def add_entry(self, entry: MediaEntry, index: int = -1) -> None:
        """
        Add an entry at the requested index
        @param entry: MediaEntry to add to playlist
        @param index: index to insert entry at (default -1 to append)
        """
        assert isinstance(index, int)
        # TODO: Handle index out of range
        if isinstance(entry, dict):
            entry = MediaEntry(**entry)
        assert isinstance(entry, MediaEntry)
        if index == -1:
            index = len(self)

        if index < self.position:
            self.set_position(self.position + 1)

        self.insert(index, entry)

    def remove_entry(self, entry: Union[int, dict, MediaEntry]) -> None:
        """
        Remove the requested entry from the playlist or raise a ValueError
        @param entry: index or MediaEntry to remove from the playlist
        """
        if isinstance(entry, int):
            self.pop(entry)
            return
        if isinstance(entry, dict):
            entry = MediaEntry(**entry)
        assert isinstance(entry, MediaEntry)
        for idx, e in enumerate(self.entries):
            if e == entry:
                self.pop(idx)
                break
        else:
            raise ValueError(f"entry not in playlist: {entry}")

    def replace(self, new_list: List[Union[dict, MediaEntry]]) -> None:
        """
        Replace the contents of this Playlist with new_list
        @param new_list: list of MediaEntry or dict objects to set this list to
        """
        self.clear()
        for e in new_list:
            self.add_entry(e)

    def set_position(self, idx: int):
        """
        Set the position in the playlist to a specific index
        @param idx: Index to set position to
        """
        self.position = idx
        self._validate_position()

    def goto_track(self, track: Union[MediaEntry, dict]) -> None:
        """
        Go to the requested track in the playlist
        @param track: MediaEntry to find and go to in the playlist
        """
        if isinstance(track, MediaEntry):
            requested_uri = track.uri
        else:
            requested_uri = track.get("uri", "")
        for idx, t in enumerate(self):
            if isinstance(t, MediaEntry):
                pl_entry_uri = t.uri
            else:
                pl_entry_uri = t.get("uri", "")
            if requested_uri == pl_entry_uri:
                self.set_position(idx)
                LOG.debug(f"New playlist position: {self.position}")
                return
        LOG.error(f"requested track not in the playlist: {track}")

    def next_track(self) -> None:
        """
        Go to the next track in the playlist
        """
        self.set_position(self.position + 1)

    def prev_track(self) -> None:
        """
        Go to the previous track in the playlist
        """
        self.set_position(self.position - 1)

    def _validate_position(self) -> None:
        """
        Make sure the current position is valid; default `position` to 0
        """
        if self.position < 0 or self.position >= len(self):
            LOG.error(f"Playlist pointer is in an invalid position "
                      f"({self.position}! Going to start of playlist")
            self.position = 0

    def __contains__(self, item):
        if isinstance(item, dict):
            item = MediaEntry(**item)
        if isinstance(item, MediaEntry):
            for e in self.entries:
                if e.uri == item.uri:
                    return True
        return False


if __name__ == "__main__":
    m = MediaEntry("1")
    m2 = MediaEntry("2")
    m3 = MediaEntry("3")
    p = Playlist("My Jams")  # it's a list subclass
    p.append(m)
    p.add_entry(m2)
    p.add_entry(m3, 0)
    assert p[0] is m3
    assert p[1] is m
    assert m in p
    assert m2 in p
    assert m3 in p
    print(p.entries)
    np = [m3, m, m2]
    assert p == np
    assert np == p
    assert p == p.entries
    print(p.position)
    p.goto_track(m2)
    print(p.position)
    p.goto_start()
    print(p.position)
    p.set_position(1)
    print(p.position)

