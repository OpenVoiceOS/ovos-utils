# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import unittest
import warnings
from ovos_utils.ocp import (
    MediaEntry, Playlist, PluginStream, dict2entry,
    PlaybackType, TrackState, MediaState, PlayerState,
    LoopState, PlaybackMode, MatchConfidence, OCP_ID,
    find_mime,
)


def _make_playlist(uris):
    """Helper to build a Playlist from a list of URIs."""
    pl = Playlist()
    for uri in uris:
        pl.add_entry(MediaEntry(uri=uri, title=uri))
    return pl


# ---- MediaEntry tests -------------------------------------------------------

class TestMediaEntry(unittest.TestCase):
    def test_default_values(self):
        entry = MediaEntry()
        self.assertEqual(entry.uri, "")
        self.assertEqual(entry.title, "")
        self.assertEqual(entry.skill_id, OCP_ID)
        self.assertEqual(entry.playback, PlaybackType.UNDEFINED)

    def test_as_dict(self):
        entry = MediaEntry(uri="http://example.com/audio.mp3", title="Test")
        d = entry.as_dict
        self.assertIsInstance(d, dict)
        self.assertEqual(d["uri"], "http://example.com/audio.mp3")
        self.assertEqual(d["title"], "Test")

    def test_from_dict(self):
        d = {"uri": "http://example.com/a.mp3", "title": "Song"}
        entry = MediaEntry.from_dict(d)
        self.assertIsInstance(entry, MediaEntry)
        self.assertEqual(entry.uri, "http://example.com/a.mp3")

    def test_infocard(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", title="My Song", length=120)
        card = entry.infocard
        self.assertEqual(card["uri"], "http://x.com/f.mp3")
        self.assertEqual(card["track"], "My Song")
        self.assertEqual(card["duration"], 120)

    def test_equality(self):
        e1 = MediaEntry(uri="http://x.com/f.mp3", title="A")
        e2 = MediaEntry(uri="http://x.com/f.mp3", title="A")
        self.assertEqual(e1, e2)

    def test_inequality(self):
        e1 = MediaEntry(uri="http://x.com/f.mp3", title="A")
        e2 = MediaEntry(uri="http://x.com/g.mp3", title="B")
        self.assertNotEqual(e1, e2)

    def test_update_from_dict(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", title="Old")
        entry.update({"title": "New"})
        self.assertEqual(entry.title, "New")

    def test_update_skipkeys(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", title="Keep")
        entry.update({"title": "New"}, skipkeys=["title"])
        self.assertEqual(entry.title, "Keep")

    def test_update_newonly(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", title="Existing")
        entry.update({"title": "New"}, newonly=True)
        # title is not empty so should NOT be updated
        self.assertEqual(entry.title, "Existing")

    def test_mimetype_audio(self):
        entry = MediaEntry(uri="http://example.com/audio.mp3")
        mime = entry.mimetype
        # mp3 should return a mime tuple
        self.assertIsNotNone(mime)

    def test_mimetype_no_uri(self):
        entry = MediaEntry()
        mime = entry.mimetype
        self.assertIsNone(mime)


class TestFindMime(unittest.TestCase):
    def test_known_extension(self):
        result = find_mime("file.mp3")
        self.assertIsNotNone(result)

    def test_unknown_extension(self):
        result = find_mime("file.unknownextension123")
        # May return None or empty tuple
        # Just check it doesn't crash


# ---- PluginStream tests -----------------------------------------------------

class TestPluginStream(unittest.TestCase):
    def test_creation(self):
        ps = PluginStream(stream="abc123", extractor_id="youtube")
        self.assertEqual(ps.stream, "abc123")
        self.assertEqual(ps.extractor_id, "youtube")

    def test_infocard(self):
        ps = PluginStream(stream="abc", extractor_id="yt", title="Video")
        card = ps.infocard
        self.assertIn("yt//abc", card["uri"])
        self.assertEqual(card["track"], "Video")

    def test_as_dict(self):
        ps = PluginStream(stream="abc", extractor_id="yt")
        d = ps.as_dict
        self.assertIsInstance(d, dict)
        self.assertEqual(d["stream"], "abc")
        self.assertEqual(d["extractor_id"], "yt")

    def test_from_dict(self):
        d = {"stream": "s1", "extractor_id": "yt", "title": "T"}
        ps = PluginStream.from_dict(d)
        self.assertIsInstance(ps, PluginStream)

    def test_from_dict_missing_extractor_id_raises(self):
        with self.assertRaises(ValueError):
            PluginStream.from_dict({"stream": "s1"})

    def test_from_dict_missing_stream_raises(self):
        with self.assertRaises(ValueError):
            PluginStream.from_dict({"extractor_id": "yt"})

    def test_as_media_entry(self):
        ps = PluginStream(stream="abc", extractor_id="yt", title="Video")
        me = ps.as_media_entry
        self.assertIsInstance(me, MediaEntry)
        self.assertIn("yt//abc", me.uri)


# ---- Playlist tests ---------------------------------------------------------

class TestPlaylistNavigation(unittest.TestCase):
    def setUp(self):
        self.pl = _make_playlist(["track1", "track2", "track3"])

    def test_initial_position(self):
        self.assertEqual(self.pl.position, 0)

    def test_set_position(self):
        self.pl.set_position(1)
        self.assertEqual(self.pl.position, 1)

    def test_set_position_out_of_range_resets(self):
        self.pl.set_position(100)
        self.assertEqual(self.pl.position, 0)

    def test_set_position_negative_resets(self):
        self.pl.set_position(-1)
        self.assertEqual(self.pl.position, 0)

    def test_next_track(self):
        self.pl.set_position(0)
        self.pl.next_track()
        self.assertEqual(self.pl.position, 1)

    def test_next_track_wraps(self):
        self.pl.set_position(2)
        self.pl.next_track()
        self.assertEqual(self.pl.position, 0)

    def test_prev_track(self):
        self.pl.set_position(2)
        self.pl.prev_track()
        self.assertEqual(self.pl.position, 1)

    def test_prev_track_at_start_wraps(self):
        self.pl.set_position(0)
        self.pl.prev_track()
        self.assertEqual(self.pl.position, 0)

    def test_goto_track_media_entry(self):
        target = MediaEntry(uri="track2", title="track2")
        self.pl.goto_track(target)
        self.assertEqual(self.pl.position, 1)

    def test_goto_track_dict(self):
        d = {"uri": "track3", "title": "track3"}
        self.pl.goto_track(d)
        self.assertEqual(self.pl.position, 2)

    def test_goto_track_not_in_playlist(self):
        target = MediaEntry(uri="nonexistent", title="nonexistent")
        self.pl.set_position(1)
        self.pl.goto_track(target)
        self.assertEqual(self.pl.position, 1)

    def test_current_track(self):
        self.pl.set_position(0)
        track = self.pl.current_track
        self.assertIsInstance(track, MediaEntry)
        self.assertEqual(track.uri, "track1")

    def test_is_first_track(self):
        self.pl.set_position(0)
        self.assertTrue(self.pl.is_first_track)

    def test_is_last_track(self):
        self.pl.set_position(2)
        self.assertTrue(self.pl.is_last_track)

    def test_is_not_last_track(self):
        self.pl.set_position(0)
        self.assertFalse(self.pl.is_last_track)

    def test_goto_start(self):
        self.pl.set_position(2)
        self.pl.goto_start()
        self.assertEqual(self.pl.position, 0)


class TestPlaylistContains(unittest.TestCase):
    def setUp(self):
        self.pl = _make_playlist(["track_a", "track_b"])

    def test_contains_media_entry(self):
        entry = MediaEntry(uri="track_a", title="track_a")
        self.assertIn(entry, self.pl)

    def test_not_contains_media_entry(self):
        entry = MediaEntry(uri="track_z", title="track_z")
        self.assertNotIn(entry, self.pl)

    def test_contains_dict(self):
        d = {"uri": "track_b", "title": "track_b"}
        self.assertIn(d, self.pl)

    def test_not_contains_dict(self):
        d = {"uri": "missing", "title": "missing"}
        self.assertNotIn(d, self.pl)

    def test_contains_plugin_stream(self):
        pl = Playlist()
        ps = PluginStream(stream="stream1", extractor_id="myextractor")
        pl.add_entry(ps)
        check = PluginStream(stream="stream1", extractor_id="myextractor")
        self.assertIn(check, pl)

    def test_not_contains_plugin_stream_wrong_stream(self):
        pl = Playlist()
        ps = PluginStream(stream="stream1", extractor_id="myextractor")
        pl.add_entry(ps)
        check = PluginStream(stream="stream2", extractor_id="myextractor")
        self.assertNotIn(check, pl)


class TestPlaylistProperties(unittest.TestCase):
    def test_empty_playlist_length(self):
        pl = Playlist()
        # max(-1, sum([])) = max(-1, 0) = 0
        self.assertEqual(pl.length, 0)

    def test_playlist_length_with_entries(self):
        pl = Playlist()
        pl.add_entry(MediaEntry(uri="a", length=60))
        pl.add_entry(MediaEntry(uri="b", length=120))
        self.assertEqual(pl.length, 180)

    def test_infocard(self):
        pl = Playlist(title="My Playlist")
        card = pl.infocard
        self.assertEqual(card["track"], "My Playlist")

    def test_as_dict(self):
        pl = _make_playlist(["t1", "t2"])
        d = pl.as_dict
        self.assertIsInstance(d, dict)
        self.assertIn("playlist", d)

    def test_from_dict(self):
        d = {"playlist": [{"uri": "t1", "title": "T1"}], "title": "PL"}
        pl = Playlist.from_dict(d)
        self.assertIsInstance(pl, Playlist)

    def test_from_dict_missing_playlist_raises(self):
        with self.assertRaises(ValueError):
            Playlist.from_dict({"title": "No playlist"})

    def test_clear(self):
        pl = _make_playlist(["a", "b", "c"])
        pl.set_position(2)
        pl.clear()
        self.assertEqual(len(pl), 0)
        self.assertEqual(pl.position, 0)

    def test_sort_by_conf(self):
        pl = Playlist()
        pl.add_entry(MediaEntry(uri="a", match_confidence=30))
        pl.add_entry(MediaEntry(uri="b", match_confidence=90))
        pl.add_entry(MediaEntry(uri="c", match_confidence=60))
        pl.sort_by_conf()
        self.assertEqual(pl[0].match_confidence, 90)

    def test_empty_current_track_is_none(self):
        pl = Playlist()
        self.assertIsNone(pl.current_track)

    def test_empty_is_first_track(self):
        pl = Playlist()
        self.assertTrue(pl.is_first_track)

    def test_empty_is_last_track(self):
        pl = Playlist()
        self.assertTrue(pl.is_last_track)

    def test_entries_property(self):
        pl = _make_playlist(["x", "y"])
        entries = pl.entries
        self.assertEqual(len(entries), 2)
        for e in entries:
            self.assertIsInstance(e, MediaEntry)

    def test_add_entry_at_index(self):
        pl = _make_playlist(["a", "b"])
        pl.add_entry(MediaEntry(uri="c", title="c"), index=0)
        self.assertEqual(pl[0].uri, "c")


# ---- dict2entry tests -------------------------------------------------------

class TestDict2Entry(unittest.TestCase):
    def test_media_entry_from_dict(self):
        d = {"uri": "http://example.com/audio.mp3", "title": "Test"}
        entry = dict2entry(d)
        self.assertIsInstance(entry, MediaEntry)

    def test_plugin_stream_from_dict(self):
        d = {"stream": "some_stream", "extractor_id": "youtube", "title": "Test"}
        entry = dict2entry(d)
        self.assertIsInstance(entry, PluginStream)

    def test_playlist_from_dict(self):
        d = {"playlist": [{"uri": "http://example.com/1.mp3", "title": "1"}],
             "title": "My Playlist"}
        entry = dict2entry(d)
        self.assertIsInstance(entry, Playlist)

    def test_invalid_dict_raises(self):
        with self.assertRaises(ValueError):
            dict2entry({"title": "No URI or stream"})

    def test_empty_dict_raises(self):
        with self.assertRaises((ValueError, KeyError)):
            dict2entry({})


# ---- Enum tests -------------------------------------------------------------

class TestEnums(unittest.TestCase):
    def test_match_confidence_values(self):
        self.assertEqual(MatchConfidence.EXACT, 95)
        self.assertEqual(MatchConfidence.VERY_HIGH, 90)
        self.assertEqual(MatchConfidence.LOW, 15)

    def test_track_state_values(self):
        self.assertEqual(TrackState.DISAMBIGUATION, 1)
        self.assertEqual(TrackState.PLAYING_AUDIO, 23)

    def test_media_state_values(self):
        self.assertEqual(MediaState.UNKNOWN, 0)
        self.assertEqual(MediaState.END_OF_MEDIA, 7)

    def test_player_state_values(self):
        self.assertEqual(PlayerState.STOPPED, 0)
        self.assertEqual(PlayerState.PLAYING, 1)
        self.assertEqual(PlayerState.PAUSED, 2)

    def test_loop_state_values(self):
        self.assertEqual(LoopState.NONE, 0)
        self.assertEqual(LoopState.REPEAT, 1)
        self.assertEqual(LoopState.REPEAT_TRACK, 2)

    def test_playback_type_values(self):
        self.assertEqual(PlaybackType.SKILL, 0)
        self.assertEqual(PlaybackType.VIDEO, 1)
        self.assertEqual(PlaybackType.AUDIO, 2)

    def test_playback_mode_values(self):
        self.assertEqual(PlaybackMode.AUTO, 0)
        self.assertEqual(PlaybackMode.AUDIO_ONLY, 10)


# ---- MPRIS / numeric hardening tests -----------------------------------------

def _stub_dbus_next():
    """Install a minimal dbus_next stub that records the Variant signature used."""
    import sys
    from unittest.mock import MagicMock

    class Variant:
        def __init__(self, signature, value):
            if signature != 'x' and not isinstance(value, (int, float, str, list)):
                raise TypeError(f"bad value for signature {signature}: {value!r}")
            self.signature = signature
            self.value = value

    dbus_stub = MagicMock()
    dbus_stub.service.Variant = Variant
    sys.modules["dbus_next"] = dbus_stub
    sys.modules["dbus_next.service"] = dbus_stub.service
    return Variant


def _unstub_dbus_next():
    import sys
    sys.modules.pop("dbus_next", None)
    sys.modules.pop("dbus_next.service", None)


class TestMprisLengthVariant(unittest.TestCase):
    """mpris:length must use MPRIS2 signature 'x' (int64), never 'd'."""

    def setUp(self):
        _stub_dbus_next()

    def tearDown(self):
        _unstub_dbus_next()

    def test_length_uses_int_signature(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", length=180)
        meta = entry.mpris_metadata
        variant = meta["mpris:length"]
        self.assertEqual(variant.signature, 'x')
        self.assertIsInstance(variant.value, int)
        self.assertEqual(variant.value, 180)

    def test_non_numeric_length_is_omitted_not_crashed(self):
        entry = MediaEntry(uri="http://x.com/f.mp3")
        entry.length = "not-a-number"  # bypass update() validation directly
        meta = entry.mpris_metadata  # must not raise
        self.assertNotIn("mpris:length", meta)

    def test_nan_length_is_omitted(self):
        entry = MediaEntry(uri="http://x.com/f.mp3")
        entry.length = float("nan")
        meta = entry.mpris_metadata
        self.assertNotIn("mpris:length", meta)

    def test_inf_length_is_omitted(self):
        entry = MediaEntry(uri="http://x.com/f.mp3")
        entry.length = float("inf")
        meta = entry.mpris_metadata
        self.assertNotIn("mpris:length", meta)


class TestMediaEntryUpdateValidation(unittest.TestCase):
    """update() must reject invalid values for numeric fields, keeping prior value."""

    def test_update_rejects_non_numeric_length(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", length=100)
        entry.update({"length": "garbage"})
        self.assertEqual(entry.length, 100)

    def test_update_rejects_nan_length(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", length=100)
        entry.update({"length": float("nan")})
        self.assertEqual(entry.length, 100)

    def test_update_rejects_inf_length(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", length=100)
        entry.update({"length": float("inf")})
        self.assertEqual(entry.length, 100)

    def test_update_rejects_bool_length(self):
        # bool is a subclass of int - must not be accepted as a numeric length
        entry = MediaEntry(uri="http://x.com/f.mp3", length=100)
        entry.update({"length": True})
        self.assertEqual(entry.length, 100)

    def test_update_accepts_valid_length(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", length=100)
        entry.update({"length": 250})
        self.assertEqual(entry.length, 250)

    def test_update_rejects_non_numeric_match_confidence(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", match_confidence=50)
        entry.update({"match_confidence": "high"})
        self.assertEqual(entry.match_confidence, 50)

    def test_update_still_applies_non_numeric_fields(self):
        entry = MediaEntry(uri="http://x.com/f.mp3", length=100, title="Old")
        entry.update({"length": "garbage", "title": "New"})
        self.assertEqual(entry.length, 100)
        self.assertEqual(entry.title, "New")

    def test_playlist_length_survives_poisoned_entry(self):
        # a non-numeric length must never reach Playlist.length's sum()
        pl = Playlist()
        pl.add_entry(MediaEntry(uri="a", length=10))
        e2 = MediaEntry(uri="b", length=20)
        e2.update({"length": "poison"})
        pl.add_entry(e2)
        self.assertEqual(pl.length, 30)


class TestDict2EntryErrorType(unittest.TestCase):
    """dict2entry must always raise ValueError on garbage input, never AssertionError/AttributeError."""

    def test_none_raises_value_error(self):
        with self.assertRaises(ValueError):
            dict2entry(None)

    def test_int_raises_value_error(self):
        with self.assertRaises(ValueError):
            dict2entry(5)

    def test_str_raises_value_error(self):
        with self.assertRaises(ValueError):
            dict2entry("not-a-dict")

    def test_list_raises_value_error(self):
        with self.assertRaises(ValueError):
            dict2entry(["not", "a", "dict"])

    def test_empty_dict_raises_value_error(self):
        with self.assertRaises(ValueError):
            dict2entry({})

    def test_dict_without_known_keys_raises_value_error(self):
        with self.assertRaises(ValueError):
            dict2entry({"foo": "bar"})


if __name__ == "__main__":
    unittest.main()
